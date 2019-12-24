import boto3
from botocore.exceptions import ClientError
import os
import json
import logging
import sys
import avm_common

vpc_id = []

def delete_igw(ec2_client, vpc_id):
  """
  Detach and delete the internet gateway
  """

  args = {
    'Filters' : [
      {
        'Name' : 'attachment.vpc-id',
        'Values' : [ vpc_id ]
      }
    ]
  }

  try:
    igw = ec2_client.describe_internet_gateways(**args)['InternetGateways']
  except ClientError as e:
    print(e.response['Error']['Message'])

  if igw:
    igw_id = igw[0]['InternetGatewayId']

    try:
      result = ec2_client.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
    except ClientError as e:
      print(e.response['Error']['Message'])

    try:
      result = ec2_client.delete_internet_gateway(InternetGatewayId=igw_id)
    except ClientError as e:
      print(e.response['Error']['Message'])

  return


def delete_subs(ec2_client, args):
  """
  Delete the subnets
  """

  try:
    subs = ec2_client.describe_subnets(**args)['Subnets']
  except ClientError as e:
    print(e.response['Error']['Message'])

  if subs:
    for sub in subs:
      sub_id = sub['SubnetId']

      try:
        result = ec2_client.delete_subnet(SubnetId=sub_id)
      except ClientError as e:
        print(e.response['Error']['Message'])

  return


def delete_rtbs(ec2_client, args):
  """
  Delete the route tables
  """

  try:
    rtbs = ec2_client.describe_route_tables(**args)['RouteTables']
  except ClientError as e:
    print(e.response['Error']['Message'])

  if rtbs:
    for rtb in rtbs:
      main = 'false'
      for assoc in rtb['Associations']:
        main = assoc['Main']
      if main == True:
        continue
      rtb_id = rtb['RouteTableId']

      try:
        result = ec2_client.delete_route_table(RouteTableId=rtb_id)
      except ClientError as e:
        print(e.response['Error']['Message'])

  return


def delete_acls(ec2_client, args):
  """
  Delete the network access lists (NACLs)
  """

  try:
    acls = ec2_client.describe_network_acls(**args)['NetworkAcls']
  except ClientError as e:
    print(e.response['Error']['Message'])

  if acls:
    for acl in acls:
      default = acl['IsDefault']
      if default == True:
        continue
      acl_id = acl['NetworkAclId']

      try:
        result = ec2_client.delete_network_acl(NetworkAclId=acl_id)
      except ClientError as e:
        print(e.response['Error']['Message'])

  return


def delete_sgps(ec2_client, args):
  """
  Delete any security groups
  """

  try:
    sgps = ec2_client.describe_security_groups(**args)['SecurityGroups']
  except ClientError as e:
    print(e.response['Error']['Message'])

  if sgps:
    for sgp in sgps:
      default = sgp['GroupName']
      if default == 'default':
        continue
      sg_id = sgp['GroupId']

      try:
        result = ec2_client.delete_security_group(GroupId=sg_id)
      except ClientError as e:
        print(e.response['Error']['Message'])

  return


def delete_vpc(ec2_client, vpc_id, region):
  """
  Delete the VPC
  """

  try:
    result = ec2_client.delete_vpc(VpcId=vpc_id)
  except ClientError as e:
    print(e.response['Error']['Message'])

  else:
    print('VPC {} has been deleted from the {} region.'.format(vpc_id, region))

  return


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

def lambda_handler(event, context):
    try:
        account_id = event["AccountId"]
        sns_topic = avm_common.get_param("sns_topic_arn")
        print(sns_topic)
        print(account_id)
        sub  = "ERROR: accountpipeline default vpc delete"
        func = "accountpipeline-vpcs-delete-defaults"
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
  account_type = "sandbox"
  account_info = avm_common.get_account_details(account_id)
  account_details = account_info["org_details"]
  if not account_details:
    raise Exception(f"Account with id [{account_id}] not found in DynamoDB")
  account_type = account_details["accountType"].lower()

  print(f"account_type is {account_type}")
  print("starting process to delete default vpcs in all regions...")
  process(event,context)
  


def process(event, context):
  """
  Do the work..
  Order of operation:
  1.) Delete the internet gateway
  2.) Delete subnets
  3.) Delete route tables
  4.) Delete network access lists
  5.) Delete security groups
  6.) Delete the VPC
  """
  account_id = event["AccountId"]
  master_role =  avm_common.get_param("tlz_admin_role")
  ROLE_ARN = f"arn:aws:iam::{account_id}:role/{master_role}"

  session = avm_common.aws_session(role=ROLE_ARN, session_name="target_account")
  ec2_client = session.client('ec2', region_name='us-east-1')

  regions = get_regions(ec2_client)
  #regions = ["us-west-2"]
  for region in regions:

    # ec2_client = session.client('ec2', region_name=region)
    ec2_client= session.client('ec2', region_name=region)

    try:
      attribs = ec2_client.describe_account_attributes(AttributeNames=[ 'default-vpc' ])['AccountAttributes']
    except ClientError as e:
      print(e.response['Error']['Message'])
      return

    else:
      vpc_id = attribs[0]['AttributeValues'][0]['AttributeValue']

    if vpc_id == 'none':
      print('VPC (default) was not found in the {} region.'.format(region))
      continue
    # Are there any existing resources?  Since most resources attach an ENI, let's check..

    args = {
      'Filters' : [
        {
          'Name' : 'vpc-id',
          'Values' : [ vpc_id ]
        }
      ]
    }

    try:
      eni = ec2_client.describe_network_interfaces(**args)['NetworkInterfaces']
    except ClientError as e:
      print(e.response['Error']['Message'])
      return

    if eni:
      print('VPC {} has existing resources in the {} region.'.format(vpc_id, region))
      continue


    result = delete_igw(ec2_client, vpc_id)
    result = delete_subs(ec2_client, args)
    result = delete_rtbs(ec2_client, args)
    result = delete_acls(ec2_client, args)
    result = delete_sgps(ec2_client, args)
    result = delete_vpc(ec2_client, vpc_id, region)

  return

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
