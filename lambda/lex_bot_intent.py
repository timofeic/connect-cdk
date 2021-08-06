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
    locale_id = os.environ['LocaleId']

    meter_reading_intent = lex.create_intent(
        intentName='MeterReading',
        sampleUtterances=[
            { 'utterance': 'submit a meter reading' },
            { 'utterance': 'enter reading' },
            { 'utterance': 'enter reading' },
            { 'utterance': 'reading my meter' },
            { 'utterance': 'submit a {UtilityType} reading' },
        ],
        botId=bot_id,
        botVersion='DRAFT',
        localeId=locale_id
    )

    user_id_slot = slot(
        'UserId', 
        'AMAZON.Number',
        'What is your account ID?',
        meter_reading_intent["intentId"],
        bot_id,
        locale_id
    )

    phone_slot = slot(
        'Phone', 
        'AMAZON.PhoneNumber', 
        'Please enter in your phone number', 
        meter_reading_intent["intentId"],
        bot_id,
        locale_id
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

def slot(slot_name, slot_type_id, message, intent_id, bot_id, locale_id):
    return lex.create_slot(
        slotName=slot_name,
        slotTypeId=slot_type_id,
        valueElicitationSetting={
            'slotConstraint': 'Required',
            'promptSpecification': {
                'messageGroups': [
                    {
                        'message': {
                            'plainTextMessage': {
                                'value': message
                            }
                        }
                    }
                ],
                'maxRetries': 3
            }
        },
        botId=bot_id,
        botVersion='DRAFT',
        localeId=locale_id,        
        intentId=intent_id
    )





