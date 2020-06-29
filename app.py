#!/usr/bin/env python3
import inspect

from aws_cdk import core

from hello.service_a import MyServiceStackA
from hello.service_b import MyServiceStackB
import aws_cdk.aws_codebuild as codebuild
import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_codepipeline_actions as codepipeline_actions
import aws_cdk.app_delivery as cicd

CODE_PATH = './hello/lambda_code/'
LAMBDA_CODE_BUCKET = 'testhomework'
GITHUB_OWNER = 'tp6m4fu6250071'
GITHUB_REPO = 'test-cdk-cicd'

app = core.App()
pipeline_stack = core.Stack(app, "CdkPipelineStack")
pipeline = codepipeline.Pipeline(
    pipeline_stack, "CodePipeline",
    restart_execution_on_update = True
)

github_token = core.SecretValue.secrets_manager('cdk-github-token', json_field='cdk-github-token')
source_output = codepipeline.Artifact()
source = codepipeline_actions.GitHubSourceAction(
    action_name="GitHub",
    oauth_token=github_token,
    owner = GITHUB_OWNER,
    repo = GITHUB_REPO,
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
#service_stack_a = MyServiceStackA(app, "ServiceStackA")
service_stack_a = MyServiceStackA(app, "ServiceStackA", CODE_PATH, 'lambda_function_a.py', LAMBDA_CODE_BUCKET)
deploy_service_aAction = cicd.PipelineDeployStackAction(
    stack=service_stack_a,
    input=synthesized_app,
    create_change_set_run_order=1,
    admin_permissions=True,
    create_change_set_action_name = 'ChangeSetA',
    execute_change_set_action_name = 'ExecuteA'
)
deploy_stage.add_action(deploy_service_aAction)

#service_stack_b = MyServiceStackB(app, "ServiceStackB")
service_stack_b = MyServiceStackB(app, "ServiceStackB", CODE_PATH, 'lambda_function_b.py', LAMBDA_CODE_BUCKET)
deploy_service_bAction = cicd.PipelineDeployStackAction(
    stack=service_stack_b,
    input=synthesized_app,
    create_change_set_run_order=10,
    admin_permissions=True,
    create_change_set_action_name = 'ChangeSetB',
    execute_change_set_action_name = 'ExecuteB'
)
deploy_stage.add_action(deploy_service_bAction)
'''
for obj in pipeline.node.find_all():
    print(obj)
    print(dir(obj))
    try: 
        print(obj.logical_id)
    except:
        pass
    print('-------------------')
# CdkPipelineStack.CodePipeline.source.GitHub.WebhookResource.LogicalID 51
print(((pipeline.node.try_find_child('source')).node.try_find_child('GitHub')).node.try_find_child('WebhookResource'))
print(dir(((pipeline.node.try_find_child('source')).node.try_find_child('GitHub')).node.try_find_child('WebhookResource')))
'''
app.synth()
