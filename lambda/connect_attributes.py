import boto3
import os
import time

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
    instance_id = os.environ['InstanceId']
    key_arn = os.environ['KeyArn']
    bucket_name = os.environ['BucketName']
    recording_prefix = os.environ['RecordingPrefix']
    transcript_prefix = os.environ['TranscriptPrefix']

    list_hours = connect.list_hours_of_operations(
        InstanceId=instance_id,
    )
    print(list_hours)
    # Assume this is a new instance and only has the default hours of operations.
    # There is no method to create a new hours of operation.
    # We need this ID later when we create a queue.
    basic_hours_id = list_hours["HoursOfOperationSummaryList"][0]["Id"]
    
    # New queue so we can reference the Id later in our contact flow.
    create_queue = connect.create_queue(
        InstanceId=instance_id,
        Name="DemoQueue",
        HoursOfOperationId=basic_hours_id
    )

    demo_queue_id = create_queue["QueueId"]

    create_contact_flow = connect.create_contact_flow(
        InstanceId=instance_id,
        Name='1 DemoContactFlow',
        Type='CONTACT_FLOW',
        Content='{"Version":"2019-10-30","StartAction":"4b484e2a-8131-4b3d-bf20-7b8782d6e6fc","Metadata":{"entryPointPosition":{"x":20,"y":20},"snapToGrid":false,"ActionMetadata":{"f21eaca2-7fdd-48fb-8488-9ae4bae1ed3e":{"position":{"x":447,"y":147}},"4b484e2a-8131-4b3d-bf20-7b8782d6e6fc":{"position":{"x":194,"y":53},"useDynamic":false}}},"Actions":[{"Identifier":"f21eaca2-7fdd-48fb-8488-9ae4bae1ed3e","Type":"DisconnectParticipant","Parameters":{},"Transitions":{}},{"Identifier":"4b484e2a-8131-4b3d-bf20-7b8782d6e6fc","Parameters":{"Text":"Hello World"},"Transitions":{"NextAction":"f21eaca2-7fdd-48fb-8488-9ae4bae1ed3e","Errors":[],"Conditions":[]},"Type":"MessageParticipant"}]}'
    )

    contact_flow_id = create_contact_flow["ContactFlowId"]

    recordings_s3_storage = s3_storage_config(
        instance_id,
        'CALL_RECORDINGS',
        bucket_name,
        recording_prefix,
        key_arn
    )

    transcripts_s3_storage = s3_storage_config(
        instance_id,
        'CHAT_TRANSCRIPTS',
        bucket_name,
        transcript_prefix,
        key_arn
    )

    physical_id = "ConnectInstanceAttributes"

    return { 'PhysicalResourceId': physical_id,
        'Data': {
            'BasicHoursId': basic_hours_id,
            'DemoQueueId': demo_queue_id,
            'ContactFlowId': contact_flow_id,
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
    # ...
    return { 'PhysicalResourceId': physical_id }

def s3_storage_config(instance_id, resource_type, bucket_name, bucket_prefix, key_arn):
    storage_config = connect.associate_instance_storage_config(
        InstanceId=instance_id,
        ResourceType=resource_type,
        StorageConfig={
            'StorageType': 'S3',
            'S3Config': {
                'BucketName': bucket_name,
                'BucketPrefix': bucket_prefix,
                'EncryptionConfig': {
                    'EncryptionType': 'KMS',
                    'KeyId': key_arn
                }
            }
        }
    )