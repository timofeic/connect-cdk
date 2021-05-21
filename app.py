#!/usr/bin/env python3

from aws_cdk import core

from connect_cdk.connect_cdk_stack import ConnectCdkStack
import os

app = core.App()
ConnectCdkStack(app, "connect-cdk", env=core.Environment(
    account=os.environ.get("CDK_DEPLOY_ACCOUNT", os.environ["CDK_DEFAULT_ACCOUNT"]),
    region=os.environ.get("CDK_DEPLOY_REGION", os.environ["CDK_DEFAULT_REGION"])))

app.synth()
