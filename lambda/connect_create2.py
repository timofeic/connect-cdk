import boto3
import os

connect = boto3.client('connect')

def on_event(event, context):
    print(event)
    request_type = event['RequestType']
    if request_type == 'Create': return on_create(event)
    if request_type == 'Update': return on_update(event)
    if request_type == 'Delete': return on_delete(event)
    raise Exception("Invalid request type: %s" % request_type)

def on_create(event):
    props = event["ResourceProperties"]
    print("create new resource with props %s" % props)
    connect_alias = os.environ['InstanceAlias']

    response = connect.create_instance(
        IdentityManagementType='CONNECT_MANAGED',
        InstanceAlias=connect_alias,
        InboundCallsEnabled=True,
        OutboundCallsEnabled=True
    )
    physical_id = "ConnectInstance-ABCD"

    return { 'PhysicalResourceId': physical_id,
        'Data': {
            'InstanceId': response["Id"],
            'InstanceArn': response["Arn"]
        }
     }

def on_update(event):
    physical_id = event["PhysicalResourceId"]
    props = event["ResourceProperties"]
    print("update resource %s with props %s" % (physical_id, props))
    # ...

def on_delete(event):
    physical_id = event["PhysicalResourceId"]
    print("delete resource %s" % physical_id)
    connect_alias = os.environ['InstanceAlias']
    
    response = connect.list_instances()
    for i in response["InstanceSummaryList"]:
        if i['InstanceStatus'] == 'ACTIVE':
            if i["InstanceAlias"] == connect_alias:
                print("Deleting Instance Id %s" % i["Id"])
                delete_instance = connect.delete_instance(
                    InstanceId=i["Id"]
                )

def is_complete(event, context):
    physical_id = event["PhysicalResourceId"]
    request_type = event["RequestType"]
    print("Event object %s" % event)

    if request_type == 'Create':    
        # We want to wait for the instance to be active before marking the resource as complete. 
        # Otherwise subsequent calls will fail.
        response = connect.describe_instance(
            InstanceId=event['Data']['InstanceId']
        )
        if response["Instance"]["InstanceStatus"] == "ACTIVE":
            print("Is Ready!!!")
            is_ready = True
        else:
            is_ready = False

    if request_type == 'Update':
        is_ready = True
    if request_type == 'Delete':
        connect_alias = os.environ['InstanceAlias']

        response = connect.list_instances()
        for i in response["InstanceSummaryList"]:
            if i["InstanceAlias"] == connect_alias:
                is_ready = False
            else:
                is_ready = True

    return { 'IsComplete': is_ready }