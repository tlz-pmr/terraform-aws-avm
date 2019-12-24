import os
import boto3

from botocore.exceptions import ClientError
import avm_common
import time
import json
import sys

# source :  https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html#access-logging-bucket-permissions

alb_s3_region_account_map = {
"us-east-1": "127311923021",
"us-east-2": "033677994240",
"us-west-1": "027434742980",
"us-west-2": "797873946194",
"ca-central-1": "985666609251",
"eu-central-1": "054676820928",
"eu-west-1": "156460612806",
"eu-west-2": "652711504416",
"eu-west-3": "009996457667",
"eu-north-1": "897822967062",
"ap-east-1": "754344448648",
"ap-northeast-1": "582318560864",
"ap-northeast-2": "600734575887",
"ap-northeast-3": "383597477331",
"ap-southeast-1": "114774131450",
"ap-southeast-2": "783225319266",
"ap-south-1": "718504428378",
"sa-east-1": "507241528517",
"us-gov-west-1": "048591011584",
"us-gov-east-1": "190560391635",
"cn-north-1": "638102146993",
"cn-northwest-1": "037604701340"
}
def check_if_bucket_policy_exists(resource,bucket_name):
    try:
        bucket = resource.Bucket(bucket_name)
        policy = bucket.Policy()
        if policy.policy:
            return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == "NoSuchBucketPolicy":
            return False
        else:
            raise e
    except Exception as e:
        #logging all the others as warning
        print("ERROR: {}".format(e))
        raise e



# Update the ALB primary bucket policies
def update_alb_bucket_policy_primary(resource,account_id,bucket_name,core_logging_account,region):
    bucket = resource.Bucket(bucket_name)

    policy = bucket.Policy()
    policy_string = None
    if not check_if_bucket_policy_exists(resource,bucket_name):
        #print("There is no policy")
        policy_string="""
{
    "Version": "2012-10-17",
    "Id": "Policy1429136655940",
    "Statement": [
        {
            "Sid": "AllowALBLoadBalancerToWrite",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::%s:root"
            },
            "Action": "s3:PutObject",
            "Resource": []
        },
        {
            "Sid": "S3ReplicationPolicy",
            "Effect": "Allow",
            "Principal": {
                "AWS": []
            },
            "Action": [
                "s3:GetBucketVersioning",
                "s3:PutBucketVersioning",
                "s3:ReplicateObject",
                "s3:ReplicateDelete"
            ],
            "Resource": [
                "arn:aws:s3:::%s",
                "arn:aws:s3:::%s/*"
            ]
        },
        {
            "Sid": "AWSLogDeliveryWrite",
            "Effect": "Allow",
            "Principal": {
                "Service": "delivery.logs.amazonaws.com"
            },
            "Action": "s3:PutObject",
            "Resource": [],
            "Condition": {
                "StringEquals": {
                    "s3:x-amz-acl": "bucket-owner-full-control"
                }
            }
        },
        {
            "Sid": "AWSLogDeliveryAclCheck",
            "Effect": "Allow",
            "Principal": {
                "Service": "delivery.logs.amazonaws.com"
            },
            "Action": "s3:GetBucketAcl",
            "Resource": "arn:aws:s3:::%s"
        }
    ]
}
"""%(alb_s3_region_account_map[region],bucket_name,bucket_name,bucket_name)
    else:
        policy_string = policy.policy
    #print(policy_string)
    p =  json.loads(policy_string)
    stmts = {statement["Sid"]:statement for statement in p["Statement"]}
    resources = stmts["AllowALBLoadBalancerToWrite"]["Resource"]
    r = f"arn:aws:s3:::{bucket_name}/AWSLogs/{account_id}/*"
    #print(r)
    if not r in resources:
        result = []
        if type(resources) is list:
            resources.append(r)
            result = resources
        elif type(resources) is str:
            result.append(resources)
            result.append(r)
        stmts["AllowALBLoadBalancerToWrite"]["Resource"] = result
        stmts["AWSLogDeliveryWrite"]["Resource"] = result

    principals = stmts["S3ReplicationPolicy"]["Principal"]["AWS"]
    principal = f"arn:aws:iam::{account_id}:root"
    #print(principals)
    if not principal in principals:
        #print(pri)
        result = []
        if type(principals) is list:
            principals.append(principal)
            result = principals
        elif type(principals) is str:
            result.append(principals)
            result.append(principal)
        stmts["S3ReplicationPolicy"]["Principal"]["AWS"] = result

    #print(json.dumps(p))
    response = policy.put(ConfirmRemoveSelfBucketAccess=False,Policy=json.dumps(p))
    print(json.dumps(response))

