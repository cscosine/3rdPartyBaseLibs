#!/usr/bin/env python3
import sys
from collections.abc import Sequence
from pathlib import Path

from csorchestrator.application.cli.cli import orchestrator_main_with_default_run
from csorchestrator.application.factory.factory import (
    OptionalOrchestratorWithReport,
)
from csorchestrator.application.recipes.checkout_build import checkout_and_build_repos
from csorchestrator.application.recipes.create_orchestrator import create_default_orchestrator
from csorchestrator.foundation.core.report import Report
from csorchestrator.frontend.cscmake_presets.supported_variants import (
    BuildConfig,
)


def create_orchestrator() -> OptionalOrchestratorWithReport:
    report = Report()

    base_target_dir = Path("workspace")
    base_install_dir = base_target_dir / Path("install")
    common_repo_ref = "dev"

    repos: dict[str, tuple[str, BuildConfig | None]] = {
        "csCMake": (common_repo_ref, None),
        "eigen3": (common_repo_ref, BuildConfig.RELEASE),
        "fmt": (common_repo_ref, BuildConfig.DEBUG_RELEASE),
        "fmt-eigen": (common_repo_ref, BuildConfig.RELEASE),
        "cpptrace": (common_repo_ref, BuildConfig.DEBUG_RELEASE),
        "magic_enum": (common_repo_ref, BuildConfig.DEBUG_RELEASE),
        "libassert": (common_repo_ref, BuildConfig.DEBUG_RELEASE),
        "tclap": (common_repo_ref, BuildConfig.RELEASE),
        "Catch2": (common_repo_ref, BuildConfig.DEBUG_RELEASE),
        "pipes": (common_repo_ref, BuildConfig.RELEASE),
        "NamedType": (common_repo_ref, BuildConfig.RELEASE),
        "tl-optional": (common_repo_ref, BuildConfig.RELEASE),
        "tl-expected": (common_repo_ref, BuildConfig.RELEASE),
    }

    o = create_default_orchestrator(
        name="3rdPartyBaseLibs",
        version="0.1.0",
        base_install_dir=base_install_dir,
    )

    checkout_and_build_repos(
        o,
        base_target_dir=base_target_dir,
        base_install_dir=base_install_dir,
        repo_ref_build_type_list=repos,
        repo_access_token="${{ secrets.ACTIONS_ORG_ACCESS }}",
    )

    return OptionalOrchestratorWithReport.createResultAndReport(o, report)


def main(argv: Sequence[str] | None = None) -> int:
    script_path = str(Path(__file__).resolve())
    return orchestrator_main_with_default_run(script_path, argv)


if __name__ == "__main__":
    sys.exit(main())
