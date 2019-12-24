#!/usr/bin/env python3

###
# Performs a plan and apply on a workspace in Terraform Enterprise
###

import json
import requests
import time
import sys
import boto3
import base64
from botocore.exceptions import ClientError
import avm_common
from botocore.exceptions import ClientError


org = avm_common.get_param("tfe_org_name")
tfe_api = avm_common.get_param("tfe_api_url")


def get_workspace(headers,workspace_name):
    #workspace_name = "baseline-tv-demo-app1-dev"
    workspace_id = None
    tfe_url = f'{tfe_api}/organizations/{org}/workspaces/{workspace_name}'
    r = requests.get(tfe_url, headers=headers)
    data = r.json()
    if "data" in data.keys():
        workspace_id = data["data"]["id"]
    else:
        print(f"No workspace found : {tfe_url}")
    return workspace_id

def create_run( headers,payload ):
    tfe_url = f'{tfe_api}/runs'
    run_id = None
    print(tfe_url)
    print(json.dumps(headers))
    r = requests.post(tfe_url, headers=headers, json=payload)
    print(json.dumps(payload))
    print(r)
    data = r.json()
    #print(json.dumps(data))
    if "data" in data.keys():
        run_id = data["data"]["id"]
    return run_id

def get_run_status(headers, run_id ):
    tfe_url = f'{tfe_api}/runs/{run_id}'
    r = requests.get(tfe_url, headers=headers)
    data = r.json()
    #print(json.dumps(data))
    run_status = data["data"]["attributes"]["status"]
    return run_status

def apply_run( headers, run_id ):
    tfe_url = f'{tfe_api}/runs/{run_id}/actions/apply'
    r = requests.post(tfe_url, headers=headers)

def create_json( workspace_id ):
    payload_json = """
    {
      "data":{
        "attributes":{
          "is-destroy":false,
          "message": "Plan initiated by TLZ-AVM"
        },
        "type":"runs",
        "relationships":{
          "workspace":{
            "data":{
              "type": "workspaces",
              "id": "%s"
            }
          }
        }
      }
    }
    """ % workspace_id
    payload = json.loads(payload_json)
    return payload

def get_workspace_name(account_id):
    account_info = avm_common.get_account_details(account_id)
    details = account_info["org_details"]
    #print(details)

    baseline_details = json.loads(details["baseline_details"])
    ws_name = baseline_details["tfe_workspace"]
    return ws_name

def lambda_handler(event, context):
    try:
        account_id = event["AccountId"]
        sns_topic = avm_common.get_param("sns_topic_arn")
        print(sns_topic)
        print(account_id)
        sub  = "ERROR: tfe Createbaseline"
        func = "avm-tfe-createbaseline"

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
    print(event)
    account_id = event["AccountId"]
    # Retrieve secrets from AWS Secrets Manager
    tfe_key = avm_common.get_secret("terraform")

    headers = {
        'Authorization': "Bearer " + tfe_key['terraform'],
        'Content-Type': "application/vnd.api+json",
    }

    #print(token)
    # Get the workspace ID using the provided workspace name
    workspace_name = get_workspace_name(account_id)
    print(workspace_name)
    workspace_id = get_workspace(headers,workspace_name)
    print(workspace_id)
    # Serialize the JSON payload with the workspace ID
    payload = create_json( workspace_id )
    #print(payload)
    # Trigger a terraform plan
    run_id = create_run( headers, payload )
    print(f"Run id : {run_id}") 
    retry_count = 6
    sleep_between_retry_attempts = 30
 
    # Check run for readiness and apply if so
    for i in range(retry_count):
        run_status = get_run_status(headers, run_id )
        print(f"Run status [{i}] : {run_status}")
        if run_status == 'planned':
            apply_run( headers,run_id )
            break
        elif run_status == 'errored':
            print("The changes have failed")
            raise Exception(f'TFE plan failed for workspace: {workspace_name}')
            break
        elif run_status == 'planned_and_finished':
            print("It appears that no changes were required")
            return 200


        time.sleep(sleep_between_retry_attempts)

    # Allow some time for the apply to finish then verify final state of run
    for i in range(retry_count):
        run_status = get_run_status( headers,run_id )
        print(f"Attempt {i} : {run_status}")
        if run_status == 'applied':
            print("Changes successfully applied")
            return 200
        elif run_status == 'planned_and_finished':
            print("It appears that no changes were required")
            return 200
        elif run_status == 'errored':
            print("The changes have failed")
            raise Exception(f'TFE apply failed for workspace: {workspace_name}')
            #return -1
        elif run_status == 'planned':
            raise Exception(f'TFE plan failed for workspace: {workspace_name}')
            #return -1
        time.sleep(sleep_between_retry_attempts)
    print("The changes are taking too long to execute and will require manual review")

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