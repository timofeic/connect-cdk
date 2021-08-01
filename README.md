
# CDK Python example to create an Amazon Connect instance

## Description
Create an Amazon Connect instance using the AWS CDK.
Amazon Connect currently does not have CloudFormation support, so we need to use a Custom Resource in order to create it using the SDK.

## Prerequisites
1. An AWS account
1. Install the AWS CDK
1. An AWS User to run the cdk deploy

## Deployment

1. Clone the repo
1. cd into the repo directory
1. `source .venv/bin/activate`
1. `pip install -r requirements.txt`
1. (If not already done) bootstrap your environment using ``` $ cdk bootstrap ```
1. Modify the instance_alias in cdk.json
1. `cdk deploy`