#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Sequence, TypeAlias

from csorchestrator.core.report import Report
from csorchestrator.orchestrator.orchestrator import Orchestrator, OptionalOrchestratorWithReport
from csorchestrator.step.step_get_repository import StepGetRepository,RepositoryType,StepGetRepositoryExtraDepthOne
from csorchestrator.step.step_cmake_command import StepCMakeWorkflow
from csorchestrator.orchestrator.step_base import StepExecuteOnMatchingContext
from csorchestrator.utils.presets.supported_variants import BuildConfig, create_context_os_architecture_compiler_generator_string, get_supported_context_os_architecture_list
from csorchestrator.core.optional_result_with_report import OptionalResultWithReport
from csorchestrator.cli.cli import orchestrator_main_with_default_run

def create_orchestrator() -> OptionalOrchestratorWithReport:
    report = Report()
    non_build_repos = [
        {
            "name": "csCMake",
            "description": "The cscosine CMake facilitator",
            "target_directory": "workspace/csCMake",
            "repo_url": "git@github.com:cscosine/csCMake.git",
        },
    ]

    build_repos = [
        {
            "name": "eigen3",
            "description": "The cscosine eigen3 library",
            "target_directory": "workspace/eigen3",
            "repo_url": "git@github.com:cscosine/eigen3.git",
            "config": BuildConfig.RELEASE
        },
        {
            "name": "fmt",
            "description": "The fmt library",
            "target_directory": "workspace/fmt",
            "repo_url": "git@github.com:cscosine/fmt.git",
            "config": BuildConfig.DEBUG_RELEASE
        },
        {
            "name": "fmt-eigen",
            "description": "The fmt-eigen library",
            "target_directory": "workspace/fmt-eigen",
            "repo_url": "git@github.com:cscosine/fmt-eigen.git",
            "config": BuildConfig.RELEASE
        },
    ]

    o = Orchestrator ()
    p = o.create_phase("Repos Update")

    skip_get_repository = True
    skip_build = False

    if skip_get_repository:
        report.append_warning("Skipping repository cloning steps")
    else:
        for repo in non_build_repos + build_repos:
            p.add_step(
                StepGetRepository(
                    repo_type=RepositoryType.GIT,
                    name=repo["name"],
                    description=repo["description"],
                    target_directory=repo["target_directory"],
                    repo_url=repo["repo_url"],
                    repo_ref="orchestrator",
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
            workflow_descriptions = get_supported_context_os_architecture_list()
            #context_os_architecture: ContextOsArchitecture
            #context_compiler_generator: ContextCompilerGenerator

            for workflow_description in workflow_descriptions:
                workflow_name = create_context_os_architecture_compiler_generator_string(workflow_description)
                p.add_step(
                    StepCMakeWorkflow(
                        name = f"{repo['name']} CMake Workflow {workflow_name}",
                        description=f"CMake workflow for {repo['name']} with config: {repo['config']}",
                        source_dir=repo["target_directory"],
                        config=repo["config"],
                        context_os_architecture = workflow_description.context_os_architecture,
                        context_compiler_generator = workflow_description.context_compiler_generator,
                    ).add_extra(StepExecuteOnMatchingContext())
                )
    return OptionalResultWithReport.createResultAndReport(o, report)

def main(argv: Sequence[str] | None = None) -> int:
    script_path = str(Path(__file__).resolve())
    return orchestrator_main_with_default_run(script_path, argv)


if __name__ == "__main__":
    sys.exit(main())
