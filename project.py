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
        target_directory="workspace/csCMake",
        repo_url="git@github.com:cscosine/csCMake.git",
        repo_ref="orchestrator",
    ).add_extra(StepGetRepositoryExtraDepthOne(on_local_checkout=False, on_github_action_checkout=True))
)

p.add_step(
    StepGetRepository(
        repo_type=RepositoryType.GIT,
        name="eigen3",
        description="The cscosine eigen3 library",
        target_directory="workspace/eigen3",
        repo_url="git@github.com:cscosine/eigen3.git",
        repo_ref="orchestrator",
    ).add_extra(StepGetRepositoryExtraDepthOne(on_local_checkout=False, on_github_action_checkout=True))
)

p = o.create_phase("Configure")

## p.add_step(
##     StepCMake("eigen3", CMakeStep.CONFIGURE, "linux-ninja-release")
## )
## p.add_step(
##     StepCMake("eigen3", CMakeStep.CONFIGURE, "linux-ninja-debug")
## )
## 
## p.add_step(
##     StepCMake("eigen3",  CMakeStep.BUILD, "linux-ninja-release")
## )
## p.add_step(
##     StepCMake("eigen3",  CMakeStep.BUILD, "linux-ninja-debug")
## )
## 
## p.add_step(
##     StepCMake("eigen3",  CMakeStep.BUILD, "linux-ninja-release-install")
## )
## p.add_step(
##     StepCMake("eigen3",  CMakeStep.BUILD, "linux-ninja-debug-install")
## )
## 
## p.add_step(
##     StepCMake("eigen3",  CMakeStep.TEST, "linux-ninja-release-test")
## )
## p.add_step(
##     StepCMake("eigen3",  CMakeStep.TEST, "linux-ninja-debug-test")
## )
## 
# p.add_step(
#     StepCMake("eigen3",  CMakeStep.WORKFLOW, "linux-ninja-debug-test")
# )

# to be complete CMakeStep.PACKAGE -> packagePresets

validate_and_execute_orchestrator(o, "./", OrchestratorExecutorReporterPrint())