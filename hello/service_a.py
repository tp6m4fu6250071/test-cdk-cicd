from aws_cdk import core
from aws_cdk import (
    aws_lambda as lambda_,
    aws_ec2 as ec2,
    core
)

class MyServiceStackA(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        hello = lambda_.Function(
            self, 'HelloHandler',
            runtime = lambda_.Runtime.PYTHON_3_7,
            code = lambda_.Code.asset('./hello/lambda_code'),
            handler = 'lambda_function.lambda_handler',
            timeout = core.Duration.seconds(10),
        )
