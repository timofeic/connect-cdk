import json
import boto3
import logging
import uuid
import random
import time
import os
from base64 import b64decode
from botocore.exceptions import ClientError

logger = logging.getLogger()
sns_client = boto3.client('sns')
ddb_idv = boto3.client('dynamodb')
ddb_users = boto3.resource('dynamodb')
user_table = ddb_users.Table(os.environ['USER_TABLE_NAME'])

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': {
              "contentType": "PlainText",
              "content": message
            },
        }
    }

    return response

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None

def get_one_time_code():
    #write onetime code to ddb - with this contact ID. as the primary key
    rand_uuid = str(uuid.uuid4())
    epoch = int(time.time())
    OTP = ''
    for _ in range(6):
        OTP += str(random.randint(0,9))
    var = ddb_idv.put_item(
        TableName=os.environ['OTP_TABLE_NAME'],
        Item={
            'uuid': {'S':str(rand_uuid)},
            'pin': {'S':str(OTP)},
            'timeStamp': {'N':str(epoch)}
            }
    )
    #return one time random 6 digit key
    return rand_uuid, OTP

def send_pin(phone_number, msg):
    #query user phone number from ddb table
    result = sns_client.publish(PhoneNumber=phone_number, Message=msg)
    return result


def get_user_details(user_id):
    #ID verification section - user_id and vcode
    try:
        response = user_table.query(
            ExpressionAttributeValues={
                ':user_id': user_id
            },
            IndexName = 'user_id-index',
            KeyConditionExpression='user_id = :user_id',
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        items = response['Items']
        if not items:
            return None
        else:
            email = try_ex(lambda: items[0]["email"])
            phone_num = try_ex(lambda: items[0]['PhoneNumber'])
            customerName = try_ex(lambda: items[0]['firstName'])

            return email, phone_num, customerName

def check_pin(pin, uuid):

    epoch = int(time.time())
    #queries DDB table for the OTP based on the uuid
    result = ddb_idv.get_item(
        TableName=os.environ['OTP_TABLE_NAME'],
        Key={'uuid': {'S':str(uuid)}}
    )
    if result['ResponseMetadata']['HTTPStatusCode'] == 200:
        if 'Item' in result.keys():
            correct_pin = result['Item']['pin']['S']
            timestamp = result['Item']['timeStamp']['N']
            valid = epoch - int(timestamp) < 60
            if not valid:
                print("expired")
            if pin == correct_pin and valid:
                return True
            else:
                return False
    else:
        logger.debug('dynamodb request error')
        return False

# function to perform IDV through verification code sent through email.
def identity_verification(user_id,vcode):
    #ID verification section - user_id and vcode
    try:
        response = user_table.query(
            ExpressionAttributeValues={
                ':user_id': user_id
            },
            IndexName = 'user_id-index',
            KeyConditionExpression='user_id = :user_id',
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        items = response['Items']
        if not items:
            return -1
        else:
            # print("Found user")
            # print(items)
            if str(vcode) == str(items[0]["vcode"]):
                return 1
            else:
                return 0

def meter_reading(intent_request):
    slots = intent_request['currentIntent']['slots']
    user_id = intent_request['currentIntent']['slots']['UserId']
    vcode = intent_request['currentIntent']['slots']['vcode']
    print (user_id,vcode)

    print(intent_request['sessionAttributes'])
    output_session_attributes = intent_request['sessionAttributes']
    authenticated = 0
    if output_session_attributes !={}:
        if "auth" in output_session_attributes:
            authenticated = output_session_attributes["auth"]

    if not user_id:
        return elicit_slot(
                        output_session_attributes,
                        'MeterReading',
                        slots,
                        'UserId',
                        {'contentType': 'PlainText', 'content': 'Thanks for submitting your meter read with us. Before we start, what is your account ID?'}
                        )
    elif not vcode:
        #alternatively, use OTP:
        customerinfo = get_user_details(user_id)
        #if not able to find user info with user_id provided
        if not customerinfo:
            return elicit_slot(
                        output_session_attributes,
                        'MeterReading',
                        slots,
                        'UserId',
                        {'contentType': 'PlainText', 'content': 'Sorry, your user id is incorrect, can you provide me again your user ID?'}
                        )

        else:
            email, phone_num, customerName = customerinfo
            if phone_num and customerName:
                rand_uuid, one_time_code = get_one_time_code()

                output_session_attributes['uuid'] = rand_uuid
                output_session_attributes['customer_phone'] = phone_num
                output_session_attributes['customer_name'] = customerName
                slots['Phone'] = phone_num
                msg = 'Hi {}! This is your one time code: '.format(customerName) + one_time_code
                result = send_pin(phone_num, msg)
                output_session_attributes['count'] = 1
                return elicit_slot(
                            output_session_attributes,
                            'MeterReading',
                            slots,
                            'vcode',
                            {'contentType': 'PlainText', 'content': 'Thank you! We have just sent you a 6 digits verification code to your mobile. Do you mind providing it back to me?'}
                            )
            else:
                return close(output_session_attributes, 'Fulfilled', 'Sorry, we are having problem retrieving your information, please contact customer support.')

    elif authenticated ==0:
        #auth = identity_verification(user_id,vcode)
        uuid = try_ex(lambda: output_session_attributes['uuid'])
        # count is number of OPT sent already
        count = int(try_ex(lambda: output_session_attributes['count']))
        auth = check_pin(vcode, uuid)
        print (auth)
        if auth:
            output_session_attributes["auth"] = auth
            return delegate(output_session_attributes, intent_request['currentIntent']['slots'])
        else:
            if count < 2:
                rand_uuid, one_time_code = get_one_time_code()
                output_session_attributes['uuid'] = rand_uuid
                phone_num = slots['Phone']
                customerName = output_session_attributes['customer_name']
                msg = 'Hi {}! This is your one time code: '.format(customerName) + one_time_code
                result = send_pin(phone_num, msg)
                output_session_attributes['count'] = count+1

                return elicit_slot(
                            output_session_attributes,
                            'MeterReading',
                            slots,
                            'vcode',
                            {'contentType': 'PlainText', 'content': 'Sorry, your verification code is incorrect. Let us try again. We have just sent you another 6 digits verification code to your mobile. Do you mind providing the latest one back to me?'}
                            )
            else:
                return close(output_session_attributes, 'Fulfilled', 'Sorry, your verification code is still incorrect, please contact customer support.')
    # authenticated ==1 and we can delegate elicit slot to Lex
    else:
        return delegate(output_session_attributes, intent_request['currentIntent']['slots'])


def water_leak(intent_request):
    slots = intent_request['currentIntent']['slots']
    user_id = intent_request['currentIntent']['slots']['UserId']
    vcode = intent_request['currentIntent']['slots']['vcode']
    print (user_id,vcode)

    print(intent_request['sessionAttributes'])
    output_session_attributes = intent_request['sessionAttributes']
    authenticated = 0
    if output_session_attributes !={}:
        if "auth" in output_session_attributes:
            authenticated = output_session_attributes["auth"]

    if not user_id:
        return elicit_slot(
                        output_session_attributes,
                        'WaterLeak',
                        slots,
                        'UserId',
                        {'contentType': 'PlainText', 'content': 'Before we start, what is your account number? This should be 7 digits'}
                        )
    elif not vcode:
        #alternatively, use OTP:
        customerinfo = get_user_details(user_id)
        #if not able to find user info with user_id provided
        if not customerinfo:
            return elicit_slot(
                        output_session_attributes,
                        'WaterLeak',
                        slots,
                        'UserId',
                        {'contentType': 'PlainText', 'content': 'Sorry, your account number is incorrect, can you provide your account number again?'}
                        )

        else:
            email, phone_num, customerName = customerinfo
            if phone_num and customerName:
                rand_uuid, one_time_code = get_one_time_code()

                output_session_attributes['uuid'] = rand_uuid
                output_session_attributes['customer_phone'] = phone_num
                output_session_attributes['customer_name'] = customerName
                slots['Phone'] = phone_num
                msg = 'Hi {}! This is your one time code: '.format(customerName) + one_time_code
                result = send_pin(phone_num, msg)
                output_session_attributes['count'] = 1
                return elicit_slot(
                            output_session_attributes,
                            'WaterLeak',
                            slots,
                            'vcode',
                            {'contentType': 'PlainText', 'content': 'Thank you! We have just sent you a 6 digits verification code to your mobile. Do you mind providing it back to me?'}
                            )
            else:
                return close(output_session_attributes, 'Fulfilled', 'Sorry, we are having problem retrieving your information, please contact customer support.')

    elif authenticated ==0:
        #auth = identity_verification(user_id,vcode)
        uuid = try_ex(lambda: output_session_attributes['uuid'])
        # count is number of OPT sent already
        count = int(try_ex(lambda: output_session_attributes['count']))
        auth = check_pin(vcode, uuid)
        if auth:
            output_session_attributes["auth"] = auth
            return delegate(output_session_attributes, intent_request['currentIntent']['slots'])
        else:
            if count < 2:
                rand_uuid, one_time_code = get_one_time_code()
                output_session_attributes['uuid'] = rand_uuid
                phone_num = slots['Phone']
                customerName = output_session_attributes['customer_name']
                msg = 'Hi {}! This is your one time code: '.format(customerName) + one_time_code
                result = send_pin(phone_num, msg)
                output_session_attributes['count'] = count+1

                return elicit_slot(
                            output_session_attributes,
                            'WaterLeak',
                            slots,
                            'vcode',
                            {'contentType': 'PlainText', 'content': 'Sorry, your verification code is incorrect. Let us try again. We have just sent you another 6 digits verification code to your mobile. Do you mind providing the latest one back to me?'}
                            )
            else:
                return close(output_session_attributes, 'Fulfilled', 'Sorry, your verification code is still incorrect, please contact customer support.')
    # authenticated ==1 and we can delegate elicit slot to Lex
    else:
        return delegate(output_session_attributes, intent_request['currentIntent']['slots'])

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'MeterReading':
        return meter_reading(intent_request)
    elif intent_name == 'WaterLeak':
        return water_leak(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')


def lambda_handler(event, context):
    print(event)
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
