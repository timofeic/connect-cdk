from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_iam as iam
)
from aws_cdk.core import CustomResource, CfnOutput
from aws_cdk.custom_resources import (AwsCustomResource, AwsCustomResourcePolicy, PhysicalResourceId)
import aws_cdk.aws_logs as logs
import aws_cdk.custom_resources as cr


class ConnectCdkStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        instance_alias = self.node.try_get_context("instance_alias")

        on_event = _lambda.Function(
                self, 'ConnectOnEventHandler',
                runtime=_lambda.Runtime.PYTHON_3_7,
                code=_lambda.Code.asset('lambda'),
                handler='connect_create2.on_event',
                log_retention=logs.RetentionDays.ONE_DAY,
                environment={
                    "InstanceAlias": instance_alias
                }
            )
        
        is_complete = _lambda.Function(
                self, 'ConnectIsCompleteHandler',
                runtime=_lambda.Runtime.PYTHON_3_7,
                code=_lambda.Code.asset('lambda'),
                handler='connect_create2.is_complete',
                log_retention=logs.RetentionDays.ONE_DAY,
                environment={
                    "InstanceAlias": instance_alias
                }
            )

        on_event.add_to_role_policy(iam.PolicyStatement(
            actions=["connect:CreateInstance",
                    "connect:DeleteInstance",
                    "connect:ListInstances",
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
                    "iam:PutRolePolicy",
                    "lambda:AddPermission",
                    "lambda:RemovePermission",
                    "events:PutRule",
                    "events:DeleteRule",
                    "events:PutTargets",
                    "events:RemoveTargets"
                    ],
            resources=["*"]
        ))

        is_complete.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "connect:DescribeInstance",
                "connect:ListLambdaFunctions",
                "connect:ListLexBots",
                "connect:ListInstances",
                "connect:ListInstanceStorageConfigs",
                "connect:ListApprovedOrigins",
                "connect:ListSecurityKeys",
                "connect:DescribeInstanceAttributes",
                "connect:DescribeInstanceStorageConfig",
                "ds:DescribeDirectories"
            ],
            resources=["*"]
        ))

        connect_provider = cr.Provider(self, "ConnectProvider",
            on_event_handler=on_event,
            is_complete_handler=is_complete,
            log_retention=logs.RetentionDays.ONE_DAY,
            query_interval=core.Duration.seconds(10),
            total_timeout=core.Duration.minutes(5)
        )

        connect_resource = CustomResource(self, "ConnectInstance", service_token=connect_provider.service_token)

        instance_id = connect_resource.get_att_string("InstanceId")
        instance_arn = connect_resource.get_att_string("InstanceArn")

        CfnOutput(
            self, "InstanceId",
            description="Amazon Connect Instance ID",
            value = instance_id
        )
        CfnOutput(
            self, "InstanceArn",
            description="Amazon Connect Instance ARN",
            value = instance_arn
        )

        on_event2 = _lambda.Function(
            self, 'ConnectAttrOnEventHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='connect_attributes.on_event',
            log_retention=logs.RetentionDays.ONE_DAY,
            environment={
                "InstanceId": instance_id
            }
        )

        on_event2.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "connect:CreateContactFlow",
                "connect:CreateInstance",
                "connect:CreateQueue",
                "connect:DescribeInstance",
                "connect:ListHoursOfOperations",
                "connect:ListInstances",
                "ds:DescribeDirectories",
            ],
            resources=["*"]
        ))

        connect_attr_provider = cr.Provider(self, "ConnectAttrProvider",
            on_event_handler=on_event2,
            log_retention=logs.RetentionDays.ONE_DAY
        )

        connect_attr_resource = CustomResource(self, "ConnectInstanceAttributes", service_token=connect_attr_provider.service_token)

        CfnOutput(
            self, "ContactFlowId",
            description="Amazon Connect Contact Flow ID",
            value = connect_attr_resource.get_att_string("ContactFlowId")
        )
        CfnOutput(
            self, "QueueId",
            description="Amazon Connect Queue Id",
            value = connect_attr_resource.get_att_string("DemoQueueId")
        )

        lex_role = iam.Role(self, "LexRole",
            assumed_by=iam.ServicePrincipal("lexv2.amazonaws.com")
        )

        lex_role.add_to_policy(iam.PolicyStatement(
            resources=["*"],
            actions=["polly:SynthesizeSpeech"]
        ))

        lex_on_event = _lambda.Function(
            self, 'LexOnEventHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='lex_bot.on_event',
            log_retention=logs.RetentionDays.ONE_DAY,
            environment={
                "RoleArn": lex_role.role_arn
            }
        )

        lex_is_complete = _lambda.Function(
            self, 'LexIsCompleteHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='lex_bot.is_complete',
            log_retention=logs.RetentionDays.ONE_DAY,
            environment={
                "RoleArn": lex_role.role_arn
            }
        )

        lex_on_event.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "lex:CreateBot",
                "lex:CreateBotLocale",
                "lex:CreateIntent",
                "lex:CreateSlot",
                "lex:DeleteBot",
                "lex:DeleteBotLocale",
                "lex:ListBots",
                "iam:PassRole"
            ],
            resources=["*"]
        ))

        lex_is_complete.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "lex:ListBots",
                "iam:PassRole"
            ],
            resources=["*"]
        ))

        lex_provider = cr.Provider(self, "LexProvider",
            on_event_handler=lex_on_event,
            is_complete_handler=lex_is_complete,
            log_retention=logs.RetentionDays.ONE_DAY,
            query_interval=core.Duration.seconds(10),
            total_timeout=core.Duration.minutes(5)
        )

        lex_resource = CustomResource(self, "LexBot", service_token=lex_provider.service_token)

        bot_id = lex_resource.get_att_string("BotId")

        CfnOutput(
            self, "BotId",
            description="Amazon Lex Bot ID",
            value = bot_id
        )

        lex_on_event2 = _lambda.Function(
            self, 'LexAttrOnEventHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='lex_bot_attributes.on_event',
            log_retention=logs.RetentionDays.ONE_DAY,
            environment={
                "BotId": bot_id
            }
        )

        lex_on_event2.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "lex:CreateBotLocale",
                "lex:CreateIntent",
                "lex:CreateSlot",
                "lex:ListBots",
                "iam:PassRole"
            ],
            resources=["*"]
        ))

        lex_attr_provider = cr.Provider(self, "LexAttrProvider",
            on_event_handler=lex_on_event2,
            log_retention=logs.RetentionDays.ONE_DAY
        )

        lex_attr_resource = CustomResource(self, "LexBotAttributes", service_token=lex_attr_provider.service_token)