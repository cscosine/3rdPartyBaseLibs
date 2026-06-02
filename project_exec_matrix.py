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
)
from csorchestrator.step.step_get_versions_from_cmake_config_package_version import StepGetVersionsFromCMakeConfigPackageVersion, CMakeConfigPackageVersionGrep
from csorchestrator.step.step_create_archives import StepCreateArchives
from csorchestrator.step.step_upload_artifacts import StepUploadArtifacts

def create_orchestrator() -> OptionalOrchestratorWithReport:
    report = Report()

    base_target_dir = Path("workspace")
    base_install_dir = base_target_dir / Path("install")
    common_repo_ref = "dev"

    non_build_repos = [
        {
            "name": "csCMake",
        },
    ]

    build_repos = [
        {
            "name": "eigen3",
            "config": BuildConfig.RELEASE,
        },
    # ]
    # others = [
        {
            "name": "fmt",
            "config": BuildConfig.DEBUG_RELEASE,
        },
        {
            "name": "fmt-eigen",
            "config": BuildConfig.RELEASE,
        },
        {
            "name": "cpptrace",
            "config": BuildConfig.DEBUG_RELEASE,
        },
        {
            "name": "magic_enum",
            "config": BuildConfig.DEBUG_RELEASE,
        },
        {
            "name": "libassert",
            "config": BuildConfig.DEBUG_RELEASE,
        },
        {
            "name": "tclap",
            "config": BuildConfig.RELEASE,
        },
        {
            "name": "Catch2",
            "config": BuildConfig.DEBUG_RELEASE,
        },
        {
            "name": "pipes",
            "config": BuildConfig.RELEASE,
        },
        {
            "name": "NamedType",
            "config": BuildConfig.RELEASE,
        },
        {
            "name": "tl-optional",
            "config": BuildConfig.RELEASE,
        },
        {
            "name": "tl-expected",
            "config": BuildConfig.RELEASE,
        },
    ]

    o = Orchestrator ("3rdPartyBaseLibs").create_default_github_workflow(
        config=CreateGitHubWorkflowConfig(
            on_push_branches=["main", "dev"],
            on_push_tags=["'v*.*.*'"],
            on_pull_request_branches=["main"],
            on_dispatch=True,
            on_schedule=Cron.weekly(DayOfWeek.MON, hour=3),
        )
    ).set_execution_matrix(
        ExecutionMatrixOsArchCompilerGenerator(
            os_architecture_compiler_generator_list = get_supported_context_os_architecture_list()
        ).add_extra(MatrixSkipExecutionOnNonMatchingContext())
    )

    p = o.create_phase("Repos Update")

    skip_get_repository = False
    skip_build = False

    if skip_get_repository:
        report.append_warning("Skipping repository cloning steps")
    else:
        for repo in non_build_repos + build_repos:
            p.add_step(
                StepGetRepositoryGitHub(
                    name=repo["name"],
                    description=f"Clone or pull-ff {repo['name']} description",
                    target_directory=str(base_target_dir / repo["name"]),
                    repo_url_parts= RepoUrlParts(
                        repo_base_url=StepGetRepositoryGitHub.GITHUB_BASE_URL_SSH,
                        repo_org="cscosine",
                        repo_name=repo["name"] + ".git",                        
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
    for repo in build_repos:

        if skip_build:
            report.append_warning("Skipping build steps")
        else:
            p.add_step(
                StepCMakeWorkflow(
                    name = f"{repo['name']} CMake Workflow",
                    description=f"CMake workflow for {repo['name']} with config: {repo['config']}",
                    source_dir=str(base_target_dir / repo["name"]),
                    config=repo['config'],
                )
            )

        repo_config_list = [
            # CMakeConfigPackageVersionGrep(
            #     name = repo['name'],
            #     version_file = Path(repo['version_file']),
            # )
            # for repo in build_repos
        ]
        
    p.add_step(
        StepGetVersionsFromCMakeConfigPackageVersion(
            name = "Get Versions",
            description= "Get Versions for all libs",
            repos_config_file_list = repo_config_list,
            repos_auto_search_list = [repo ['name'] for repo in build_repos],
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
