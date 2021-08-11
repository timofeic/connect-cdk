import boto3
import os

connect = boto3.client('connect')
lex = boto3.client('lexv2-models')

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
    instance_id = os.environ['InstanceId']
    region = os.environ['Region']
    account = os.environ['Account']
    bot_id = os.environ['BotId']
    bot_alias_id = os.environ['BotAliasId']

    response = connect.associate_bot(
        InstanceId=instance_id,
        LexV2Bot={
            'AliasArn': 'arn:aws:lex:%s:%s:bot-alias/%s/%s' % (region, account, bot_id, bot_alias_id)
        }
    )

    physical_id = "ConnectAssociateBot"

    return { 'PhysicalResourceId': physical_id }

def on_update(event):
    physical_id = event["PhysicalResourceId"]
    props = event["ResourceProperties"]
    print("update resource %s with props %s" % (physical_id, props))
    # ...

def on_delete(event):
    physical_id = event["PhysicalResourceId"]
    print("delete resource %s" % physical_id)
    # ...
    return { 'PhysicalResourceId': physical_id }
