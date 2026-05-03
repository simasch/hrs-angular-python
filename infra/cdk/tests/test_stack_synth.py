import aws_cdk as cdk
from aws_cdk.assertions import Template

from stacks.hrs_stack import HrsStack


def test_stack_synthesizes_with_expected_resources() -> None:
    app = cdk.App()
    stack = HrsStack(app, "TestStack")
    template = Template.from_stack(stack)

    template.resource_count_is("AWS::Lambda::Function", 1)
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)
