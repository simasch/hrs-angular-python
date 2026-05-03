from pathlib import Path

import aws_cdk as cdk
from aws_cdk import (
    Duration,
    Stack,
)
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_lambda as _lambda
from constructs import Construct

BACKEND_ROOT = Path(__file__).resolve().parents[3] / "backend"


class HrsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api_fn = _lambda.DockerImageFunction(
            self,
            "HrsApi",
            code=_lambda.DockerImageCode.from_image_asset(str(BACKEND_ROOT)),
            timeout=Duration.seconds(15),
            memory_size=512,
            architecture=_lambda.Architecture.ARM_64,
            environment={
                "POWERTOOLS_SERVICE_NAME": "hrs",
                "POWERTOOLS_METRICS_NAMESPACE": "hrs",
            },
        )

        api = apigw.LambdaRestApi(
            self,
            "HrsRestApi",
            handler=api_fn,
            proxy=True,
        )
        cdk.CfnOutput(self, "ApiUrl", value=api.url)
