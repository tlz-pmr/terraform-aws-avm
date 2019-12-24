from __future__ import print_function

import json

import sys
import os
import boto3
import botocore
import pprint
import json
import time
from botocore.exceptions import ClientError
import avm_common


#from awsretry import AWSRetry
pp = pprint.PrettyPrinter(indent=4)
from decimal import Decimal

class fakefloat(float):
    def __init__(self, value):
        self._value = value
    def __repr__(self):
        return str(self._value)

def defaultencode(o):
    if isinstance(o, Decimal):
        # Subclass float with custom repr?
        return fakefloat(o)
    raise TypeError(repr(o) + " is not JSON serializable")


class awsOrgManager:
    """Class that manages access to AWSOrgnization resources"""
    _session = None
    _client = None
    _resource = None
    _master_id = None
    _caller_account_id = None
    _master_account = None
    _master_role = None

    def __init__(self, session, caller_account,master_account,master_role, org_account_access_role):
        self._session = session
        self._client = self._session.client('organizations')
        self._caller_account_id = caller_account
        self._pp = pprint.PrettyPrinter(indent=4)
        self._master_account = master_account
        self._master_role = master_role
        self._org_account_access_role = org_account_access_role



    def get_org(self,org_name):
        # This search looks for OUs within the top level of the AWS organization.
        # The AVM currently expects all TLZ OUs to live at this top level--
        # Core, Sandbox, POC, et cetera.

        response = self._client.list_roots()
        parents = response['Roots']
        parent_id = parents[0]['Id']
        #print(f"Parent returned by list_roots() is {parent_id}")
        token = None
        # orgs
        orgs = {}
        paginator = self._client.get_paginator('list_organizational_units_for_parent')
        counter = 1
        while True:
            # print(token)
            #print(f"Main counter: {counter}")
            counter = counter + 1
            response_iterator = paginator.paginate( ParentId=parent_id,
                    PaginationConfig={
                        'MaxItems': 123,
                        'PageSize': 10,
                        'StartingToken': token
                    }
                    )
            ous = None
            page_count = 1
            for ous in response_iterator:
                #print(f"Page count : {page_count} : [{len(ous['OrganizationalUnits'])}]")
                page_count = page_count + 1
                for o in ous["OrganizationalUnits"]:
                    orgs[o['Name']] = o['Id']
                    #print(o['Name'])
                #print(ous)
            #print(ous)
            if "NextToken" not in ous.keys():
                break
            else:
                token = ous["NextToken"]


        #print(orgs.keys())
        #print(len(orgs))

        if org_name in orgs.keys():
            print(f"Found OU {org_name} at org root...")
            return orgs[org_name]
        else:
            # create a new org
            print(f"OU {org_name} not found at org root (will be created)...")
            response = self._client.create_organizational_unit(ParentId=parent_id,Name=org_name)
            return response['OrganizationalUnit']['Id']


    def get_master(self):
        if not self._master_id:
            sts_client = self._session.client("sts")
            self._master_id = sts_client.get_caller_identity()["Account"]
        return self._master_id

    def move_account(self,account_id, target_org):
        response = self._client.list_parents(ChildId=account_id)
        parents = response["Parents"]
        parent_id = parents[0]["Id"]
        target_parent_id = self.get_org(target_org)
        if (parent_id == target_parent_id):
            print(f"Account {account_id} is already in the proper OU, skipping move...")
        # The master payer account is the organization root account; it should not live in an OU,
        # and SCPs do not apply to it.
        # Reference: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scp.html#not-restricted-by-scp
        elif (account_id == self.get_master()):
            print(f"Account {account_id} is the organization master account, skipping move...")
        else:
            response = self._client.move_account(AccountId=account_id,
                                                SourceParentId=parent_id,
                                                DestinationParentId=target_parent_id)

    def get_account_alias(self,account_type,name,lob,environment, account_prefix):
        alias = None
        slug = name.replace(' ', '-').lower()
        if account_type.lower() == "application":
            alias = f"{account_prefix}-app-{lob.lower()}-{slug}-{environment.lower()}"
        elif account_type.lower() == "core":
            alias = f"{account_prefix}-{account_type.lower()}_{slug}"
        else:
            alias = f"{account_prefix}-{account_type.lower()}-{slug}"
        return alias

    def get_account_by_email(self,email):
        accounts = self.list_accounts()
        account = [a for a in accounts if a["email"] == email  ]
        print("we are in get_account_by_email")
        print(account)
        if len(account):
            return account[0]
        else:
            return None

    def list_accounts(self):
        try:
            paginator = self._client.get_paginator('list_accounts')
            marker = None
            accounts = []
            while True:
                if marker:
                    response = paginator.paginate(PaginationConfig={'MaxItems': 123,'PageSize': 20, 'StartingToken': marker})
                else:
                    response = paginator.paginate(PaginationConfig={'MaxItems': 123,'PageSize': 20})

                for acc_array in response:
                    for acc in acc_array["Accounts"]:
                        accounts.append(self.get_account(acc))
                    try:
                        marker = acc_array['NextToken']
                    except KeyError:
                        return accounts
            return accounts
        except botocore.exceptions.ClientError as e:
            raise e

    def assume_role_to_target(self,account,role_name,source_session=None):
        print(f"Assuming {role_name} role for {account}")
        role_arn = f"arn:aws:iam::{account}:role/{role_name}"
        session = avm_common.aws_session(role=role_arn, session_name="client_session",source_session=source_session)
        return session


    def update_org_account_access_role(self,account):
        # AssumeRole as org_account_access_role as master_payer
        master_session = self.assume_role_to_target(account,self._org_account_access_role,self._session)
        # Create automation role if not exist
        client = master_session.client('iam')
        policy_doc ="""{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": ["arn:aws:iam::%s:root"]
      },
      "Action": "sts:AssumeRole"
    }
]}""" %(self._caller_account_id)

        try:
            response = client.create_role(RoleName=self._master_role,AssumeRolePolicyDocument=policy_doc,Description="tlz-avm automation role")
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                pass
        response = client.attach_role_policy(RoleName=self._master_role, PolicyArn="arn:aws:iam::aws:policy/AdministratorAccess")

        return response



    def get_account(self,account):
        print(f"Getting details for {account['Id']}")
        response = self._client.describe_account(AccountId=account['Id'])
        account = response["Account"]
        response = self._client.list_parents(ChildId=account['Id'])
        parents = response["Parents"]
        parent_id = parents[0]["Id"]
        parent_type = parents[0]["Type"]
        org_name = ""
        if parent_type == "ORGANIZATIONAL_UNIT":
            org_details = self._client.describe_organizational_unit(OrganizationalUnitId=parent_id)
            org_name = org_details["OrganizationalUnit"]["Name"]


        #self._pp.pprint(parents)
        act  = {}
        act["id"] =  account['Id']
        act["type"] =  "account"
        act["email"] = account['Email']
        act["name"] = account["Name"]
        act["method"] = account["JoinedMethod"]
        act["joined_date"] = str(account['JoinedTimestamp'])
        act["status"] = account["Status"]
        act["parent_id"] = parent_id
        act["parent_type"] = parent_type
        act["org_name"] = org_name
        act["master"] = self.get_master()
        act["vendor"] = "aws"
        return act

    def ingest_data(self,target_session,a):
        try:
            client = target_session.client('dynamodb')
            resource = target_session.resource('dynamodb')
            table = resource.Table('OrgDetails')
            #print(a)
            row = {}
            is_update = False
            for k in a.keys():
                row[k] = {"S" : a[k] or 'NULL'}
            #client.put_item(TableName="OrgDetails",Item=row)


            try:
                response = table.get_item(Key={'id': a["id"]})
                #print("Get item succeeded")
                if "Item" in response.keys():
                    is_update=True
            except ClientError as e:
                print("Error:Unable to query")
                print(e)
                is_update=True

            if is_update:
                print("Updating the account")
                item = response['Item']
                #reserved_list = ["id", "type","name","method","status"]
                reserved_list = ["pipe_line_status","sent_support_emails","account_request"]
                # delete key id from hash
                up_expr_arr = [ f"{k} = :{k}" for k in row.keys() if k in reserved_list]
                up_expr_str = " ,".join(up_expr_arr)
                expr_attr_dict = {}
                pp.pprint(f"Updating account : {a['id']}")
                for k in row.keys():
                    if k in reserved_list and row[k]:
                        expr_attr_dict[f":{k}"] = row[k]["S"] or "NULL"
                #pp.pprint(f"Updating account : {a['id']}")
                pp.pprint(expr_attr_dict)
                pp.pprint(up_expr_str)
                response = table.update_item(Key={
                    'id': item["id"]
                },
                UpdateExpression=f"set {up_expr_str}",
                ExpressionAttributeValues=expr_attr_dict,
                ReturnValues="UPDATED_NEW"
            )
            else:
                client.put_item(TableName="OrgDetails",
                Item=row)
                pp.pprint(f"Adding account : {a['id']}")

        except Exception as e:
            print("Error adding data to table:")
            print(e)

    def start_pipeline(self,target_session,account_id, additional_info):
        print("Invoking the pipeline")
        client = target_session.client('ssm', region_name="us-east-2")
        response = client.start_automation_execution(
        DocumentName='tlz-avm-ssm-document',
        Parameters={
        'AccountId': [str(account_id)],
        'AccountType' : [additional_info["account_type"]],
        'AdditionalInfo' : [json.dumps(additional_info).replace('"','\\"')]

        }
        )
        print(response)

    def create_account(self,account_request):
        print(account_request)
        role_name = self._org_account_access_role
        print(f'Email : {account_request["email"]}')
        account = self.get_account_by_email(account_request["email"])
        print("Response from Create account")
        print(account)
        account_created = False
        max_attempts = 30
        attempts = 0
        response = None
        create_account = False
        if account:
            return account
        else:
            print(f"Account with email: {account_request['email']} not found and creating a new account")
            create_account = True


        if create_account:
            alias = self.get_account_alias(account_request["accountType"],account_request["account_name"],account_request["lob"], account_request["env"], account_request["accountPrefix"])
            response = self._client.create_account(
                Email=account_request["email"],
                AccountName=alias,
                RoleName=role_name
            )
            print(response)
            account_created = False
            max_attempts = 50
            while account_created != True:
                response = self._client.describe_create_account_status(CreateAccountRequestId=response["CreateAccountStatus"]["Id"])
                if response["CreateAccountStatus"]["State"] == "SUCCEEDED":
                    account_created = True
                    break
                else:
                    time.sleep(5)
                    attempts = attempts + 1
                    if attempts > max_attempts:
                        break
            # By now account should have been created
            if account_created:
                acc = self._client.describe_account(AccountId=response["CreateAccountStatus"]["AccountId"])
                # retry 5 times until sts succeeds
                sleep_time = 10
                num_retries = 5
                result_account = None
                for x in range(0, num_retries):
                    try:
                        target_session = self.assume_role_to_target(acc,role_name)
                        # Update trust-policy of the role_name so that CSS can assume the role_name
                        break
                    except Exception as str_error:
                        time.sleep(sleep_time)
                        sleep_time *= 2

                if not result_account:
                    # send an SNS notification
                    body = f"Master account unable to assume {self._master_role} for {acc}"
                    sns_topic = avm_common.get_param("sns_topic_arn")
                    sub  = "WARN: tfe avm-tfe-master-lambda"
                    func = "avm-tfe-master-lambda"
                    avm_common.send_pipeline_notification(account_request['email'],sns_topic,func, sub,body)

                return self.get_account(acc)
            else:
                return None



