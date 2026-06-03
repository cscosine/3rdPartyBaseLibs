#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Sequence, TypeAlias

from csorchestrator.core.report import Report
from csorchestrator.orchestrator.orchestrator import Orchestrator, OptionalOrchestratorWithReport
from csorchestrator.step.step_get_repository import RepoUrlParts, StepGetRepositoryGitHub, StepGetRepositoryExecuteOnlyOncePerMatrix,StepGetRepositoryExtraDepthOne,StepGetRepositoryExtraAccessToken
from csorchestrator.step.step_cmake_command import StepCMakeWorkflow
from csorchestrator.utils.presets.supported_variants import BuildConfig, get_supported_context_os_architecture_list
from csorchestrator.core.optional_result_with_report import OptionalResultWithReport
from csorchestrator.cli.cli import orchestrator_main_with_default_run
from csorchestrator.context.context_os_architecture_compiler_generator import (
    ExecutionMatrixOsArchCompilerGenerator,
    MatrixSkipExecutionOnNonMatchingContext
)
from csorchestrator.ci.github.github_workflow_config import (
    CreateGitHubWorkflowConfig,
    Cron,
    DayOfWeek,
    JobReleaseCreationFromArifacts,
)
from csorchestrator.step.step_get_versions_from_cmake_config_package_version import StepGetVersionsFromCMakeConfigPackageVersion, CMakeConfigPackageVersionGrep
from csorchestrator.step.step_create_archives import StepCreateArchives
from csorchestrator.step.step_upload_artifacts import StepUploadArtifacts

def create_orchestrator() -> OptionalOrchestratorWithReport:
    report = Report()

    base_target_dir = Path("workspace")
    base_install_dir = base_target_dir / Path("install")
    common_repo_ref = "dev"

    repos : dict[str, None | BuildConfig] = {
            "csCMake": None,
            "eigen3": BuildConfig.RELEASE,
    # }
    # others: dict[str, BuildConfig] = {
            "fmt":BuildConfig.DEBUG_RELEASE,
            "fmt-eigen": BuildConfig.RELEASE,
            "cpptrace": BuildConfig.DEBUG_RELEASE,
            "magic_enum": BuildConfig.DEBUG_RELEASE,
            "libassert": BuildConfig.DEBUG_RELEASE,
            "tclap": BuildConfig.RELEASE,
            "Catch2": BuildConfig.DEBUG_RELEASE,
            "pipes": BuildConfig.RELEASE,
            "NamedType": BuildConfig.RELEASE,
            "tl-optional": BuildConfig.RELEASE,
            "tl-expected": BuildConfig.RELEASE,
    }

    o = Orchestrator ("3rdPartyBaseLibs", version="0.1.0").create_default_github_workflow(
        config=CreateGitHubWorkflowConfig(
            on_push_branches=["main", "dev"],
            on_push_tags=["'v*.*.*'"],
            on_pull_request_branches=["main"],
            on_dispatch=True,
            on_schedule=Cron.weekly(DayOfWeek.MON, hour=3),
        )
    ).set_execution_matrix(
        ExecutionMatrixOsArchCompilerGenerator(
            name="orchestrator-matrix",
            os_architecture_compiler_generator_list = get_supported_context_os_architecture_list()
        ).add_extra(MatrixSkipExecutionOnNonMatchingContext())
    )

    o.default_github_wf.on_job(
        job=
        JobReleaseCreationFromArifacts(
            name="release-from-artifacts",
            needs="orchestrator-matrix",
            runs_on="ubuntu-latest",
            if_str="${{ github.ref_type == 'tag' }}"
        )
    )


    skip_get_repository = False
    skip_build = False

    if skip_get_repository:
        report.append_warning("Skipping repository cloning steps")
    else:
        p = o.create_phase("Repos Update")
        for repo in repos.keys():
            p.add_step(
                StepGetRepositoryGitHub(
                    name=repo,
                    description=f"Clone or pull-ff {repo} description",
                    target_directory=str(base_target_dir / repo),
                    repo_url_parts= RepoUrlParts(
                        repo_base_url=StepGetRepositoryGitHub.GITHUB_BASE_URL_SSH,
                        repo_org="cscosine",
                        repo_name=repo + ".git",                        
                    ),
                    repo_ref=common_repo_ref,
                ).add_extra(
                    StepGetRepositoryExtraDepthOne(
                        on_local_checkout=False,
                        on_github_action_checkout=True,
                    )
                ).add_extra(
                    StepGetRepositoryExecuteOnlyOncePerMatrix()
                ).add_extra(
                    StepGetRepositoryExtraAccessToken("${{ secrets.ACTIONS_ORG_ACCESS }}")
                )
            )

    p = o.create_phase(f"Configure-Build-Test-Install")
    for repo, config in repos.items():

        if skip_build:
            report.append_warning("Skipping build steps")
        else:
            if config is None:
                report.append_info(f"Skipping build steps for {repo} since config is None")
                continue
            p.add_step(
                StepCMakeWorkflow(
                    name = f"{repo} CMake Workflow",
                    description=f"CMake workflow for {repo} with config: {config}",
                    source_dir=str(base_target_dir / repo),
                    config=config,
                )
            )
        
    p = o.create_phase(f"Create and Upload Artifacts")
    p.add_step(
        StepGetVersionsFromCMakeConfigPackageVersion(
            name = "Get Versions",
            description= "Get Versions for all libs",
            repos_auto_search_list = [repo for repo, config in repos.items() if config is not None],
            base_install_dir = base_install_dir,
            id = "versions",
            output_dict_name = "packages"
        )
    )

    p.add_step(
        StepCreateArchives(
            name = "Create Archives",
            description= "Create archives with libs and versions",
            input_id = "versions",
            input_dict = "packages",
            base_install_dir = base_install_dir,
        )
    )

    p.add_step(
        StepUploadArtifacts(
            name = "Upload Artifacts",
            description= "Upload Artifacts with libs and versions",
            base_install_dir = base_install_dir,
        )
    )

    return OptionalResultWithReport.createResultAndReport(o, report)

def main(argv: Sequence[str] | None = None) -> int:
    script_path = str(Path(__file__).resolve())
    return orchestrator_main_with_default_run(script_path, argv)


if __name__ == "__main__":
    sys.exit(main())
