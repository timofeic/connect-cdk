from __future__ import print_function
from crhelper import CfnResource
import boto3
import logging

logger = logging.getLogger(__name__)
# Initialise the helper, all inputs are optional, this example shows the defaults
helper = CfnResource(
        json_logging=False, 
        log_level='DEBUG', 
        boto_level='CRITICAL', 
        sleep_on_delete=120, 
        ssl_verify=None
        )

try:
    ## Init code goes here
    connect = boto3.client('connect')
    pass
except Exception as e:
    helper.init_failure(e)


@helper.create
def create(event, context):
    logger.info("Resource Created")

    response = connect.create_instance(
        IdentityManagementType='CONNECT_MANAGED',
        InstanceAlias='cheungt-test-lon',
        InboundCallsEnabled=True,
        OutboundCallsEnabled=True
    )
    logger.info('Response: %s', response)

    connect.create_user(
        Username='admin',
        Password='Passw0rd',
        IdentityInfo={
            'FirstName': 'Admin',
            'LastName': 'istrator',
            'Email': 'admin@example.com'
        },
        PhoneConfig={
            'PhoneType': 'SOFT_PHONE',
            'AutoAccept': False,
            'AfterContactWorkTimeLimit': 0,
        },
        SecurityProfileIds=[
            'Admin',
        ],
        RoutingProfileId='Basic Routing Profile',
        InstanceId=response["Id"],
    )

    return response["Id"]


@helper.update
def update(event, context):
    logger.info("Resource Updated")
    # If the update resulted in a new resource being created, return an id for the new resource. 
    # CloudFormation will send a delete event with the old id when stack update completes
    return "NewPhysicalResourceId"


@helper.delete
def delete(event, context):
    logger.info("Resource Deleted")
    
    response = connect.delete_instance(
        InstanceId='cheungt-test-lon'
    )


def handler(event, context):
    helper(event, context)