def lambda_handler(event, context):
    try:
        insert_event = [i for i in event["Records"] if i["eventName"] == "INSERT"]
        if not len(insert_event):
            print("ERROR: No account to create")
            return

        newImage = insert_event[0]["dynamodb"]["NewImage"]
        account_email =  newImage["id"]["S"]
        sns_topic = avm_common.get_param("sns_topic_arn")
        print(sns_topic)
        sub  = "ERROR: tfe avm-tfe-master-lambda"
        func = "avm-tfe-master-lambda"
        lambda_handler_inner(event, context)
    except ClientError as e:
        body = f"Unexpected error : {e}"
        print(body)
        #(accountId, snsARN, function_name, subject, body):
        avm_common.send_pipeline_notification(account_email,sns_topic,func, sub,body)
        raise e
    except Exception as e:
        body = f"Unexpected error : {e}"
        print(body)
        avm_common.send_pipeline_notification(account_email,sns_topic,func, sub,body)
        raise e

def lambda_handler_inner(event, context):
    master_account = avm_common.get_param("master_payer_account")
    master_role =  avm_common.get_param("tlz_admin_role")
    org_account_access_role = avm_common.get_param("tlz_org_account_access_role")
    #print("Received event: " + json.dumps(event, indent=2))
    master_role_arn = f"arn:aws:iam::{master_account}:role/{org_account_access_role}"
    session_local = avm_common.aws_session()
    current_account = session_local.client('sts').get_caller_identity().get('Account')
    session_regular = avm_common.aws_session(role=master_role_arn)

    account_request = {}
    insert_event = [i for i in event["Records"] if i["eventName"] == "INSERT"]
    if not len(insert_event):
        print("ERROR: No account to create")
        return

    newImage = insert_event[0]["dynamodb"]["NewImage"]
    account_request["email"] =  newImage["id"]["S"]
    account_request["account_name"] = newImage["appName"]["S"]
    account_request["accountType"] = newImage["accountType"]["S"]
    account_request["accountPrefix"] = newImage["accountPrefix"]["S"]

    account_request["lob"] = newImage["lob"]["S"]
    if account_request["accountType"].lower() != "application":
        account_request["lob"] = account_request["accountType"].title()
    account_request["env"] = newImage["envType"]["S"]

    # CloudOps interal variable definition that will be used in certain areas where only prd, npd, sbx or dev are needed
    if (account_request["env"] == "stg" or account_request["env"] == "qa" or account_request["env"] == "dev"):
        account_request["intEnvironment"] = "npd"
    elif (account_request["env"] == "pre-prod" or account_request["env"] == "prd"):
        account_request["intEnvironment"] = "prd"

    print(account_request)
    orgMan = awsOrgManager(session_regular,current_account,master_account,master_role,org_account_access_role)
    account = orgMan.create_account(account_request)
    # By now account should have been created
    if account:
        target_ou = "Sandbox"
        # Move the account the target organizational_unit
        if account_request["accountType"].lower() != "application":
            target_ou = account_request["accountType"].title()
        else:
            if "lob" in account_request.keys():
                if account_request["lob"]:
                    target_ou = account_request["lob"]

        orgMan.move_account(account["id"],target_ou)
        acc = orgMan._client.describe_account(AccountId=account["id"])

    # update account with additional details
    account["account_request"] = json.dumps(account_request,default=defaultencode)
    alias = orgMan.get_account_alias(account_request["accountType"],account_request["account_name"],account_request["lob"], account_request["env"], account_request["accountPrefix"] )
    account["alias"]  = alias
    account["accountType"]  = account_request["accountType"]
    org = account_request["lob"].title()
    git_url = avm_common.get_param("tlz_git_url")
    print(git_url)
    vended_applications_project = avm_common.get_param("vended_applications_project")
    vended_baselines_project = avm_common.get_param("vended_baselines_project")
    if avm_common.resource_workspace_required(account_request["accountType"]):
        account["app_details"]  = json.dumps({'git' : f'{git_url}/{vended_applications_project}/{alias}.git', 'tfe_workspace': f'{alias}-resources'})
        account["baseline_details"]  = json.dumps({'git' : f'{git_url}/{vended_baselines_project}/{alias}.git', 'tfe_workspace': f'{alias}-baseline'})
    else:
        account["baseline_details"]  = json.dumps({'git' : f'{git_url}/{vended_baselines_project}/{alias}.git', 'tfe_workspace': f'{alias}'})

    print(account)
    orgMan.ingest_data(session_local,account)
    additional_info = {}
    additional_info["alias"] = alias
    additional_info["account_type"] = account_request["accountType"]
    additional_info["org_name"] = account_request["lob"]
    additional_info["owner"] = newImage["responsible"]["S"]
    additional_info["environment"] = account_request["env"]
    additional_info["intEnvironment"] = account_request["env"]
    additional_info["primaryVpcCidr"] = newImage["primaryVpcCidr"]["S"]
    additional_info["secondaryVpcCidr"] = newImage["secondaryVpcCidr"]["S"]
    #for k in newImage.keys():
    #    additional_info[k] = newImage[k]["S"]
    #additional_info["account"] = account
    orgMan.update_org_account_access_role(account["id"])
    print("About to call the automation document")
    orgMan.start_pipeline(session_local, account["id"], additional_info)


if __name__ == "__main__":
    import logging
    from optparse import OptionParser
    import pprint
    import json
    import sys

    parser = OptionParser()
    parser.add_option("-f", "--event_file", dest="event_file", help="Event file to be processed")
    pp = pprint.PrettyPrinter(indent=4)
    (options, args) = parser.parse_args(sys.argv)
    pp.pprint(options)
    with open(options.event_file) as json_data:
        event = json.load(json_data)
        lambda_handler(event,None)
