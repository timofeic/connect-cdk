#!/usr/bin/env python3

from aws_cdk import core as cdk

from connect_cdk.connect_cdk_stack import ConnectCdkStack
from connect_cdk.lex_stack import LexStack
import os

app = cdk.App()

prod = cdk.Environment(
    account=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"]),
    region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"]))

lex_stack = LexStack(app, "LexStack", env=prod)

cdk_stack = ConnectCdkStack(app, "ConnectStack",
    bot_id=lex_stack.bot_id,
    bot_alias_id=lex_stack.bot_alias_id,
    bucket=lex_stack.bucket_name,
    env=prod)

app.synth()
