#!/usr/bin/env python3

from aws_cdk import core

from aws_networking.aws_networking_stack import AwsNetworkingStack


app = core.App()
AwsNetworkingStack(app, "aws-networking")

app.synth()
