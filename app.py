#!/usr/bin/env python3

from aws_cdk import core

from aws_networking.vpc_stack import VPCStack

app = core.App()
# AwsNetworkingStack(app, "aws-networking")
VPCStack(app, 'vpc-stack')
app.synth()
