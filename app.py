#!/usr/bin/env python3

from aws_cdk import core

from hello.service_a import MyServiceStackA
from hello.service_b import MyServiceStackB
import aws_cdk.aws_codebuild as codebuild
import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_codepipeline_actions as codepipeline_actions

app = core.App()
pipeline_stack = core.Stack(app, "CdkPipelineStack")
pipeline = codepipeline.Pipeline(
    pipeline_stack, "CodePipeline",
    restart_execution_on_update = True
)

source_output = codepipeline.Artifact()
source = codepipeline_actions.GitHubSourceAction(
    action_name="GitHub",
    output=source_output
)
pipeline.add_stage(
    stage_name="source",
    actions=[source]
)

project = codebuild.PipelineProject(pipeline_stack, "CodeBuild")
synthesized_app = codepipeline.Artifact()
build_action = codepipeline_actions.CodeBuildAction(
    action_name="CodeBuild",
    project=project,
    input=source_output,
    outputs=[synthesized_app]
)
pipeline.add_stage(
    stage_name="build",
    actions=[build_action]
)

self_update_stage = pipeline.add_stage(stage_name="SelfUpdate")
self_update_stage.add_action(cicd.PipelineDeployStackAction(
    stack=pipeline_stack,
    input=synthesized_app,
    admin_permissions=True
))

deploy_stage = pipeline.add_stage(stage_name="Deploy")
service_stack_a = MyServiceStackA(app, "ServiceStackA")
deploy_service_aAction = cicd.PipelineDeployStackAction(
    stack=service_stack_a,
    input=synthesized_app,
    create_change_set_run_order=1,
    admin_permissions=True
)
deploy_stage.add_action(deploy_service_aAction)

service_stack_b = MyServiceStackB(app, "ServiceStackB")
deploy_service_bAction = cicd.PipelineDeployStackAction(
    stack=service_stack_b,
    input=synthesized_app,
    create_change_set_run_order=2,
    admin_permissions=True
)
deploy_stage.add_action(deploy_service_bAction)

app.synth()
