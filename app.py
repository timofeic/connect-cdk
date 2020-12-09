#!/usr/bin/env python3

from aws_cdk import core

from connect_cdk.connect_cdk_stack import ConnectCdkStack


app = core.App()
ConnectCdkStack(app, "connect-cdk")

app.synth()
