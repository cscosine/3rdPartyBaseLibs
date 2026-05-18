#!/usr/bin/env python3

from csorchestrator.orchestrator.orchestrator import Orchestrator
from csorchestrator.orchestrator.execution import validate_and_execute_orchestrator
from csorchestrator.step.step_get_repository import StepGetRepository,RepositoryType,StepGetRepositoryExtraDepthOne
from csorchestrator.step.step_cmake_command import StepCMakeWorkflow
from csorchestrator.reporters.orchestrator_executor_reporter_print import OrchestratorExecutorReporterPrint
from cscmake.utils.supported_variants import GeneratorType, BuildConfig, get_supported_combined_workflow_for_multi_config_generators, get_supported_context_os_architecture_list_string, get_all_supported_workflow_names_list
from csorchestrator.orchestrator.orchestrator_executor import flatten_orchestrator_executor_visit_reports

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
    workflow_names = get_all_supported_workflow_names_list(repo["configs"])

    for workflow_name in workflow_names:
        p.add_step(
            StepCMakeWorkflow(
                name = f"{repo['name']} CMake Workflow {workflow_name}",
                description=f"CMake workflow for {repo['name']} with configs: {repo['configs']}",
                source_dir=repo["target_directory"],
                workflow_name=workflow_name,
            )
        )


executionResult = validate_and_execute_orchestrator(o, "./", OrchestratorExecutorReporterPrint())
executionResult.report_pre_execution.print()
flatten_orchestrator_executor_visit_reports(executionResult.report_execution).print()