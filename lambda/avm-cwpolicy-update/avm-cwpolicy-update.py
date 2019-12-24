import os
import boto3
from botocore.exceptions import ClientError
import time
import json
import sys
import logging
import json
import sys
import csv
import avm_common



def update_cw_destination_policy(session,event):

    regions = ["us-east-2","us-east-1"]
    
    # get log-destinations
    account_id = event["AccountId"]
    print(event)
    for r in regions:
        client = session.client("logs",region_name = r)
        resp = client.describe_destinations()
        for d in resp["destinations"]:
            if "vpc_flowlogs" in d["destinationName"]:
                #print(json.dumps(d))
                if "accessPolicy" not in d.keys():
                    resource = d["arn"]
                    access_policy = f"""
                    {{
                    "Version": "2012-10-17",
                    "Statement": [
                        {{
                        "Sid": "PublishSubscriptionFilterToFirehose",
                        "Effect": "Allow",
                        "Principal": {{
                            "AWS": [
                            "{account_id}"
                            ]
                        }},
                        "Action": [
                            "logs:PutSubscriptionFilter"
                        ],
                        "Resource": "{resource}"
                        }}
                    ]
                    }}
                    """
                    print(access_policy)
                    response = client.put_destination_policy(destinationName=d["destinationName"],accessPolicy=access_policy)
                    #print(json.dumps(response))
                else:
                    access_policy = json.loads(d["accessPolicy"])
                    
                    stmt = access_policy["Statement"][0]
                    accounts = stmt["Principal"]["AWS"]
                    if str(account_id) not in accounts:
                        accounts.append(str(account_id))
                        access_policy["Statement"][0]["Principal"]["AWS"] = accounts
                        access_policy["Statement"][0]["Resource"] = d["arn"]
                        print(json.dumps(access_policy))
                        response = client.put_destination_policy(destinationName=d["destinationName"],accessPolicy=json.dumps(access_policy))
                        #print(json.dumps(response))


def lambda_handler(event, context):
    try:
        account_id = event["AccountId"]
        sns_topic = avm_common.get_param("sns_topic_arn")
        print(sns_topic)
        print(account_id)
        sub  = "ERROR: accountpipeline CW destination policy update"
        func = "accountpipeline-cw-destination-policy-update"
        lambda_handler_inner(event, context)
    except ClientError as e:
        body = f"Unexpected error : {e}"
        print(body)
        #(accountId, snsARN, function_name, subject, body):
        avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)
    except Exception as e:
        body = f"Unexpected error : {e}"
        print(body)
        avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)

def lambda_handler_inner(event, context):
    core_logging = avm_common.get_param("core_logging_account")
    master_role =  avm_common.get_param("tlz_admin_role")

    ROLE_ARN_LOGGING=f"arn:aws:iam::{core_logging}:role/{master_role}"
    session_assumed = avm_common.aws_session(role=ROLE_ARN_LOGGING, session_name='logging-services')
    update_cw_destination_policy(session_assumed,event)


if __name__ == "__main__":
    from optparse import OptionParser
    import pprint
    import json
    import sys

    parser = OptionParser()
    parser.add_option("-a", "--account_number", dest="account_number", help="AccountNUmber to test")
    pp = pprint.PrettyPrinter(indent=4)
    (options, args) = parser.parse_args(sys.argv)
    pp.pprint(options)
    event = { "AccountId": f"{options.account_number}"}
    lambda_handler(event,None)