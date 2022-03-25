from typing import Optional, List, cast

from antarest.core.model import JSON
from antarest.core.utils.utils import assert_this
from antarest.study.storage.rawstudy.model.filesystem.factory import FileStudy


class FileStudyHelpers:
    @staticmethod
    def get_config(study: FileStudy, output_id: Optional[str] = None) -> JSON:
        config_path = ["settings", "generaldata"]
        if output_id:
            config_path = [
                "output",
                output_id,
                "about-the-study",
                "parameters",
            ]
        return study.tree.get(config_path)

    @staticmethod
    def save_config(study: FileStudy, config: JSON) -> None:
        config_path = ["settings", "generaldata"]
        return study.tree.save(config, config_path)

    @staticmethod
    def get_playlist(study: FileStudy) -> List[int]:
        config = FileStudyHelpers.get_config(study)
        general_config = config.get("general", {})
        nb_years = cast(int, general_config.get("nbyears"))
        playlist_activated = cast(
            bool, general_config.get("user-playlist", False)
        )
        if not playlist_activated:
            return list(range(0, nb_years))
        playlist_config = config.get("playlist", {})
        playlist_reset = playlist_config.get("playlist_reset", True)
        added = playlist_config.get("playlist_year +", [])
        removed = playlist_config.get("playlist_year -", [])
        if playlist_reset:
            return [year for year in range(0, nb_years) if year not in removed]
        return [year for year in added if year not in removed]

    @staticmethod
    def set_playlist(study: FileStudy, playlist: List[int]) -> None:
        config = FileStudyHelpers.get_config(study)
        general_config: Optional[JSON] = config.get("general", None)
        assert_this(general_config is not None)
        general_config = cast(JSON, general_config)
        nb_years = cast(int, general_config.get("nbyears"))
        if len(playlist) == nb_years:
            general_config["user-playlist"] = False
        else:
            playlist_config = config.get("playlist", {})
            general_config["user-playlist"] = True
            if len(playlist) > nb_years / 2:
                playlist_config["playlist_reset"] = True
                if "playlist_year +" in playlist_config:
                    del playlist_config["playlist_year +"]
                playlist_config["playlist_year -"] = [
                    year for year in range(0, nb_years) if year not in playlist
                ]
            else:
                playlist_config["playlist_reset"] = False
                if "playlist_year -" in playlist_config:
                    del playlist_config["playlist_year -"]
                playlist_config["playlist_year +"] = playlist
            config["playlist"] = playlist_config
        FileStudyHelpers.save_config(study, config)
