from aws_cdk import core
from aws_cdk import (
    aws_lambda as lambda_,
    aws_ec2 as ec2,
    aws_s3 as s3,
    core
)
import boto3

'''
CODE_PATH = './hello/lambda_code/'
LAMBDA_CODE_FILE_NAME = 'lambda_function_a'
LAMBDA_CODE_FILE_EXT = 'py'
LAMBDA_CODE_BUCKET = 'testhomework'
'''

class MyServiceStackA(core.Stack):

    def __init__(self, scope: core.Construct, id: str, code_path, lambda_code_file, lambda_code_bucket_name, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.code_path = code_path
        self.lambda_code_file = lambda_code_file
        self.lambda_code_bucket_name = lambda_code_bucket_name
        tmp_lambda_code_file = lambda_code_file.split('.')
        self.lambda_code_file_name = tmp_lambda_code_file[0]
        self.lambda_code_file_ext = tmp_lambda_code_file[1]

        self.upload_code()

        lambda_code_bucket = s3.Bucket.from_bucket_attributes(
            self, 'LambdaCodeBucket',
            bucket_name=self.lambda_code_bucket_name
        )

        hello = lambda_.Function(
            self, 'HelloHandler',
            runtime = lambda_.Runtime.PYTHON_3_7,
            #code = lambda_.Code.asset('./hello/lambda_code'),
            code = lambda_.S3Code(
                bucket = lambda_code_bucket,
                key = self.lambda_code_file
            ),
            handler = self.lambda_code_file_name+'.lambda_handler',
            timeout = core.Duration.seconds(10),
        )
    def upload_code(self):
        with open(self.code_path+self.lambda_code_file, 'r') as f:
            client = boto3.client('s3')
            client.put_object(
                Bucket = self.lambda_code_bucket_name,
                Body = f.read(),
                Key = self.lambda_code_file
            )
