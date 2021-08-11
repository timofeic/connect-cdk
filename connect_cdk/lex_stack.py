from aws_cdk import (
    core as cdk,
    aws_lambda as _lambda,
    aws_dynamodb as ddb,
    aws_iam as iam,
    aws_s3 as s3,
)
from aws_cdk.core import CustomResource, CfnOutput
import aws_cdk.aws_logs as logs
import aws_cdk.custom_resources as cr

class LexStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lex_locale_code = self.node.try_get_context("lex_locale_code")

        bucket = s3.Bucket(self, "RecordingTranscript",
            encryption=s3.BucketEncryption.KMS
            #bucket_name=bucket_name
        )

        self.bucket_name = bucket.bucket_name

        @property
        def bucket_name(self):
            return self.bucket_name

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
                "lex:DeleteBot",
                "lex:DeleteBotAlias",
                "lex:DeleteIntent",
                "lex:DeleteUtterances",
                "lex:DeleteSlot",
                "lex:DeleteSlotType",
                "lex:DeleteBotChannel",
                "lex:DeleteBotLocale",
                "lex:DeleteBotVersion",
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
            query_interval=cdk.Duration.seconds(10),
            total_timeout=cdk.Duration.minutes(5)
        )

        lex_resource = CustomResource(
            self, 
            "LexBot", 
            service_token=lex_provider.service_token
        )

        self.bot_id = lex_resource.get_att_string("BotId")
        self.bot_name = lex_resource.get_att_string("BotName")

        @property
        def bot_name(self):
            return self.bot_name

        @property
        def bot_id(self):
            return self.bot_id

        CfnOutput(
            self, "BotId",
            description="Amazon Lex Bot ID",
            value = self.bot_id
        )

        lex_bot_locale = _lambda.Function(
            self, 'LexLocaleOnEventHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='lex_bot_locale.on_event',
            log_retention=logs.RetentionDays.ONE_DAY,
            environment={
                "BotId": self.bot_id,
                "LocaleId": lex_locale_code
            },
            timeout=cdk.Duration.seconds(15)
        )

        lex_bot_locale_complete = _lambda.Function(
            self, 'LexLocaleIsCompleteHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='lex_bot_locale.is_complete',
            log_retention=logs.RetentionDays.ONE_DAY,
            environment={
                "BotId": self.bot_id,
                "LocaleId": lex_locale_code
            }
        )

        lex_bot_locale.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "lex:CreateBotLocale",
                "lex:ListBots",
                "iam:PassRole"
            ],
            resources=["*"]
        ))

        lex_bot_locale_complete.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "lex:DescribeBotLocale",
                "iam:PassRole"
            ],
            resources=["*"]
        ))

        lex_bot_locale_provider = cr.Provider(self, "LexLocaleProvider",
            on_event_handler=lex_bot_locale,
            is_complete_handler=lex_bot_locale_complete,
            log_retention=logs.RetentionDays.ONE_DAY,
            query_interval=cdk.Duration.seconds(10),
            total_timeout=cdk.Duration.minutes(5)
        )

        lex_bot_locale_resource = CustomResource(
            self, 
            "LexBotLocale", 
            service_token=lex_bot_locale_provider.service_token
        )

        lex_locale_id = lex_bot_locale_resource.get_att_string("LocaleId")

        lex_bot_intent = _lambda.Function(
            self, 'LexIntentOnEventHandler',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='lex_bot_intent.on_event',
            log_retention=logs.RetentionDays.ONE_DAY,
            environment={
                "BotId": self.bot_id,
                "LocaleId": lex_locale_id
            },
            timeout=cdk.Duration.seconds(30)
        )

        lex_bot_intent.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "lex:CreateIntent",
                "lex:CreateSlot",
                "lex:CreateSlotType",
                "lex:CreateBotAlias",
                "lex:CreateBotVersion",
                "lex:DescribeBotVersion",
                "lex:ListBots",
                "lex:BuildBotLocale",
                "iam:PassRole"
            ],
            resources=["*"]
        ))

        lex_bot_intent_provider = cr.Provider(self, "LexIntentProvider",
            on_event_handler=lex_bot_intent,
            log_retention=logs.RetentionDays.ONE_DAY,
        )

        lex_bot_intent_resource = CustomResource(
            self, 
            "LexBotIntent", 
            service_token=lex_bot_intent_provider.service_token
        )

        self.bot_alias = lex_bot_intent_resource.get_att_string("BotAlias")
        self.bot_alias_id = lex_bot_intent_resource.get_att_string("BotAliasId")

        @property
        def bot_alias(self):
            return self.bot_alias

        @property
        def bot_alias_id(self):
            return self.bot_alias_id

        meter_table = ddb.Table(
            self, 'MeterReadingTable',
            partition_key={'name':'user_id', 'type': ddb.AttributeType.STRING},
            sort_key={'name':'timestamp', 'type': ddb.AttributeType.NUMBER},
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
        )

        meter_table.apply_removal_policy(cdk.RemovalPolicy.DESTROY) #Used while in testing

        user_table = ddb.Table(
            self, 'UserTable',
            partition_key={'name':'PhoneNumber', 'type': ddb.AttributeType.STRING},
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
        )

        user_table.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        otp_table = ddb.Table(
            self, 'OtpTable',
            partition_key={'name':'uuid', 'type': ddb.AttributeType.STRING},
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
        )

        otp_table.apply_removal_policy(cdk.RemovalPolicy.DESTROY)

        meter_read = _lambda.Function(
            self, 'MeterReading',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='meter_reading.lambda_handler',
            environment={
                'METER_READING_TABLE_NAME': meter_table.table_name,
                'USER_TABLE_NAME': user_table.table_name
            },
        )

        meter_read.add_to_role_policy(iam.PolicyStatement(
            actions=["sns:Publish"],
            resources=["*"]
        ))

        meter_table.grant_read_write_data(meter_read)
        user_table.grant_read_write_data(meter_read)

        id_verification = _lambda.Function(
            self, 'IdentityVerification',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.asset('lambda'),
            handler='identity_verification.lambda_handler',
            environment={
                'OTP_TABLE_NAME': otp_table.table_name,
                'USER_TABLE_NAME': user_table.table_name
            },
        )

        id_verification.add_to_role_policy(iam.PolicyStatement(
            actions=["sns:Publish"],
            resources=["*"]
        ))

        user_table.grant_read_write_data(id_verification)
        otp_table.grant_read_write_data(id_verification)