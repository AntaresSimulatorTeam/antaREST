"""
This module dedicated to variant snapshot generation.
"""
import datetime
import logging
import shutil
import typing as t
from pathlib import Path

from antarest.core.exceptions import VariantGenerationError
from antarest.core.interfaces.cache import CacheConstants, ICache
from antarest.core.jwt import JWTUser
from antarest.core.model import StudyPermissionType
from antarest.core.tasks.service import TaskUpdateNotifier, noop_notifier
from antarest.study.model import RawStudy, StudyAdditionalData
from antarest.study.storage.patch_service import PatchService
from antarest.study.storage.rawstudy.model.filesystem.config.model import FileStudyTreeConfigDTO
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy, StudyFactory
from antarest.study.storage.rawstudy.raw_study_service import RawStudyService
from antarest.study.storage.utils import assert_permission_on_studies, export_study_flat
from antarest.study.storage.variantstudy.command_factory import CommandFactory
from antarest.study.storage.variantstudy.model.dbmodel import CommandBlock, VariantStudy, VariantStudySnapshot
from antarest.study.storage.variantstudy.model.model import GenerationResultInfoDTO
from antarest.study.storage.variantstudy.repository import VariantStudyRepository
from antarest.study.storage.variantstudy.variant_command_generator import VariantCommandGenerator

logger = logging.getLogger(__name__)


OUTPUT_RELATIVE_PATH = "output"


class SnapshotGenerator:
    """
    Helper class used to generate snapshots for variant studies.
    """

    def __init__(
        self,
        cache: ICache,
        raw_study_service: RawStudyService,
        command_factory: CommandFactory,
        study_factory: StudyFactory,
        patch_service: PatchService,
        repository: VariantStudyRepository,
    ):
        self.cache = cache
        self.raw_study_service = raw_study_service
        self.command_factory = command_factory
        self.study_factory = study_factory
        self.patch_service = patch_service
        self.repository = repository

    def generate_snapshot(
        self,
        variant_study_id: str,
        jwt_user: JWTUser,
        *,
        denormalize: bool = True,
        from_scratch: bool = False,
        notifier: TaskUpdateNotifier = noop_notifier,
    ) -> GenerationResultInfoDTO:
        # ATTENTION: since we are making changes to disk, a file lock is needed.
        # The locking is currently done in the `VariantStudyService.generate_task` function
        # when starting the task. However, it is not enough, because the snapshot generation
        # need to read the root study or a snapshot of a variant study which may be modified
        # during the task. Ideally, we should lock the root study and all its descendants,
        # but it is not currently possible to lock studies.
        # The locking done at the task level nevertheless makes it possible to limit the risks.

        logger.info(f"Generating variant study snapshot for '{variant_study_id}'")

        root_study, descendants = self._retrieve_descendants(variant_study_id)
        assert_permission_on_studies(jwt_user, [root_study, *descendants], StudyPermissionType.READ, raising=True)
        search_result = search_ref_study(root_study, descendants, from_scratch=from_scratch)

        ref_study = search_result.ref_study
        cmd_blocks = search_result.cmd_blocks

        # Get snapshot directory
        variant_study = descendants[-1]
        snapshot_dir = variant_study.snapshot_dir

        force_regenerate = (
            search_result.force_regenerate or not snapshot_dir.exists() or ref_study.id != variant_study_id
        )
        if force_regenerate:
            shutil.rmtree(snapshot_dir, ignore_errors=True)

        try:
            if force_regenerate:
                logger.info(f"Exporting the reference study '{ref_study.id}' to '{snapshot_dir.name}'...")
                self._export_ref_study(snapshot_dir, ref_study)

            logger.info(f"Applying commands to the reference study '{ref_study.id}'...")
            results = self._apply_commands(snapshot_dir, variant_study, cmd_blocks)

            # The snapshot is generated, we also need to de-normalize the matrices.
            file_study = self.study_factory.create_from_fs(
                snapshot_dir,
                study_id=variant_study_id,
                output_path=snapshot_dir / OUTPUT_RELATIVE_PATH,
                use_cache=False,  # Avoid saving the study config in the cache
            )
            if denormalize:
                logger.info(f"Denormalizing variant study {variant_study_id}")
                file_study.tree.denormalize()

            # Finally, we can update the database.
            logger.info(f"Saving new snapshot for study {variant_study_id}")
            variant_study.snapshot = VariantStudySnapshot(
                id=variant_study_id,
                created_at=datetime.datetime.utcnow(),
                last_executed_command=cmd_blocks[-1].id if cmd_blocks else None,
            )

            logger.info(f"Reading additional data from files for study {file_study.config.study_id}")
            variant_study.additional_data = self._read_additional_data(file_study)
            self.repository.save(variant_study)

            # Store the study config in the cache (with adjusted paths).
            file_study.config.study_path = file_study.config.path = snapshot_dir
            file_study.config.output_path = snapshot_dir / OUTPUT_RELATIVE_PATH
            self._update_cache(file_study)

        except Exception:
            shutil.rmtree(snapshot_dir, ignore_errors=True)
            raise

        else:
            try:
                notifier(results.json())
            except Exception as exc:
                # This exception is ignored, because it is not critical.
                logger.warning(f"Error while sending notification: {exc}", exc_info=True)

        return results

    def _retrieve_descendants(self, variant_study_id: str) -> t.Tuple[RawStudy, t.Sequence[VariantStudy]]:
        # Get all ancestors of the current study from bottom to top
        # The first IDs are variant IDs, the last is the root study ID.
        ancestor_ids = self.repository.get_ancestor_or_self_ids(variant_study_id)
        descendant_ids = ancestor_ids[::-1]
        descendants = self.repository.find_variants(descendant_ids)
        root_study = self.repository.one(descendant_ids[0])
        return root_study, descendants

    def _export_ref_study(self, snapshot_dir: Path, ref_study: t.Union[RawStudy, VariantStudy]) -> None:
        if isinstance(ref_study, VariantStudy):
            export_study_flat(
                ref_study.snapshot_dir,
                snapshot_dir,
                self.study_factory,
                denormalize=False,  # de-normalization is done at the end
                outputs=False,  # do NOT export outputs
            )
        elif isinstance(ref_study, RawStudy):
            self.raw_study_service.export_study_flat(
                ref_study,
                snapshot_dir,
                denormalize=False,  # de-normalization is done at the end
                outputs=False,  # do NOT export outputs
            )
        else:  # pragma: no cover
            raise TypeError(repr(type(ref_study)))

    def _apply_commands(
        self,
        snapshot_dir: Path,
        variant_study: VariantStudy,
        cmd_blocks: t.Sequence[CommandBlock],
    ) -> GenerationResultInfoDTO:
        commands = [self.command_factory.to_command(cb.to_dto()) for cb in cmd_blocks]
        generator = VariantCommandGenerator(self.study_factory)
        results = generator.generate(
            commands,
            snapshot_dir,
            variant_study,
            delete_on_failure=False,  # Not needed, because we are using a temporary directory
            notifier=None,
        )
        if not results.success:
            message = f"Failed to generate variant study {variant_study.id}"
            if results.details:
                detail: t.Tuple[str, bool, str] = results.details[-1]
                message += f": {detail[2]}"
            raise VariantGenerationError(message)
        return results

    def _read_additional_data(self, file_study: FileStudy) -> StudyAdditionalData:
        horizon = file_study.tree.get(url=["settings", "generaldata", "general", "horizon"])
        author = file_study.tree.get(url=["study", "antares", "author"])
        patch = self.patch_service.get_from_filestudy(file_study)
        study_additional_data = StudyAdditionalData(horizon=horizon, author=author, patch=patch.json())
        return study_additional_data

    def _update_cache(self, file_study: FileStudy) -> None:
        # The study configuration is changed, so we update the cache.
        self.cache.invalidate(f"{CacheConstants.RAW_STUDY}/{file_study.config.study_id}")
        self.cache.put(
            f"{CacheConstants.STUDY_FACTORY}/{file_study.config.study_id}",
            FileStudyTreeConfigDTO.from_build_config(file_study.config).dict(),
        )


