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


def create_orchestrator() -> OptionalOrchestratorWithReport:
    report = Report()
    non_build_repos = [
        {
            "name": "csCMake",
            "description": "The cscosine CMake facilitator",
            "target_directory": "workspace/csCMake",
        },
    ]

    build_repos = [
        {
            "name": "eigen3",
            "description": "The cscosine eigen3 library",
            "target_directory": "workspace/eigen3",
            "config": BuildConfig.RELEASE
        },
        {
            "name": "fmt",
            "description": "The fmt library",
            "target_directory": "workspace/fmt",
            "config": BuildConfig.DEBUG_RELEASE
        },
        {
            "name": "fmt-eigen",
            "description": "The fmt-eigen library",
            "target_directory": "workspace/fmt-eigen",
            "config": BuildConfig.RELEASE
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
                    description=repo["description"],
                    target_directory=repo["target_directory"],
                    repo_url_parts= RepoUrlParts(
                        repo_base_url=StepGetRepositoryGitHub.GITHUB_BASE_URL_SSH,
                        repo_org="cscosine",
                        repo_name=repo["name"] + ".git",                        
                    ),
                    repo_ref="orchestrator",
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

    if skip_build:
        report.append_warning("Skipping build steps")
    else:
        p = o.create_phase(f"Configure-Build-Test-Install")
        for repo in build_repos:

            p.add_step(
                StepCMakeWorkflow(
                    name = f"{repo['name']} CMake Workflow",
                    description=f"CMake workflow for {repo['name']} with config: {repo['config']}",
                    source_dir=repo["target_directory"],
                    config=repo['config'],
                )
            )
    return OptionalResultWithReport.createResultAndReport(o, report)

def main(argv: Sequence[str] | None = None) -> int:
    script_path = str(Path(__file__).resolve())
    return orchestrator_main_with_default_run(script_path, argv)


if __name__ == "__main__":
    sys.exit(main())
