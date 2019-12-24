import os
import boto3
from botocore.exceptions import ClientError
import avm_common

import time
import json
import sys


# This script will setup GuardDuty on the master account and invite a member account.
# Contributed by Assaf Namer, namera@amazon.com
#
# Run this script using master account access-key and secret-access key
#
# Usage: python3 gd_setup_master.py  --member_account_id 123456789012 --member_account_email MemberAccountRoot@example.com





def get_regions(ec2_client):
  """
  Return all AWS regions
  """

  regions = []

  try:
    aws_regions = ec2_client.describe_regions()['Regions']
  except ClientError as e:
    print(e.response['Error']['Message'])

  else:
    for region in aws_regions:
      regions.append(region['RegionName'])

  return regions

def send_error_notification(e, account_id):

    body = f"Unexpected error : {e}"
    print(body)
    sns_topic = avm_common.get_param("sns_topic_arn")
    print(sns_topic)
    print(account_id)
    sub  = "ERROR: GuardDuty invites"
    func = "avm-guardduty-invite-member-accounts"
    #(accountId, snsARN, function_name, subject, body):
    avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)

def lambda_handler(event, context):
    try:
        account_id = event["AccountId"]
        lambda_handler_inner(event, context)
    except ClientError as e:
        send_error_notification(e,account_id)
        raise e       

def lambda_handler_inner(event, context):
    core_security = avm_common.get_param("core_security_account")
    master_role =  avm_common.get_param("tlz_admin_role")

    ROLE_ARN_SECURITY=f"arn:aws:iam::{core_security}:role/{master_role}"
    session_assumed = avm_common.aws_session(role=ROLE_ARN_SECURITY, session_name='security-services')
    gd_client = session_assumed.client('ec2', region_name='us-east-1')
    if core_security == event["AccountId"]:
        print("No need to send guradduty invites as guardDuty master account cannot be member to itself")
        return

    regions = get_regions(gd_client)
    for region in regions:#
        print("Processing %s region" %(region))
        try:
            client = session_assumed.client('guardduty', region_name=region)
            #Find out if GuardDuty already enabled:
            detectors_list = client.list_detectors()

            if not detectors_list["DetectorIds"]:
                print ("GuardDuty is not enabled ... enabling GuardDuty on master account")
                response = client.create_detector(Enable=True)
                # Save DetectorID handler
                DetectorId = response["DetectorId"]
            else:
                print("GuardDuty already enabled on account")
                DetectorId = detectors_list['DetectorIds'][0]
            # Do error handling here

            # print all Detectorts
            detectors_list = client.list_detectors()
            print ("Detector lists: ")
            for x in detectors_list["DetectorIds"]:
                #print(x, end=" ")
                print(x)
            account_id = event["AccountId"]
            account = avm_common.get_account_details(account_id)
            print(f"id from event : {account_id} id from orgdetails: {account['org_details']['id']}")
            if account:
                # invite an account
                print(account['org_details'])
                print ("\nInviting member account " + account_id)
                invite_member = client.create_members(
                    AccountDetails=[
                        {
                            'AccountId': account_id,
                            'Email': account['org_details']["email"]
                        },
                    ],
                    DetectorId=DetectorId
                )

                gd_members = client.get_members(
                    AccountIds=[
                        account_id,
                    ],
                    DetectorId=DetectorId
                )

                # the future member account is now staged
                if gd_members:
                    print(gd_members)
                    print ("Memeber account RelationshipStatus: " + gd_members['Members'][0]['RelationshipStatus'])

                # Invite members account(s)
                response = client.invite_members(
                    AccountIds=[
                        account_id,
                    ],
                    DetectorId=DetectorId,
                    Message='Please join AWS GuardDuty master account'
                )

                gd_members = client.get_members(
                    AccountIds=[
                        account_id,
                    ],
                    DetectorId=DetectorId
                )
                # the future member account should be 'pending'
                print ("Memeber account RelationshipStatus: " + gd_members['Members'][0]['RelationshipStatus'])
        except ClientError as e:
            send_error_notification(e,account_id)
        

    # Enable GuardDuty on target account and accept the invites
    print(f"About to enable and accept requests for {account_id}")
    target_session = avm_common.aws_session(role=f"arn:aws:iam::{account_id}:role/{master_role}", session_name='target-account')
    for region in regions:
        print("Processing %s region" %(region))
        try:
            client = target_session.client('guardduty', region_name=region)
            #Find out if GuardDuty already enabled:
            detectors_list = client.list_detectors()

            if not detectors_list["DetectorIds"]:
                print (f"GuardDuty is not enabled ... enabling GuardDuty on {account_id} account")
                response = client.create_detector(Enable=True)
                # Save DetectorID handler
                DetectorId = response["DetectorId"]
            else:
                print(f"GuardDuty already enabled on account {account_id}")
                DetectorId = detectors_list['DetectorIds'][0]
            # accept the invites
            response = client.list_invitations(MaxResults=10)
            if response:
                invites = [i for i in response['Invitations']]
                for i in invites:
                    r = client.accept_invitation(DetectorId=DetectorId,InvitationId=i["InvitationId"],MasterId=i["AccountId"])
        except ClientError as e:
            body = f"Unexpected error : {e}"
            print(body)
            send_error_notification(e,account_id)

if __name__ == "__main__":
    from optparse import OptionParser
    import pprint
    import json
    import sys

    parser = OptionParser()
    parser.add_option("-a", "--account_number", dest="account_number", help="AccountNUmber to test",default="694866286020")
    pp = pprint.PrettyPrinter(indent=4)
    (options, args) = parser.parse_args(sys.argv)
    pp.pprint(options)
    event = { "AccountId": f"{options.account_number}"}
    lambda_handler(event,None)
