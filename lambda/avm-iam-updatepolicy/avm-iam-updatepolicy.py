import boto3
import json
import avm_common
from botocore.exceptions import ClientError



def lambda_handler(event, context):
    try:
        account_id = event["AccountId"]
        lambda_handler_inner(event, context)
    except ClientError as e:
        body = f"Unexpected error : {e}"
        sns_topic = avm_common.get_param("sns_topic_arn")
        sub  = "ERROR: Managed policy update"
        func = "avm-iam-managedpolicy-update-for-new-account"
        avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)
        raise e
 

def lambda_handler_inner(event, context):
    session_assumed = avm_common.aws_session(role=None, session_name='logging-services')
    account_id = event["AccountId"]
    iamclient = session_assumed.client('iam')
    iamresource = session_assumed.resource('iam')
    current_account = session_assumed.client('sts').get_caller_identity().get('Account')
    
    POLICY_ARN_AVM=f"arn:aws:iam::{current_account}:policy/tlz_accounts_assumerole_policy"
    versionid = iamclient.get_policy(PolicyArn=POLICY_ARN_AVM)
    versionid1 = versionid["Policy"]["DefaultVersionId"][1:]
    previousversion = int(versionid1)-1
    versiondelete = "v" + str(previousversion)

    # Update a new version of the specified managed policy and set as Default
    policy = iamresource.Policy(POLICY_ARN_AVM)
    version = policy.default_version
    policyJson = version.document
    #policy = json.loads(policyJson)

    #print()
    resources = policyJson['Statement'][0]['Resource']
    master_role =  avm_common.get_param("tlz_admin_role")
    new_policy = f'arn:aws:iam::{account_id}:role/{master_role}'
    if new_policy not in resources:
        print(f"Adding {account_id} to policy resources")
        policyJson['Statement'][0]['Resource'].append(new_policy)
        policystring = json.dumps(policyJson)
        print(policystring)
        if previousversion > 0:
            deleteresponse = iamclient.delete_policy_version(PolicyArn=POLICY_ARN_AVM,VersionId=versiondelete)
            print(deleteresponse)
        policy_version = policy.create_version(PolicyDocument=policystring,SetAsDefault=True)
        print(policy_version)
    else:
        print(f"{account_id} is already part of existing resources")

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
