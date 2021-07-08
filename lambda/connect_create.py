from __future__ import print_function
from crhelper import CfnResource
import boto3
import logging, os

logger = logging.getLogger(__name__)
# Initialise the helper, all inputs are optional, this example shows the defaults
helper = CfnResource(
        json_logging=False, 
        log_level='INFO', 
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

connect_alias = os.environ['InstanceAlias']

@helper.create
def create(event, context):
    logger.debug("[Event] %s", event)

    response = connect.create_instance(
        IdentityManagementType='CONNECT_MANAGED',
        InstanceAlias=connect_alias,
        InboundCallsEnabled=True,
        OutboundCallsEnabled=True
    )
    logger.info('[Response] %s', response)
    helper.Data.update({"Arn": response["Arn"]})
    logger.info('[Helper] %s', helper.Data)


@helper.update
def update(event, context):
    logger.info("Resource Updated")
    # If the update resulted in a new resource being created, return an id for the new resource. 
    # CloudFormation will send a delete event with the old id when stack update completes
    return "NewPhysicalResourceId"


@helper.delete
def delete(event, context):
    
    logger.debug("[Event] %s", event)
    response = connect.delete_instance(
        InstanceId=connect_alias
    )
    logger.info("Resource Deleted")


def handler(event, context):
    helper(event, context)