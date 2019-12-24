
import boto3
from botocore.exceptions import ClientError
import os
import json
import logging
import sys
import avm_common

def lambda_handler(event, context):
    try:
        account_id = event["AccountId"]
        sns_topic = avm_common.get_param("sns_topic_arn")
        print(sns_topic)
        print(account_id)
        sub  = "ERROR: avm-ssm-validate"
        func = "avm-ssm-validate"
        lambda_handler_inner(event, context)
    except ClientError as e:
        body = f"Unexpected error : {e}"
        print(body)
        #(accountId, snsARN, function_name, subject, body):
        avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)
        raise e
    except Exception as e:
        body = f"Unexpected error : {e}"
        print(body)
        avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)
        raise e

def lambda_handler_inner(event, context):
    account_id = event["AccountId"]
    exec_id = event["execution_id"]

    session = avm_common.aws_session( session_name="target_account")
    client = session.client('ssm')

    response = client.get_automation_execution(AutomationExecutionId=exec_id)
    failed_steps = [f for f in response["AutomationExecution"]["StepExecutions"] if f["StepStatus"] == "Failed"]
    if len(failed_steps):
        body = str(failed_steps)
        sns_topic = avm_common.get_param("sns_topic_arn")
        sub = f"SSM automation with {exec_id} failed for account {account_id}"
        avm_common.send_pipeline_notification(account_id,sns_topic,response["AutomationExecution"]["DocumentName"], sub,body)
    
    return 200


if __name__ == "__main__":
    from optparse import OptionParser
    import pprint
    import json
    import sys

    parser = OptionParser()
    parser.add_option("-a", "--account_number", dest="account_number", help="AccountNUmber to test",default="694866286020")
    parser.add_option("-e", "--execution_id", dest="execution_id", help="execution_id to validate")
    pp = pprint.PrettyPrinter(indent=4)
    (options, args) = parser.parse_args(sys.argv)
    pp.pprint(options)
    event = { "AccountId": f"{options.account_number}", "execution_id": options.execution_id}
    lambda_handler(event,None)    
