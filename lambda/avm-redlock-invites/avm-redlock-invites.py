import requests
import json
import sys
import avm_common

# Use this code snippet in your app.
# If you need more information about configurations or implementing the sample code, visit the AWS docs:
# https://aws.amazon.com/developers/getting-started/python/

import boto3
import base64
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    try:
        account_id = event["AccountId"]
        sns_topic = avm_common.get_param("sns_topic_arn")
        sub  = "ERROR: redlock addaccount"
        func = "avm-3rdparty-redlock-addaccount"
        lambda_handler_inner(event, context)
    except ClientError as e:
        body = f"Unexpected error : {e}"
        avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)
        raise e
    except Exception as e:
        body = f"Unexpected error : {e}"
        avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)
        raise e



def lambda_handler_inner(event, context):
    account_id = event["AccountId"]
    add_account_to_redlock(account_id)

def extract_externalid(account_id):
    sts_client = boto3.client('sts')
    master_role =  avm_common.get_param("tlz_admin_role")
    response=sts_client.assume_role( RoleArn=f"arn:aws:iam::{account_id}:role/{master_role}", RoleSessionName="AssumeRoleSession1")
    iam_policies = boto3.resource('iam',aws_access_key_id=response['Credentials']['AccessKeyId'], aws_secret_access_key=response['Credentials']['SecretAccessKey'],aws_session_token=response['Credentials']['SessionToken'])
    externalID = ""
    for role in iam_policies.roles.all():
        if role.name == "tlz_redlock_read_only":
            externalID = role.assume_role_policy_document['Statement'][0]['Condition']['StringEquals']['sts:ExternalId']
    return externalID

def add_account_to_redlock(account_id):
    redlock = avm_common.get_secret("redlock")
    result = avm_common.get_account_details(account_id)

    account_alias = f"{result['org_details']['name']}"
    if result['request_details']:
        if "subAccountType" in result['request_details'].keys():
            account_alias += f"-{result['request_details']['subAccountType']}"
    body = {"username" : redlock["user"],"password" : redlock["password"] }
    header = {'Content-Type': 'application/json'}

    r = requests.post(f'{redlock["rest_api_url"]}/login', headers=header, data=json.dumps(body))
    if r.status_code == requests.codes.ok:
        resp = json.loads(r.text)
        token = resp["token"]
        account_payload = {
        "accountId": account_id,
        "enabled": True,
        "externalId": extract_externalid(account_id),
        "groupIds": [ redlock["group_id"] ],
        "name": f"{account_alias}-{account_id}",
        "roleArn": f"arn:aws:iam::{account_id}:role/tlz_redlock_read_only"
        }
        headers = {"x-redlock-auth" : token, "Content-Type" : "application/json"}
        addaccount_r = requests.post(f'{redlock["rest_api_url"]}/cloud/aws', headers=headers, data=json.dumps(account_payload))
    else:
        body  = f"{r.json()}"
        sub = "ERROR: Unable to add account {account_id} to redlock"
        func = "redlock-addaccount"
        sns_topic = avm_common.get_param("sns_topic_arn")
        avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)

if __name__ == "__main__":
    from optparse import OptionParser
    import pprint
    import json
    import sys

    parser = OptionParser()
    parser.add_option("-a", "--account_number", dest="account_number", help="AccountNUmber to test")
    pp = pprint.PrettyPrinter(indent=4)
    (options, args) = parser.parse_args(sys.argv)
    event = { "AccountId": f"{options.account_number}"}
    lambda_handler(event,None)
