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
    bot_id = os.environ['BotId']
    
    bot_locale = lex.create_bot_locale(
        botId=bot_id,
        botVersion='DRAFT', # The version of the bot to create the locale for. This can only be the draft version of the bot.
        localeId='en_GB', #https://docs.aws.amazon.com/lexv2/latest/dg/how-languages.html
        description='GB English locale for the DUE Lex bot',
        nluIntentConfidenceThreshold=0.40,
        voiceSettings={
            'voiceId': 'Amy'
        }
    )

    return { 'PhysicalResourceId': 'LexBotAttr-DUE' }

def on_update(event):
    physical_id = event["PhysicalResourceId"]
    props = event["ResourceProperties"]
    print("update resource %s with props %s" % (physical_id, props))
    # ...

def on_delete(event):
    physical_id = event["PhysicalResourceId"]
    print("delete resource %s" % physical_id)
    
    return { 'PhysicalResourceId': physical_id }







