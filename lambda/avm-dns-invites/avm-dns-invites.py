import os
import boto3
import avm_common
from botocore.exceptions import ClientError
import time
import json
import sys

# Lambda handler
def lambda_handler(event, context):
    try:
        account_id = event["AccountId"]
        lambda_handler_inner(event, context)
    except ClientError as e:
        body = f"Unexpected error : {e}"
        print(body)
        sns_topic = avm_common.get_param("sns_topic_arn")
        print(sns_topic)
        print(account_id)
        sub  = "ERROR: DNS Invite"
        func = "avm-dns-invite-member-account"
        avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)
        raise e

# main handler
def lambda_handler_inner(event, context):
    account_id = event["AccountId"]
    account_details = avm_common.get_account_details(account_id)
    account_type  = account_details["org_details"]["accountType"]
    print(f"account_type is {account_type}")

    skip_process = True
    if account_type.lower() in ["application"]:
        skip_process = False

    if not skip_process:
        print(f"Invite dns invites for  account: {account_id}" )
        process(event,context)
    else:
        print(f"skip dns invite for the account {account_id}" )

def process(event, context):
    # 1.  Identify target account VPC ID.
    # aws ec2 describe-vpcs
    # Assume role to target_account
    account_id = event["AccountId"]
    master_role =  avm_common.get_param("tlz_admin_role")
    primary_region, secondary_region = avm_common.get_regions(account_id)

    target_session = avm_common.aws_session(role=f"arn:aws:iam::{account_id}:role/{master_role}", session_name='target-account')

    regions  = [secondary_region, primary_region]
    vpcs = []

    for region in regions:
        print("Processing %s region" %(region))
        try:
            ec2 = target_session.client('ec2', region_name=region)
            response = ec2.describe_vpcs()
            v = [ {"VPCId" : x['VpcId'], "VPCRegion" : region} for x in response["Vpcs"]]
            vpcs.extend(v)
        except ClientError as e:
            print(e)
        except:
            print("Unexpected error")

    #print(vpcs)
    # 2. On core-common-shared-service account (Route 53 Privated Hosted Zone SOA and InfoBlox forwarder), create vpc association authorization.
    # aws route53 list-hosted-zones (assume the below is the default zone and will not change)
    core_shared_services = avm_common.get_param("core_shared_services_account")
    ROLE_ARN_SharedServices=f"arn:aws:iam::{core_shared_services}:role/{master_role}"
    session_common_shared = avm_common.aws_session(role=ROLE_ARN_SharedServices, session_name='core-shared-services')
    print("Able to assume role")
    route53 = session_common_shared.client('route53')
    zones_response = route53.list_hosted_zones()
    #print(zones_response)
    # Get the hosted_zone_id for HostedZone-> aws.spe.sony.com.
    hosted_zone_ids = [ z['Id'] for z in zones_response['HostedZones'] if  "aws.tlz-avm.com" in z['Name']]
    print(hosted_zone_ids)
    for x in hosted_zone_ids:
        for vpc in vpcs:
            response = route53.create_vpc_association_authorization(
                HostedZoneId = x,
                VPC = vpc
            )
            print(json.dumps(response))
    print("****** Step : Accept VPC association authorization ******")
    # 3. On target account, accept vpc association authorization.
    # aws route53 associate-vpc-with-hosted-zone --hosted-zone-id "/hostedzone/$awsR53PHZ" --vpc VPCRegion=" $awsRegion",VPCId="$targetAccountVPCID"
    route53_target = target_session.client('route53')
    for x in hosted_zone_ids:
        for vpc in vpcs:
            try:
                accept_response = route53_target.associate_vpc_with_hosted_zone(
                    HostedZoneId = x,
                    VPC = vpc
                )
                print(json.dumps(accept_response))
            except ClientError as e:
                 print(e)
            except:
                print("Unknown error")
    # 4. On core-common-shared-service account, delete vpc assoiciation authorization.
    # aws route53 delete-vpc-association-authorization --hosted-zone-id "/hostedzone/$awsR53PHZ " --vpc VPCRegion="$awsRegion ",VPCId="$targetAccountVPCID "
    print("****** Step: Delete VPC association authorization for core shared******")

    for x in hosted_zone_ids:
        for vpc in vpcs:
            delete_response = route53.delete_vpc_association_authorization(
                HostedZoneId = x,
                VPC = vpc
            )
            print(json.dumps(delete_response))

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
