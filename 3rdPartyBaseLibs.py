#!/usr/bin/env python3
import sys
from pathlib import Path
from typing import Sequence

from csorchestrator.foundation.core.report import Report
from csorchestrator.foundation.core.optional_result_with_report import OptionalResultWithReport


from csorchestrator.context.step_utils import StepExecuteOnlyOncePerMatrix, StepSkipExecutionOnLocal
from csorchestrator.step.step_get_repository import RepoUrlParts, StepGetRepositoryGitHub, StepGetRepositoryExtraDepthOne,StepGetRepositoryExtraAccessToken
from csorchestrator.step.step_cmake_command import StepCMakeWorkflow
from csorchestrator.step.step_get_versions_from_cmake_config_package_version import StepGetVersionsFromCMakeConfigPackageVersion
from csorchestrator.step.step_create_archives import StepCreateArchives
from csorchestrator.step.step_upload_artifacts import StepUploadArtifacts, create_artifact_prefix_from_orchestrator_name_version

from csorchestrator.utils.presets.supported_variants import BuildConfig

from csorchestrator.domain.orchestrator.workflow_config import WorkflowConfig, Cron, DayOfWeek, ReleaseCreationOnTagConfig

from csorchestrator.cli.cli import orchestrator_main_with_default_run
from csorchestrator.execution.factory  import OptionalOrchestratorWithReport, create_orchestrator_factory_all_supported_cases


def create_orchestrator() -> OptionalOrchestratorWithReport:
    report = Report()

    base_target_dir = Path("workspace")
    base_install_dir = base_target_dir / Path("install")
    common_repo_ref = "dev"

    repos : dict[str, None | BuildConfig] = {
            "csCMake": None,
            "eigen3": BuildConfig.RELEASE,
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

    o = create_orchestrator_factory_all_supported_cases(
        name = "3rdPartyBaseLibs", 
        version="0.1.0", 
        execution_matrix_name = "orchestrator-matrix"
    )
    
    o.wf_config=WorkflowConfig(
            on_push_branches=["main", "dev"],
            on_push_tags=["'v*.*.*'"],
            on_pull_request_branches=["main"],
            on_dispatch=True,
            on_schedule=Cron.weekly(DayOfWeek.MON, hour=3),
            create_release_on_tag=ReleaseCreationOnTagConfig(name="release-from-artifacts")
        )
    
  
    # ----------------------------------------------------------------
    p = o.create_phase("Repos Update")
    for repo in repos.keys():
        p.add_step(
            StepGetRepositoryGitHub(
                name=f"{repo} Git clone/pull-ff",
                description=f"Clone or pull-ff {repo} description",
                target_directory=(base_target_dir / repo).as_posix(),
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
                StepExecuteOnlyOncePerMatrix()
            ).add_extra(
                StepGetRepositoryExtraAccessToken("${{ secrets.ACTIONS_ORG_ACCESS }}")
            )
        )

    # ----------------------------------------------------------------
    p = o.create_phase(f"Configure-Build-Test-Install")
    for repo, config in repos.items():
        if config is not None:
            p.add_step(
                StepCMakeWorkflow(
                    name = f"{repo} CMake Workflow",
                    description=f"CMake workflow for {repo} with config: {config}",
                    source_dir=(base_target_dir / repo).as_posix(),
                    config=config,
                )
            )
    
    # ----------------------------------------------------------------
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
        ).add_extra(StepSkipExecutionOnLocal())
    )

    p.add_step(
        StepUploadArtifacts(
            name = "Upload Artifacts",
            description= "Upload Artifacts with libs and versions",
            base_install_dir = base_install_dir,
            artifact_prefix = create_artifact_prefix_from_orchestrator_name_version(o)
        )
    )

    return OptionalResultWithReport.createResultAndReport(o, report)

def main(argv: Sequence[str] | None = None) -> int:
    script_path = str(Path(__file__).resolve())
    return orchestrator_main_with_default_run(script_path, argv)


if __name__ == "__main__":
    sys.exit(main())
