import boto3
import os

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
    role_arn = os.environ['RoleArn']
    
    lex_bot = lex.create_bot(
        botName='DUEBot',
        description='Digital User Engagement Bot',
        roleArn=role_arn,
        dataPrivacy={
            'childDirected': False
        },
        idleSessionTTLInSeconds=300,
    )

    return { 'PhysicalResourceId': 'LexBot-DUE',
        'Data': {
            'BotId': lex_bot["botId"]
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
    
    list_bots = lex.list_bots()
    for i in list_bots["botSummaries"]:
        if i['botName'] == 'DUEBot':
            print("Deleting Lex Bot Id %s" % i['botId'])
            lex_bot = lex.delete_bot(
                botId=i['botId']
            )
    
    return { 'PhysicalResourceId': physical_id }

def is_complete(event, context):
    physical_id = event["PhysicalResourceId"]
    request_type = event["RequestType"]
    print("Event object %s" % event)

    if request_type == 'Create':    
        # We want to wait for the instance to be active before marking the resource as complete. 
        # Otherwise subsequent calls will fail.
        list_bots = lex.list_bots()
        for i in list_bots["botSummaries"]:
            if i['botName'] == 'DUEBot':
                if  i['botStatus'] == "Available":
                    return { 'IsComplete': True }
                else:
                    is_ready = False
        return { 'IsComplete': False }
    if request_type == 'Update':
        is_ready = True
    if request_type == 'Delete':
        is_ready = True

    return { 'IsComplete': is_ready }