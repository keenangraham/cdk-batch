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

from aws_cdk.aws_ecr_assets import Platform

from aws_cdk.aws_batch import FargateComputeEnvironment
from aws_cdk.aws_batch import JobQueue
from aws_cdk.aws_batch import EcsFargateContainerDefinition
from aws_cdk.aws_batch import EcsJobDefinition

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
            maxv_cpus=2,
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

        container = EcsFargateContainerDefinition(
            self,
            'TestFargateBatchContainer',
            image=ContainerImage.from_asset(
                './docker',
                platform=Platform.LINUX_AMD64,
            ),
            memory=Size.mebibytes(2048),
            cpu=1,
            environment={
                'SOME_ENV': 'abc',
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


BatchWorkflowStack(
    app,
    'BatchWorkflowStack',
    env=US_WEST_2,
)


app.synth()
