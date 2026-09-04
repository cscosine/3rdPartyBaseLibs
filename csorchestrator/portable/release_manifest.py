import json
import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

from csorchestrator.portable.package_version import (
    CMakeConfigPackageVersionGrep,
    PackageVersion,
    get_package_versions_helper,
)


@dataclass
class ManifestVersionsEntry:
    variant: str
    entries: list[PackageVersion] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "entries": [entry.to_dict() for entry in self.entries],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManifestVersionsEntry":
        return cls(
            variant=data["variant"],
            entries=[PackageVersion.from_dict(entry) for entry in data["entries"]],
        )


@dataclass
class ReleaseManifest:
    project_name: str
    project_version: str
    variants: list[ManifestVersionsEntry] = field(default_factory=list)

    MANIFEST_VERSION: ClassVar[str] = "1.0"
    manifest_version: str = MANIFEST_VERSION

    CS_ORCHESTRATOR_MANIFEST_EXTENSION: ClassVar[str] = ".csOrchestratorManifest"
    CS_ORCHESTRATOR_MANIFEST_ROOT: ClassVar[str] = "csOrchestratorManifest"

    def to_dict(self) -> dict[str, Any]:
        return {
            ReleaseManifest.CS_ORCHESTRATOR_MANIFEST_ROOT: {
                "manifest_version": self.manifest_version,
                "project_name": self.project_name,
                "project_version": self.project_version,
                "variants": [variant.to_dict() for variant in self.variants],
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReleaseManifest":
        in_data = data[ReleaseManifest.CS_ORCHESTRATOR_MANIFEST_ROOT]
        return cls(
            manifest_version=in_data["manifest_version"],
            project_name=in_data["project_name"],
            project_version=in_data["project_version"],
            variants=[ManifestVersionsEntry.from_dict(variant) for variant in in_data["variants"]],
        )

    def write_release_manifest(
        self,
        filename: Path,
    ) -> None:
        """Write a release manifest to a JSON file."""
        path = Path(filename)
        # TODO robustify and return possible errors
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, sort_keys=True)

    @classmethod
    def load_release_manifest(
        cls,
        filename: Path,
    ) -> "ReleaseManifest":
        """Load a release manifest from a JSON file."""
        path = Path(filename)
        # TODO robustify and return possible errors
        with path.open("r", encoding="utf-8") as f:
            return ReleaseManifest.from_dict(json.load(f))


def get_package_versions_and_write_single_variant_manifest(
    repos_config_file_list: list[CMakeConfigPackageVersionGrep],  # pairs of repo and files reporting versions
    repos_auto_search_list: list[str],  # repo name only
    repos_version: list[PackageVersion],  # pairs of repo and versions
    base_install_dir: Path,
    install_subdir: Path,
    variant_string: str,
    project_name: str,
    project_version: str,
    output_file: Path,
) -> list[str]:  # return errors

    result = get_package_versions_helper(
        repos_config_file_list,
        repos_auto_search_list,
        repos_version,
        base_install_dir,
        install_subdir,
    )

    if result.errors:
        return result.errors

    entry = ManifestVersionsEntry(variant=variant_string, entries=result.versions)
    manifest = ReleaseManifest(
        project_name=project_name,
        project_version=project_version,
        variants=[entry],
    )

    manifest.write_release_manifest(output_file)

    return []


def load_release_manifest_single_variant_and_prepare_archive(
    input_full_path: Path,
    context_os_architecture_compiler_generator_string: str,
    input_base_dir: Path,
) -> list[str]:  # return errors
    # load which packages to create archives for from the version file (eg. eigen3: 3.4.0, boost: 1.82.0, etc)
    packages = ReleaseManifest.load_release_manifest(input_full_path)
    if len(packages.variants) == 0 or len(packages.variants) > 1:
        return [f"release manifest {str(input_full_path)} has {len(packages.variants)} variants, expected 1"]

    if context_os_architecture_compiler_generator_string != packages.variants[0].variant:
        return [
            f"release manifest {str(input_full_path)} has variant name {packages.variants[0].variant}, expected {context_os_architecture_compiler_generator_string}"  # noqa: E501
        ]

    for item in packages.variants[0].entries:
        input_path = Path(
            input_base_dir / context_os_architecture_compiler_generator_string / Path(item.name)
        ).resolve()
        output_path = Path(
            input_base_dir
            / Path(
                str(context_os_architecture_compiler_generator_string)
                + "-"
                + item.name
                + "-"
                + item.version
                + ".tar.gz"
            )
        ).resolve()

        with tarfile.open(output_path, "w:gz") as tar:
            for path in input_path.rglob("*"):
                resolved_path = path.resolve()
                arcname = path.resolve().relative_to(input_base_dir)
                tar.add(resolved_path, arcname=arcname)

    return []
