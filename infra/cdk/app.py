#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.hrs_stack import HrsStack

app = cdk.App()
HrsStack(app, "HrsStack")
app.synth()
