"""
JalaNetra AWS CDK Infrastructure (Python)
Defines cloud architecture for future production deployment.

⚠️  DO NOT DEPLOY during the hackathon unless you understand AWS charges.
⚠️  This defines infrastructure only. No deployment is triggered by running cdk synth.

Prerequisites for cdk synth:
    pip install aws-cdk-lib constructs
    npm install -g aws-cdk
    cdk bootstrap aws://<ACCOUNT>/<REGION>  # only needed for actual deploy
"""
import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as integrations,
    aws_events as events,
    aws_events_targets as targets,
    aws_sns as sns,
    aws_sns_subscriptions as subs,
    aws_iam as iam,
    aws_logs as logs,
    Duration,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct


class JalaNetraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # -------------------------------------------------------------------
        # S3 — Raw data bucket
        # -------------------------------------------------------------------
        raw_bucket = s3.Bucket(
            self, "RawDataBucket",
            bucket_name=f"jalanetra-raw-{self.account}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="archive-old-data",
                    enabled=True,
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90),
                        )
                    ],
                )
            ],
        )

        # -------------------------------------------------------------------
        # DynamoDB Tables — JalaNetra Pulse
        # -------------------------------------------------------------------
        # Ward state table
        ward_table = dynamodb.Table(
            self, "WardStateTable",
            table_name="ward_state",
            partition_key=dynamodb.Attribute(name="ward_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # Water reports table (JalaNetra Pulse Real-Time Ingestion)
        water_reports_table = dynamodb.Table(
            self, "WaterReportsTable",
            table_name="water_reports",
            partition_key=dynamodb.Attribute(name="ward_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="created_at", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            time_to_live_attribute="ttl",
        )

        # Community alerts table (JalaNetra Pulse Outage Clusters)
        community_alerts_table = dynamodb.Table(
            self, "CommunityAlertsTable",
            table_name="community_alerts",
            partition_key=dynamodb.Attribute(name="ward_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="alert_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Alert subscriptions table
        subscriptions_table = dynamodb.Table(
            self, "AlertSubscriptionsTable",
            table_name="subscriptions",
            partition_key=dynamodb.Attribute(name="ward_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="phone_hash", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # -------------------------------------------------------------------
        # SNS — Alert topic
        # NOTE: In demo mode, no subscriptions are added automatically.
        # Phone numbers must be verified in SNS sandbox before use.
        # -------------------------------------------------------------------
        alert_topic = sns.Topic(
            self, "AlertTopic",
            topic_name="jalanetra-alerts",
            display_name="JalaNetra Water Stress Alerts",
        )

        # -------------------------------------------------------------------
        # IAM — Shared Lambda execution role
        # -------------------------------------------------------------------
        lambda_role = iam.Role(
            self, "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        # Least-privilege DynamoDB access
        ward_table.grant_read_write_data(lambda_role)
        water_reports_table.grant_read_write_data(lambda_role)
        community_alerts_table.grant_read_write_data(lambda_role)
        subscriptions_table.grant_read_write_data(lambda_role)

        # S3 read access
        raw_bucket.grant_read(lambda_role)

        # SNS publish access
        alert_topic.grant_publish(lambda_role)

        # Amazon Polly access (synthesize speech)
        lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["polly:SynthesizeSpeech"],
                resources=["*"],
                effect=iam.Effect.ALLOW,
            )
        )

        # -------------------------------------------------------------------
        # Lambda — API Handler
        # -------------------------------------------------------------------
        api_lambda = lambda_.Function(
            self, "ApiHandler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("../backend"),
            handler="lambda_handler.handler",
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "WARD_TABLE": ward_table.table_name,
                "REPORTS_TABLE": reports_table.table_name,
                "SUBSCRIPTION_TABLE": subscriptions_table.table_name,
                "S3_BUCKET": raw_bucket.bucket_name,
                "ALERT_TOPIC_ARN": alert_topic.topic_arn,
                "DATA_MODE": "real",
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # -------------------------------------------------------------------
        # Lambda — Ingestion / Data Refresh
        # -------------------------------------------------------------------
        ingest_lambda = lambda_.Function(
            self, "IngestHandler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("../backend"),
            handler="lambda_ingest.handler",
            role=lambda_role,
            timeout=Duration.seconds(300),
            memory_size=1024,
            environment={
                "S3_BUCKET": raw_bucket.bucket_name,
                "WARD_TABLE": ward_table.table_name,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # -------------------------------------------------------------------
        # Lambda — Alert Evaluator
        # -------------------------------------------------------------------
        alert_eval_lambda = lambda_.Function(
            self, "AlertEvaluatorHandler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("../backend"),
            handler="lambda_alert_eval.handler",
            role=lambda_role,
            timeout=Duration.seconds(120),
            memory_size=512,
            environment={
                "WARD_TABLE": ward_table.table_name,
                "SUBSCRIPTION_TABLE": subscriptions_table.table_name,
                "ALERT_TOPIC_ARN": alert_topic.topic_arn,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
        )

        # -------------------------------------------------------------------
        # API Gateway HTTP API
        # -------------------------------------------------------------------
        api = apigwv2.HttpApi(
            self, "JalaNetraApi",
            api_name="jalanetra-api",
            description="JalaNetra Water Security API",
            cors_preflight=apigwv2.CorsPreflightOptions(
                allow_headers=["Content-Type", "Authorization"],
                allow_methods=[
                    apigwv2.CorsHttpMethod.GET,
                    apigwv2.CorsHttpMethod.POST,
                    apigwv2.CorsHttpMethod.OPTIONS,
                ],
                allow_origins=["https://*.amplifyapp.com", "http://localhost:5173"],
            ),
        )

        api_integration = integrations.HttpLambdaIntegration(
            "ApiIntegration", api_lambda
        )
        api.add_routes(
            path="/{proxy+}",
            methods=[apigwv2.HttpMethod.ANY],
            integration=api_integration,
        )

        # -------------------------------------------------------------------
        # EventBridge — Scheduled alert evaluation (every 6 hours)
        # -------------------------------------------------------------------
        events.Rule(
            self, "AlertEvalSchedule",
            rule_name="jalanetra-alert-eval",
            description="JalaNetra: evaluate ward risk and dispatch alerts",
            schedule=events.Schedule.rate(Duration.hours(6)),
            targets=[targets.LambdaFunction(alert_eval_lambda)],
        )

        # EventBridge — Daily ingestion refresh
        events.Rule(
            self, "IngestSchedule",
            rule_name="jalanetra-ingest",
            description="JalaNetra: refresh groundwater and rainfall data",
            schedule=events.Schedule.cron(hour="2", minute="0"),
            targets=[targets.LambdaFunction(ingest_lambda)],
        )

        # -------------------------------------------------------------------
        # Outputs
        # -------------------------------------------------------------------
        CfnOutput(self, "ApiEndpoint", value=api.api_endpoint, description="API Gateway endpoint URL")
        CfnOutput(self, "RawBucketName", value=raw_bucket.bucket_name, description="S3 raw data bucket")
        CfnOutput(self, "AlertTopicArn", value=alert_topic.topic_arn, description="SNS alert topic ARN")
        CfnOutput(self, "WardTableName", value=ward_table.table_name, description="DynamoDB ward state table")


app = cdk.App()
JalaNetraStack(
    app, "JalaNetraStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account") or "123456789012",
        region=app.node.try_get_context("region") or "ap-south-1",
    ),
    description="JalaNetra — Mangaluru Water Security Early Warning System",
)
app.synth()
