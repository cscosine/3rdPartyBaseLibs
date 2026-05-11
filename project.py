#!/usr/bin/env python3

from csorchestrator.orchestrator.orchestrator import Orchestrator
from csorchestrator.orchestrator.execution import validate_and_execute_orchestrator
from csorchestrator.step.step_get_repository import StepGetRepository,RepositoryType,StepGetRepositoryExtraDepthOne
from csorchestrator.reporters.orchestrator_executor_reporter_print import OrchestratorExecutorReporterPrint

o = Orchestrator ()
p = o.create_phase("Repo Update")
p.add_step(
    StepGetRepository(
        repo_type=RepositoryType.GIT,
        name="csCMake",
        description="The cscosine CMake facilitator",
        target_directory="src/csCMake",
        repo_url="git@github.com:cscosine/csCMake.git",
        repo_ref="cs-main",
    ).add_extra(StepGetRepositoryExtraDepthOne(on_local_checkout=False, on_github_action_checkout=True))
)

p.add_step(
    StepGetRepository(
        repo_type=RepositoryType.GIT,
        name="eigen3",
        description="The cscosine eigen3 library",
        target_directory="src/eigen3",
        repo_url="git@github.com:cscosine/eigen3.git",
        repo_ref="cs-main",
    ).add_extra(StepGetRepositoryExtraDepthOne(on_local_checkout=False, on_github_action_checkout=True))
)

validate_and_execute_orchestrator(o, "./", OrchestratorExecutorReporterPrint())