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

from aws_cdk.aws_events_targets import BatchJob

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


BatchWorkflowStack(
    app,
    'BatchWorkflowStack',
    env=US_WEST_2,
)


app.synth()
