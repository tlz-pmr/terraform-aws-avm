#!/usr/bin/env python3

# Using arn:aws:iam::508542367771:user/terraform-test
# old-common-shared-services
import boto3
import json
import base64
import requests
import sys
import json
import avm_common
import os
from botocore.exceptions import ClientError

#aws_profile_name='default'
aws_region_name=os.getenv('AWS_REGION')

#session = boto3.session.Session(profile_name=aws_profile_name,region_name=aws_region_name)

DDB_TABLE = 'OrgDetails'
org = avm_common.get_param("tfe_org_name")
tfe_api = avm_common.get_param("tfe_api_url")

class tlzKeyRotator:
    """Class that manages access to Keyrotations resources"""

    _account = None
    _session = None
    _iam = None
    _ddb_table = None
    _secrets = None

    def __init__(self, account):
        self._account = account
        master_role = avm_common.get_param("tlz_admin_role")
        self._session = avm_common.aws_session(role=f"arn:aws:iam::{account}:role/{master_role}", session_name='target-account')
        self._iam = self._session.client('iam')
        session = boto3.session.Session()
        dynamodb = session.resource('dynamodb',region_name=aws_region_name)
        self._ddb_table = dynamodb.Table(DDB_TABLE)



    def update_ddb_result(self,AccountId, tfe_workspaces):
        response = self._ddb_table.update_item(
            TableName=DDB_TABLE,
            Key={"id": AccountId},
            ExpressionAttributeValues={
                ":sr": tfe_workspaces,
            },
            UpdateExpression="SET tfe_workspaces = tfe_workspaces + :sr",
            ReturnValues="UPDATED_NEW"
        )
        print(f"update_item: {response['ResponseMetadata']}", flush=True)


    def get_access_keys(self,user_name):
        response = self._iam.list_access_keys(UserName=user_name)
        # Move active key to inactive and delete inactive key
        if len(response["AccessKeyMetadata"]) > 0:
            # Check to see if there are two currently active keys
            if len(response["AccessKeyMetadata"]) == 2:
                if response["AccessKeyMetadata"][0]["Status"] == "Active" \
                and response["AccessKeyMetadata"][1]["Status"] == "Active":
                    self.notify("Multiple active keys found, exiting without changes!")
            for key in response["AccessKeyMetadata"]:
                if key["Status"] == "Inactive":
                    self.delete_inactive_key(key["AccessKeyId"], user_name)
                elif key["Status"] == "Active":
                    self.make_key_inactive(key["AccessKeyId"], user_name)

        # Create the new key
        return self.createKey(user_name)


    def delete_inactive_key(self,key, user_name):
        print("Delete: " + key)
        response = self._iam.delete_access_key(UserName=user_name,AccessKeyId=key)


    def make_key_inactive(self,key, user_name):
        print("Inactivate: " + key)
        response = self._iam.update_access_key(UserName=user_name,AccessKeyId=key,Status='Inactive')


    def createKey(self,user_name):
        keypair = {}
        response = self._iam.create_access_key(UserName=user_name)
        keypair["AccessKeyId"] = response["AccessKey"]["AccessKeyId"]
        keypair["SecretAccessKey"] = response["AccessKey"]["SecretAccessKey"]
        return keypair


    def update_tfe_workspaces(self,keys, secret_name, account_id):
        print("Update TFE workspaces with new keys")
        tfe_key = avm_common.get_secret("terraform")
        tfe_api_token = tfe_key['terraform']
        headers = {
                'authorization': "Bearer " + tfe_api_token,
                'content-type': "application/vnd.api+json",
            }

        tfe_workspaces = self.get_tfe_workspaces(account_id)
        for workspace_name in tfe_workspaces:
            workspace_id = self.get_workspace_id(workspace_name, headers)
            self.remove_workspace_vars(workspace_name, headers)
            self.create_tfe_variables(workspace_id, headers, keys["AccessKeyId"], keys["SecretAccessKey"])


    def get_tfe_workspaces(self,AccountId):
        print(f"Get TFE workspaces as a list from DynamoDB for {AccountId}")
        try:
            response = self._ddb_table.get_item(Key={'id': AccountId})
            app_details = json.loads(response['Item']['app_details'])
            print(app_details["tfe_workspace"])
            workspaces = app_details["tfe_workspace"].split(',')
            return workspaces
        except:
            self.notify(f"ERROR: AVM::KeyRotation - Unable to find the app_workspace for account: {AccountId}")
            pass
        #return ['baseline-developers-developer-paul-li-dev', 'corp-rudy-sampleapp-dev']

    def get_param(self,param):
        return avm_common.get_param(param)

    def get_workspace_id(self,workspace_name, headers):
        tfe_url = f'{tfe_api}/organizations/{org}/workspaces/{workspace_name}'
        r = requests.get(tfe_url, headers=headers)
        data = r.json()
        workspace_id = data["data"]["id"]
        return workspace_id


    def remove_workspace_vars(self,workspace_name, headers):
        tfe_url = f'{tfe_api}/vars?filter%5Borganization%5D%5Bname%5D={org}&filter%5Bworkspace%5D%5Bname%5D={workspace_name}'
        r = requests.get(tfe_url, headers=headers)
        data = r.json()
        for var in data["data"]:
            if var["attributes"]["key"] == "AWS_ACCESS_KEY_ID":
                self.delete_tfe_var(var["id"], headers)
            elif var["attributes"]["key"] == "AWS_SECRET_ACCESS_KEY":
                self.delete_tfe_var(var["id"], headers)
        return data


    def delete_tfe_var(self,var_id, headers):
        tfe_url = f'{tfe_api}/vars/{var_id}'
        r = requests.delete(tfe_url, headers=headers)
        return r


    def create_tfe_variables(self,workspace_id, headers, access_key_id, access_key_secret):
        key_id_payload = self.create_key_id_json(access_key_id, workspace_id)
        secret_payload = self.create_secret_json(access_key_secret, workspace_id)

        print("Add Key_ID")
        tfe_url = f'{tfe_api}/vars'
        r = requests.post(tfe_url, headers=headers, json=key_id_payload)
        data = r.json()

        print("Add Secret")
        tfe_url = f'{tfe_api}/vars'
        r = requests.post(tfe_url, headers=headers, json=secret_payload)
        data = r.json()

    def create_key_id_json(self,access_key_id, workspace_id):
        payload_json = """
        {
          "data":{
            "type":"vars",
            "attributes":{
              "key":"AWS_ACCESS_KEY_ID",
              "value":"%s",
              "category":"env",
              "hcl":false,
              "sensitive":false
            },
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
        """ % (access_key_id, workspace_id)
        payload = json.loads(payload_json)
        return payload


    def create_secret_json(self,access_key_secret, workspace_id):
        payload_json = """
        {
          "data":{
            "type":"vars",
            "attributes":{
              "key":"AWS_SECRET_ACCESS_KEY",
              "value":"%s",
              "category":"env",
              "hcl":false,
              "sensitive":true
            },
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
        """ % (access_key_secret, workspace_id)
        payload = json.loads(payload_json)
        return payload

    def notify(self,message):
        # TODO: Set up notifications
        sub  = "INFO: accountpipeline keyrotation-for-terraform-user"
        func = "accountpipeline-tfe-secret-rotation"
        sns_topic = avm_common.get_param("sns_topic_arn")
        avm_common.send_pipeline_notification(self._account,sns_topic,func, sub,message)


def lambda_handler(event, context):
    try:
        account_id = event["AccountId"]
        sns_topic = avm_common.get_param("sns_topic_arn")
        print(sns_topic)
        print(account_id)
        sub  = "ERROR: accountpipeline keyrotation-for-terraform-user"
        func = "accountpipeline-tfe-secret-rotation"
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
    tlzKeyMan = tlzKeyRotator(account_id)

    #response = iam.list_users()
    #user_name =  response["Users"][0]["UserName"]
    secret_name = avm_common.get_param("terraform_service_user")
    keys = tlzKeyMan.get_access_keys(secret_name)
    tlzKeyMan.update_tfe_workspaces(keys, secret_name, account_id)

if __name__ == '__main__':
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
