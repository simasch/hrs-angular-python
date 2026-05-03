from pathlib import Path

import aws_cdk as cdk
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
)
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_dynamodb as ddb
from aws_cdk import aws_lambda as _lambda
from constructs import Construct

BACKEND_ROOT = Path(__file__).resolve().parents[3] / "backend"


class HrsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        table = ddb.Table(
            self,
            "HrsTable",
            table_name="hrs",
            partition_key=ddb.Attribute(name="PK", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="SK", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=ddb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True,
            ),
        )
        table.add_global_secondary_index(
            index_name="GSI1",
            partition_key=ddb.Attribute(name="GSI1PK", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="GSI1SK", type=ddb.AttributeType.STRING),
        )
        table.add_global_secondary_index(
            index_name="GSI2",
            partition_key=ddb.Attribute(name="GSI2PK", type=ddb.AttributeType.STRING),
            sort_key=ddb.Attribute(name="GSI2SK", type=ddb.AttributeType.STRING),
        )

        api_fn = _lambda.DockerImageFunction(
            self,
            "HrsApi",
            code=_lambda.DockerImageCode.from_image_asset(str(BACKEND_ROOT)),
            timeout=Duration.seconds(15),
            memory_size=512,
            architecture=_lambda.Architecture.ARM_64,
            environment={
                "DYNAMODB_TABLE_NAME": table.table_name,
                "AWS_REGION_NAME": self.region,
                "POWERTOOLS_SERVICE_NAME": "hrs",
                "POWERTOOLS_METRICS_NAMESPACE": "hrs",
            },
        )
        table.grant_read_write_data(api_fn)

        api = apigw.LambdaRestApi(
            self,
            "HrsRestApi",
            handler=api_fn,
            proxy=True,
        )
        cdk.CfnOutput(self, "ApiUrl", value=api.url)