# Update the ALB Secondary bucket policies
def update_alb_bucket_policy_secondary(resource,account_id,bucket_name,core_logging_account,region):
    bucket = resource.Bucket(bucket_name)
    policy = bucket.Policy()
    policy_string = None
    if not check_if_bucket_policy_exists(resource,bucket_name):
        #print("There is no policy")
        policy_string="""
{
    "Version": "2012-10-17",
    "Id": "Policy1429136655940",
    "Statement": [
        {
            "Sid": "AllowALBLoadBalancerToWrite",
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::%s:root"
            },
            "Action": "s3:PutObject",
            "Resource": []
        },
         {
            "Sid": "AWSLogDeliveryWrite",
            "Effect": "Allow",
            "Principal": {
                "Service": "delivery.logs.amazonaws.com"
            },
            "Action": "s3:PutObject",
            "Resource": [],
            "Condition": {
                "StringEquals": {
                    "s3:x-amz-acl": "bucket-owner-full-control"
                }
            }
        },
        {
            "Sid": "AWSLogDeliveryAclCheck",
            "Effect": "Allow",
            "Principal": {
                "Service": "delivery.logs.amazonaws.com"
            },
            "Action": "s3:GetBucketAcl",
            "Resource": "arn:aws:s3:::%s"
        }

    ]
}
"""%(alb_s3_region_account_map[region],bucket_name)
    else:
        policy_string = policy.policy

    p =  json.loads(policy_string)
    stmts = {statement["Sid"]:statement for statement in p["Statement"]}

    resources = stmts["AllowALBLoadBalancerToWrite"]["Resource"]
    r = f"arn:aws:s3:::{bucket_name}/AWSLogs/{account_id}/*"
    if not r in resources:
        result = []
        if type(resources) is list:
            resources.append(r)
            result = resources
        elif type(resources) is str:
            result.append(resources)
            result.append(r)
        stmts["AllowALBLoadBalancerToWrite"]["Resource"] = result
        stmts["AWSLogDeliveryWrite"]["Resource"] = result


    response = policy.put(ConfirmRemoveSelfBucketAccess=False,Policy=json.dumps(p))
    print(json.dumps(response))

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
        sub  = "ERROR: accountpipeline s3 update corelogging bucket policies"
        func = "avm-s3-updatepolicy"
        #(accountId, snsARN, function_name, subject, body):
        #avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)
        raise e

def lambda_handler_inner(event, context):
    account_id = event["AccountId"]
    account_details = avm_common.get_account_details(account_id)
    core_logging = avm_common.get_param("core_logging_account")
    master_role =  avm_common.get_param("tlz_admin_role")
    primary_region, secondary_region = avm_common.get_regions(account_id)

    ROLE_ARN_LOGGING=f"arn:aws:iam::{core_logging}:role/{master_role}"

    session_assumed = avm_common.aws_session(role=ROLE_ARN_LOGGING, session_name='logging-services')
    s3 = session_assumed.resource('s3')
    #s3 = session_assumed.client('s3')
    update_alb_bucket_policy_primary(s3,account_id,f"tlz-alb-access-central-primary-{core_logging}",core_logging,primary_region)
    update_alb_bucket_policy_secondary(s3,account_id,f"tlz-alb-access-central-secondary-{core_logging}",core_logging,secondary_region)


if __name__ == "__main__":
    from optparse import OptionParser
    import pprint
    import json
    import sys

    parser = OptionParser()
    parser.add_option("-a", "--account_number", dest="account_number", help="AccountNUmber to test")
    pp = pprint.PrettyPrinter(indent=4)
    (options, args) = parser.parse_args(sys.argv)
    #pp.pprint(options)
    event = { "AccountId": f"{options.account_number}"}
    lambda_handler(event,None)
