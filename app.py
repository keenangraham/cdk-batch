from aws_cdk import App
from aws_cdk import CfnOutput
from aws_cdk import Environment
from aws_cdk import Stack
from aws_cdk import Size

from aws_cdk.aws_ec2 import SubnetSelection
from aws_cdk.aws_ec2 import SubnetType

from aws_cdk.aws_ecs import AwsLogDriverMode
from aws_cdk.aws_ecs import LogDriver
from aws_cdk.aws_ecs import ContainerImage

from aws_cdk.aws_secretsmanager import Secret as SMSecret

from aws_cdk.aws_ecr_assets import Platform

from aws_cdk.aws_iam import Role
from aws_cdk.aws_iam import ServicePrincipal

from aws_cdk.aws_batch import FargateComputeEnvironment
from aws_cdk.aws_batch import JobQueue
from aws_cdk.aws_batch import EcsFargateContainerDefinition
from aws_cdk.aws_batch import EcsJobDefinition
from aws_cdk.aws_batch import Secret

from aws_cdk.aws_events import Rule
from aws_cdk.aws_events import Schedule
from aws_cdk.aws_events import EventPattern
from aws_cdk.aws_events import EventField
from aws_cdk.aws_events import Connection
from aws_cdk.aws_events import ApiDestination
from aws_cdk.aws_events import RuleTargetInput

from aws_cdk.aws_events_targets import BatchJob
from aws_cdk.aws_events_targets import ApiDestination as TargetApiDestination

from aws_cdk.aws_ssm import StringParameter

from aws_cdk.aws_logs import RetentionDays

from aws_cdk.aws_ec2 import Vpc

from constructs import Construct


app = App()


US_WEST_2 = Environment(
    account='618537831167',
    region='us-west-2',
)


class BatchWorkflowStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        '''     
        ComputeEnvironments
        JobDefinitions
        JobQueues
        SchedulingPolicies
        '''
        vpc = Vpc.from_lookup(
            self,
            'VPC',
            vpc_id='vpc-ea3b6581'
        )

        compute_environment = FargateComputeEnvironment(
            self,
            'ComputeEnvironment',
            vpc=vpc,
            vpc_subnets=SubnetSelection(
                subnet_type=SubnetType.PUBLIC,
            ),
            compute_environment_name='TestCDKComputeEnvironmentName',
            maxv_cpus=2
        )

        job_queue = JobQueue(
            self,
            'JobQueue',
            job_queue_name='TestCDKJobQueue',
        )

        job_queue.add_compute_environment(
            compute_environment,
            1
        )

        job_role = Role(
            self,
            'TestFargateBatchRole',
            assumed_by=ServicePrincipal(
                'ecs-tasks.amazonaws.com'
            )
        )

        sa_secret = SMSecret.from_secret_complete_arn(
            self,
            'SASecret',
            'arn:aws:secretsmanager:us-west-2:618537831167:secret:test/secret/json/blob-6axDxV',
        )

        container = EcsFargateContainerDefinition(
            self,
            'TestFargateBatchContainer',
            assign_public_ip=True,
            image=ContainerImage.from_asset(
                './docker',
                platform=Platform.LINUX_AMD64,
            ),
            memory=Size.mebibytes(2048),
            cpu=1,
            environment={
                'SOME_ENV': 'abc',
            },
            secrets={
                'SA_SECRET': Secret.from_secrets_manager(
                    secret=sa_secret,
                    field='json_str',
                )
            },
            logging=LogDriver.aws_logs(
                stream_prefix='testbatchjob',
                mode=AwsLogDriverMode.NON_BLOCKING,
                log_retention=RetentionDays.ONE_MONTH,
            )
        )

        job_definition = EcsJobDefinition(
            self,
            'TestBatchJobDefinition',
            container=container,
        )


        rule = Rule(
            self,
            'TestBatchJobRule',
            schedule=Schedule.cron(
                minute='0',
                hour='9',
                day='*',
                month='*',
                year='*'
            ),
        )

        target = BatchJob(
            job_queue_arn=job_queue.job_queue_arn,
            job_queue_scope=job_queue,
            job_definition_arn=job_definition.job_definition_arn,
            job_definition_scope=job_definition,
            job_name='TestScheduledBatchJob',
            retry_attempts=0,
        )

        rule.add_target(target)

        connection = Connection.from_event_bus_arn(
            self,
            'Connection',
            connection_arn='arn:aws:events:us-west-2:618537831167:connection/test-connection/91ea900a-3859-4515-8549-1aea492c9ab8',
            connection_secret_arn='arn:aws:secretsmanager:us-west-2:618537831167:secret:events!connection/test-connection/8e36f4d9-82f7-4eca-a48e-9d60e43a8994-GY4yUr',
        )

        endpoint = StringParameter.from_string_parameter_name(
            self,
            'SlackWebhookUrl',
            string_parameter_name='DEMO_EVENTS_SLACK_WEBHOOK_URL',
        )

        api_destination = ApiDestination(
            self,
            'BatchJobNotificationSlackChannel',
            connection=connection,
            endpoint=endpoint.string_value,
        )

        succeeded_transformed_event = RuleTargetInput.from_object(
            {
                'text': f':white_check_mark: *AnvilFileTransferSucceeded* | {job_queue.job_queue_arn}'
            }
        )

        failed_transformed_event = RuleTargetInput.from_object(
            {
                'text': f':x: *AnvilFileTransferFailed* | {job_queue.job_queue_arn}'
            }
        )

        succeeded_outcome_notification_rule = Rule(
            self,
            'NotifySlackBatchJobSucceeded',
            event_pattern=EventPattern(
                source=['aws.batch'],
                detail_type=['Batch Job State Change'],
                detail={
                    'status': ['SUCCEEDED'],
                    'jobQueue': [f'{job_queue.job_queue_arn}'],
                }
            ),
            targets=[
                TargetApiDestination(
                    api_destination=api_destination,
                    event=succeeded_transformed_event,
                )
            ]
        )

        failed_outcome_notification_rule = Rule(
            self,
            'NotifySlackBatchJobFailed',
            event_pattern=EventPattern(
                source=['aws.batch'],
                detail_type=['Batch Job State Change'],
                detail={
                    'status': ['FAILED'],
                    'jobQueue': [f'{job_queue.job_queue_arn}'],
                }
            ),
            targets=[
                TargetApiDestination(
                    api_destination=api_destination,
                    event=failed_transformed_event,
                )
            ]
        )


BatchWorkflowStack(
    app,
    'BatchWorkflowStack',
    env=US_WEST_2,
)


app.synth()
