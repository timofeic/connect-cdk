import boto3
import os
import time

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

    utility_slot_type = lex.create_slot_type(
        slotTypeName='UtilityType',
        description='Gas or Electricity utility type',
        slotTypeValues=[
            {
                'sampleValue': { 'value': 'gas' },
            },
            {
                'sampleValue': { 'value': 'electricity' },
            }
        ],
        valueSelectionSetting={
            'resolutionStrategy': 'OriginalValue'
        },
        botId=bot_id,
        botVersion='DRAFT',
        localeId=locale_id
    )

    meter_reading_intent = lex.create_intent(
        intentName='MeterReading',
        sampleUtterances=[
            { 'utterance': 'submit a meter reading' },
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

    reading_slot = slot(
        'Reading', 
        'AMAZON.PhoneNumber', 
        'What is the meter reading? This should be 6 digits, including any zeros. Ignore the number in red, plus any after a decimal point.', 
        meter_reading_intent["intentId"],
        bot_id,
        locale_id
    )

    vcode_slot = slot(
        'vcode', 
        'AMAZON.PhoneNumber', 
        'What is your one time verification number?', 
        meter_reading_intent["intentId"],
        bot_id,
        locale_id
    )

    utility_slot = slot(
        'UtilityType', 
        utility_slot_type["slotTypeId"], 
        'Is this for a Gas or Electricity reading?', 
        meter_reading_intent["intentId"],
        bot_id,
        locale_id
    )

    build = lex.build_bot_locale(
        botId=bot_id,
        botVersion='DRAFT',
        localeId=locale_id
    )

    version = lex.create_bot_version(
        botId=bot_id,
        botVersionLocaleSpecification={
            'en_GB': {
                'sourceBotVersion': 'DRAFT'
            }
        }
    )
    time.sleep(3)

    while True:
        check_bot_version = lex.describe_bot_version(
            botId=bot_id,
            botVersion=version["botVersion"]
        )
        if check_bot_version["botStatus"] == "Available":
            break
        time.sleep(1)

    alias = lex.create_bot_alias(
        botId=bot_id,
        botAliasName='PROD',
        botVersion=version["botVersion"]
    )

    return { 'PhysicalResourceId': 'LexBotAttr-DUE',
        'Data': {
            'BotAlias': 'PROD',
            'BotAliasId': alias["botAliasId"]
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