class RefStudySearchResult(t.NamedTuple):
    """
    Result of the search for the reference study.
    """

    ref_study: t.Union[RawStudy, VariantStudy]
    cmd_blocks: t.Sequence[CommandBlock]
    force_regenerate: bool = False


def search_ref_study(
    root_study: t.Union[RawStudy, VariantStudy],
    descendants: t.Sequence[VariantStudy],
    *,
    from_scratch: bool = False,
) -> RefStudySearchResult:
    """
    Search for the reference study and the commands to use for snapshot generation.

    Args:
        root_study: The root study from which the descendants of variants are derived.
        descendants: The list of descendants of variants from top to bottom.
        from_scratch: Whether to generate the snapshot from scratch or not.

    Returns:
        The reference study and the commands to use for snapshot generation.
    """

    # The reference study is the root study or a variant study with a valid snapshot
    ref_study: t.Union[RawStudy, VariantStudy]

    # The commands to apply on the reference study to generate the current variant
    cmd_blocks: t.List[CommandBlock]

    if from_scratch:
        # In the case of a from scratch generation, the root study will be used as the reference study.
        # We need to retrieve all commands from the descendants of variants in order to apply them
        # on the reference study.
        ref_study = root_study
        cmd_blocks = [c for v in descendants for c in v.commands]
        force_regenerate = True

    else:
        # To generate the last variant of a descendant of variants, we must search for
        # the most recent snapshot in order to use it as a reference study.
        # If no snapshot is found, we use the root study as a reference study.

        snapshot_vars = [v for v in descendants if v.is_snapshot_recent()]

        if snapshot_vars:
            # We use the most recent snapshot as a reference study
            ref_study = max(snapshot_vars, key=lambda v: v.snapshot.created_at)

            # This variant's snapshot corresponds to the commands actually generated
            # at the time of the snapshot. However, we need to retrieve the remaining commands,
            # because the snapshot generation may be incomplete.
            last_exec_cmd = ref_study.snapshot.last_executed_command  # ID of the command
            command_ids = [c.id for c in ref_study.commands]
            if not last_exec_cmd or last_exec_cmd not in command_ids:
                # The last executed command may be missing (probably caused by a bug)
                # or may reference a removed command.
                # This requires regenerating the snapshot from scratch,
                # with all commands from the reference study.
                cmd_blocks = ref_study.commands[:]
                force_regenerate = True
            else:
                last_exec_index = command_ids.index(last_exec_cmd)
                cmd_blocks = ref_study.commands[last_exec_index + 1 :]
                force_regenerate = False

            # We need to add all commands from the descendants of variants
            # starting at the first descendant of reference study.
            index = descendants.index(ref_study)
            cmd_blocks.extend([c for v in descendants[index + 1 :] for c in v.commands])

        else:
            # We use the root study as a reference study
            ref_study = root_study
            cmd_blocks = [c for v in descendants for c in v.commands]
            force_regenerate = True

    return RefStudySearchResult(
        ref_study=ref_study,
        cmd_blocks=cmd_blocks,
        force_regenerate=force_regenerate,
    )
