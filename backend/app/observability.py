from aws_lambda_powertools import Logger, Metrics, Tracer

logger = Logger(service="hrs")
tracer = Tracer(service="hrs")
metrics = Metrics(namespace="hrs", service="hrs")
