from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_iam as iam
)
from aws_cdk.core import CustomResource
import aws_cdk.aws_logs as logs
import aws_cdk.custom_resources as cr


class ConnectCdkStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        on_event = _lambda.Function(
                self, 'ConnectHandler',
                runtime=_lambda.Runtime.PYTHON_3_7,
                code=_lambda.Code.asset('lambda'),
                handler='connect_create.handler',
            )

        on_event.add_to_role_policy(iam.PolicyStatement(
            actions=["connect:CreateInstance",
                    "connect:DeleteInstance",
                    "ds:CreateAlias",
                    "ds:AuthorizeApplication",
                    "ds:UnauthorizeApplication",
                    "ds:CreateIdentityPoolDirectory",
                    "ds:CreateDirectory",
                    "ds:DescribeDirectories",
                    "ds:CheckAlias",
                    "ds:DeleteDirectory",
                    "iam:AttachRolePolicy",
                    "iam:CreateServiceLinkedRole",
                    "iam:PutRolePolicy"],
            resources=["*"]
        ))

        my_provider = cr.Provider(self, "MyProvider",
            on_event_handler=on_event,
            #is_complete_handler=is_complete, # optional async "waiter"
            log_retention=logs.RetentionDays.ONE_DAY
        )

        CustomResource(self, "ConnectInstance", service_token=my_provider.service_token)