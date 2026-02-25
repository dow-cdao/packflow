import importlib.resources
import shutil
import zipfile
from pathlib import Path
from typing import Union

import packflow.constants as constants

from .loaders.config import PackflowConfig


class PackflowProject:
    def __init__(self, base_dir: Union[str, Path]):
        self.base_dir = Path(base_dir).resolve()

    @property
    def has_packflow_config(self):
        return self.base_dir.joinpath(constants.PACKAGING_CONFIG_NAME).exists()

    def __repr__(self):
        return f"{self.__class__.__name__} @ {self.base_dir}"

    @classmethod
    def create(cls, project_name: str, force: bool = False, template: str = "minimal"):
        """
        Create a new project and then return the PackflowProject controller
        for the new project
        """
        config = PackflowConfig(name=project_name)

        base_path = Path(config.name).resolve()

        base_path.mkdir(parents=True, exist_ok=force)

        # HARD CODED SINCE THERE'S ONLY ONE TEMPLATE RIGHT NOW
        templates_dir = (
            importlib.resources.files("packflow")
            .joinpath("data/templates")
            .joinpath(template)
        )

        shutil.copytree(str(templates_dir), str(base_path), dirs_exist_ok=True)

        config.write_yaml(base_path)

        config.write_requirements(base_path)

        return cls(base_path)

    def load_config(self):
        return PackflowConfig.from_project_path(self.base_dir)

    def export(self, output_directory: str = ".") -> Path:
        """
        Save the loaded project as a package.zip with schema `{name}-{version}-pkg.zip`
        """
        config = PackflowConfig.from_project_path(self.base_dir)
        export_file_name = config.archive_file_name(output_directory)

        try:
            with zipfile.ZipFile(export_file_name, "w") as zip_file:
                for file_path in self.base_dir.rglob("*"):
                    if (
                        file_path.is_file()
                        and file_path.resolve() != export_file_name.resolve()
                    ):
                        relative_path = file_path.relative_to(self.base_dir)
                        zip_file.write(str(file_path), str(relative_path))
            return export_file_name
        except Exception as e:
            # TODO: Create custom exception
            raise Exception(f"An error occurred: {e}")
