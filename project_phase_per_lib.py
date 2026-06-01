#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Sequence, TypeAlias

from csorchestrator.core.report import Report
from csorchestrator.orchestrator.orchestrator import Orchestrator, OptionalOrchestratorWithReport
from csorchestrator.step.step_get_repository import RepoUrlParts, StepGetRepositoryGitHub,StepGetRepositoryExtraDepthOne
from csorchestrator.step.step_cmake_command import StepCMakeWorkflow
from csorchestrator.orchestrator.step_base import StepSkipExecutionOnNonMatchingContext
from csorchestrator.utils.presets.supported_variants import BuildConfig, get_all_supported_workflow_descriptions, workflow_name_from_description
from csorchestrator.core.optional_result_with_report import OptionalResultWithReport
from csorchestrator.cli.cli import orchestrator_main_with_default_run

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

    o = Orchestrator ("3rdPartyBaseLibs")
    p = o.create_phase("Repos Update")

    skip_get_repository = False
    skip_build = True

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
                    repo_ref="dev",
                ).add_extra(
                    StepGetRepositoryExtraDepthOne(
                        on_local_checkout=False,
                        on_github_action_checkout=True,
                    )
                )
            )

    if skip_build:
        report.append_warning("Skipping build steps")
    else:
        for repo in build_repos:
            p = o.create_phase(f"{repo['name']} Configure-Build-Test-Install")
            workflow_descriptions = get_all_supported_workflow_descriptions(repo["config"])

            for workflow_description in workflow_descriptions:
                workflow_name = workflow_name_from_description(workflow_description)
                p.add_step(
                    StepCMakeWorkflow.create_from_workflow_description(
                        name = f"{repo['name']} CMake Workflow {workflow_name}",
                        description=f"CMake workflow for {repo['name']} with config: {repo['config']}",
                        source_dir=repo["target_directory"],
                        workflow_description=workflow_description,
                    ).add_extra(StepSkipExecutionOnNonMatchingContext())
                )
    return OptionalResultWithReport.createResultAndReport(o, report)

def main(argv: Sequence[str] | None = None) -> int:
    script_path = str(Path(__file__).resolve())
    return orchestrator_main_with_default_run(script_path, argv)


if __name__ == "__main__":
    sys.exit(main())
