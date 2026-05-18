#!/usr/bin/env python3
from typing import TypeAlias

from csorchestrator.core.report import Report
from csorchestrator.orchestrator.orchestrator import Orchestrator
from csorchestrator.orchestrator.execution import validate_and_execute_orchestrator
from csorchestrator.step.step_get_repository import StepGetRepository,RepositoryType,StepGetRepositoryExtraDepthOne
from csorchestrator.step.step_cmake_command import StepCMakeWorkflow
from csorchestrator.reporters.orchestrator_executor_reporter_print import OrchestratorExecutorReporterPrint
from csorchestrator.utils.presets.supported_variants import GeneratorType, BuildConfig, get_supported_combined_workflow_for_multi_config_generators, get_supported_context_os_architecture_list_string, get_all_supported_workflow_names_list
from csorchestrator.orchestrator.orchestrator_executor import flatten_orchestrator_executor_visit_reports
from csorchestrator.core.optional_result_with_report import OptionalResultWithReport

OptionalOrchestratorWithReport: TypeAlias = OptionalResultWithReport[Orchestrator]

def create_orchestrator() -> OptionalOrchestratorWithReport:
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
            "configs": [BuildConfig.RELEASE]
        },
        {
            "name": "fmt",
            "description": "The fmt library",
            "target_directory": "workspace/fmt",
            "repo_url": "git@github.com:cscosine/fmt.git",
            "configs": [BuildConfig.DEBUG, BuildConfig.RELEASE]
        },
        {
            "name": "fmt-eigen",
            "description": "The fmt-eigen library",
            "target_directory": "workspace/fmt-eigen",
            "repo_url": "git@github.com:cscosine/fmt-eigen.git",
            "configs": [BuildConfig.RELEASE]
        },
    ]

    o = Orchestrator ()
    p = o.create_phase("Repos Update")

    skip_get_repository = False

    if skip_get_repository:
        print("Skipping repository cloning steps")
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

    for repo in build_repos:
        p = o.create_phase(f"{repo['name']} Configure-Build-Test-Install")
        workflow_names_expected = get_all_supported_workflow_names_list(repo["configs"])

        if workflow_names_expected.value is None:
            assert workflow_names_expected.error is not None
            return OptionalResultWithReport.createReport(Report().append_error(f"Error for {repo['name']}: {workflow_names_expected.error}"))

        for workflow_name in workflow_names_expected.value:
            p.add_step(
                StepCMakeWorkflow(
                    name = f"{repo['name']} CMake Workflow {workflow_name}",
                    description=f"CMake workflow for {repo['name']} with configs: {repo['configs']}",
                    source_dir=repo["target_directory"],
                    workflow_name=workflow_name,
                )
            )
    return OptionalResultWithReport.createResultAndReport(o, Report())

def execute() -> None:
    orchestratorResult = create_orchestrator()
    if orchestratorResult.result is None:
        orchestratorResult.report.print()
    else:
        executionResult = validate_and_execute_orchestrator(orchestratorResult.result, "./", OrchestratorExecutorReporterPrint())
        
        executionResult.report_pre_execution.print()
        flatten_orchestrator_executor_visit_reports(executionResult.report_execution).print()

if __name__ == "__main__":
    execute()