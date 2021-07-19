from pathlib import Path

from antarest.core.custom_types import JSON
from antarest.study.model import Patch, PatchOutputs, RawStudy


class PatchService:
    def get(self, study: RawStudy) -> Patch:
        patch_path = Path(study.path) / "patch.json"
        if patch_path.exists():
            return Patch.parse_file(patch_path)
        return Patch()

    def set_reference_output(
        self, study: RawStudy, output_id: str, status: bool = True
    ) -> None:
        patch = self.get(study)
        if patch.outputs is not None:
            patch.outputs.reference = output_id if status else None
        elif status:
            patch.outputs = PatchOutputs(reference=output_id)
        self.save(study, patch)

    def save(self, study: RawStudy, patch: Patch) -> None:
        patch_content = patch.json()
        patch_path = Path(study.path) / "patch.json"
        patch_path.write_text(patch_content)

    def patch(self, study: RawStudy, new_patch_content: JSON) -> None:
        new_patch = Patch.parse_obj(new_patch_content)
        old_patch = self.get(study)
        merged_path = old_patch.patch(new_patch)
        self.save(study, merged_path)
