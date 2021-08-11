from aws_cdk import (
    core as cdk,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_kms as kms,
    aws_s3 as s3,
)
from aws_cdk.core import CustomResource, CfnOutput
import aws_cdk.aws_logs as logs
import aws_cdk.custom_resources as cr

class ConnectCdkStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, bot_alias_id: str, bot_id: str, bucket: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        instance_alias = self.node.try_get_context("instance_alias")
        #bucket_name = self.node.try_get_context("connect_s3_bucket") #optional
        recording_prefix = self.node.try_get_context("recording_s3_prefix")
        transcript_prefix = self.node.try_get_context("transcript_s3_prefix")

        connect_key_statement1 = iam.PolicyStatement(
            actions=["kms:CreateGrant", "kms:Describe*", "kms:Get*", "kms:List*"],
            resources=["*"],
            conditions={
                'StringEquals': {
                    'kms:ViaService': 'connect.%s.amazonaws.com' % self.region,
                    'kms:CallerAccount': self.account
                }
            }
        )
        connect_key_statement1.add_any_principal()
        
        connect_key_statement2 = iam.PolicyStatement(
            actions=["kms:Describe*", "kms:Get*", "kms:List*"],
            resources=["*"],
        )
        connect_key_statement2.add_service_principal("connect.amazonaws.com")

        key = kms.Key(self, "ConnectKey")
        key.add_to_resource_policy(connect_key_statement1)
        key.add_to_resource_policy(connect_key_statement2)

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
            query_interval=cdk.Duration.seconds(10),
            total_timeout=cdk.Duration.minutes(5)
        )

        connect_resource = CustomResource(
            self, 
            "ConnectInstance", 
            service_token=connect_provider.service_token
        )

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
                "InstanceId": instance_id,
                "KeyArn": key.key_arn,
                "BucketName": bucket,
                "RecordingPrefix": recording_prefix,
                "TranscriptPrefix": transcript_prefix
            },
            timeout=cdk.Duration.seconds(30)
        )

        on_event2.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "connect:CreateContactFlow",
                "connect:CreateInstance",
                "connect:CreateQueue",
                "connect:DescribeInstance",
                "connect:ListHoursOfOperations",
                "connect:ListInstances",
                "connect:AssociateInstanceStorageConfig",
                "ds:DescribeDirectories",
                "firehose:DescribeDeliveryStream",
                "iam:AttachRolePolicy",
                "iam:CreateServiceLinkedRole",
                "iam:PutRolePolicy",
                "kinesis:DescribeStream",
                "kms:CreateGrant",
                "kms:DescribeKey",
                "s3:GetBucketAcl",
                "s3:GetBucketLocation"
            ],
            resources=["*"]
        ))

        connect_attr_provider = cr.Provider(self, "ConnectAttrProvider",
            on_event_handler=on_event2,
            log_retention=logs.RetentionDays.ONE_DAY
        )

        connect_attr_resource = CustomResource(
            self, 
            "ConnectInstanceAttributes", 
            service_token=connect_attr_provider.service_token
        )

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

        connect_associate_bot = _lambda.Function(
            self, 'ConnectAssociateBotOnEventHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='connect_associate_bot.on_event',
            log_retention=logs.RetentionDays.ONE_DAY,
            environment={
                "InstanceId": instance_id,
                "Region": self.region,
                "Account": self.account,
                "BotId": bot_id,
                "BotAliasId": bot_alias_id
            },
            timeout=cdk.Duration.seconds(15)
        )

        connect_associate_bot.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "connect:AssociateBot",
                "lex:CreateResourcePolicyStatement",
                "iam:AttachRolePolicy",
                "iam:CreateServiceLinkedRole",
                "iam:PutRolePolicy",
                "lex:CreateResourcePolicy",
                "lex:DescribeBotAlias",
                "lex:GetBot",
                "lex:UpdateResourcePolicy",
                "iam:PassRole"
            ],
            resources=["*"]
        ))

        connect_associate_bot_provider = cr.Provider(self, "ConnectAssociateBotProvider",
            on_event_handler=connect_associate_bot,
            log_retention=logs.RetentionDays.ONE_DAY,
        )

        connect_associate_bot_resource = CustomResource(
            self, 
            "ConnectAssociateBot", 
            service_token=connect_associate_bot_provider.service_token
        )