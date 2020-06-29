#!/usr/bin/env python3
import inspect

from aws_cdk import core

from hello.service_a import MyServiceStackA
from hello.service_b import MyServiceStackB
import aws_cdk.aws_codebuild as codebuild
import aws_cdk.aws_codepipeline as codepipeline
import aws_cdk.aws_codepipeline_actions as codepipeline_actions
import aws_cdk.app_delivery as cicd
import aws_cdk.aws_iam as iam

CODE_PATH = './hello/lambda_code'
SOURCE_BUNDLE_NAME = 'cdk_pipeline_function.zip'
LAMBDA_CODE_BUCKET = 'testhomework'
GITHUB_OWNER = 'tp6m4fu6250071'
GITHUB_REPO = 'test-cdk-cicd'
LAMBDA_FUNCTION_FILENAME_A = 'lambda_function_a.py'
LAMBDA_FUNCTION_FILENAME_B = 'lambda_function_b.py'

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

project = codebuild.PipelineProject(pipeline_stack, "CodeBuild",
    environment_variables = {
        "LAMBDA_CODE_BUCKET": codebuild.BuildEnvironmentVariable(value=LAMBDA_CODE_BUCKET),
        "CODE_PATH": codebuild.BuildEnvironmentVariable(value=CODE_PATH),
        "SOURCE_BUNDLE_NAME": codebuild.BuildEnvironmentVariable(value=SOURCE_BUNDLE_NAME),
        "LAMBDA_FUNCTION_FILENAME_A": codebuild.BuildEnvironmentVariable(value=LAMBDA_FUNCTION_FILENAME_A),
        "LAMBDA_FUNCTION_FILENAME_B": codebuild.BuildEnvironmentVariable(value=LAMBDA_FUNCTION_FILENAME_B)

    }
)
### for no Assets workaround, I need to add the permission for CodeBuild service role to access my bucket. Otherwise, CodeBuild could not put my lambda code while running "cdk synth" command in the build project.
myS3AccessPolicy = iam.Policy(pipeline_stack, "MyS3AccessPolicy",
    roles = [
        project.role
    ]
).add_statements(
    iam.PolicyStatement(
        actions = [
            's3:*'
        ],
        effect = iam.Effect.ALLOW,
        resources = [
            'arn:aws:s3:::'+LAMBDA_CODE_BUCKET,
            'arn:aws:s3:::'+LAMBDA_CODE_BUCKET+'/*'
        ] # arn:aws:s3:::bucket_name/key_name
    )
)
### End of this no Assets workaround

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
service_stack_a = MyServiceStackA(app, "ServiceStackA", SOURCE_BUNDLE_NAME, LAMBDA_FUNCTION_FILENAME_A, LAMBDA_CODE_BUCKET)
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
service_stack_b = MyServiceStackB(app, "ServiceStackB", SOURCE_BUNDLE_NAME, LAMBDA_FUNCTION_FILENAME_B, LAMBDA_CODE_BUCKET)
deploy_service_bAction = cicd.PipelineDeployStackAction(
    stack=service_stack_b,
    input=synthesized_app,
    create_change_set_run_order=10,
    admin_permissions=True,
    create_change_set_action_name = 'ChangeSetB',
    execute_change_set_action_name = 'ExecuteB'
)
deploy_stage.add_action(deploy_service_bAction)

### Debugging (print out the object's information to see what can I do.)
'''
for obj in pipeline.node.find_all():
    print(obj)
    print(dir(obj))
    try: 
        print(obj.logical_id)
    except:
        pass
    print('-------------------')
'''
# CdkPipelineStack.CodePipeline.build.CodeBuild.CodePipelineActionRole.Resource.LogicalID.78
# print(pipeline.node.try_find_child('build').node.try_find_child('CodeBuild').node.try_find_child('CodePipelineActionRole'))
# CdkPipelineStack.CodePipeline.source.GitHub.WebhookResource.LogicalID.51
#print(((pipeline.node.try_find_child('source')).node.try_find_child('GitHub')).node.try_find_child('WebhookResource'))
#print(dir(((pipeline.node.try_find_child('source')).node.try_find_child('GitHub')).node.try_find_child('WebhookResource')))


app.synth()
