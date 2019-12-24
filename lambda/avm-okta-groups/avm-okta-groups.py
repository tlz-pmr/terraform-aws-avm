import boto3
import base64
from botocore.exceptions import ClientError
import json
import avm_common
import requests
from http import HTTPStatus

okta_config = avm_common.get_secret("okta")
url = okta_config["url"]

# Checks if Group already exists
def get_group_id(group_name,secret):
    print(f"Checking group {group_name}")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "SSWS " + secret
    }
    # check if group already exists
    response = requests.get(url + "/api/v1/groups", headers=headers)
    response = json.loads(response.text)

    for group in response:
        if(group["profile"]["name"] == group_name):
            #print(group)
            print(group_name + " already exists")
            return group["id"]
    print(group_name + " does not exist. Creating.")
    return None

# Creates group and returns Group ID
def create_group(group_name,secret):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "SSWS " + secret
    }
    body = {
        "profile": {
            "name": group_name,
            "description": group_name + " GROUP"
        }
    }
    response = requests.post(url + "/api/v1/groups", headers=headers, json=body)
    group_id = requests.get(url + "/api/v1/groups?q=" + group_name, headers=headers)
    group_id = json.loads(group_id.text)
    return str(group_id[0]["id"])

# Assigns Group ID to App ID 
def assign_group_app(group_id, app_id, secret):
    print(f"Attaching {group_id} with {app_id}")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "SSWS " + secret
    }
    response = requests.put(url + "/api/v1/apps/" + app_id + "/groups/" + group_id, headers=headers)
    #print(response.text)
    return response.status_code

    
def get_user_id(principal_email, secret):
    print(f"Checking user {principal_email}")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "SSWS " + secret
    }
    # Check if the user already exists.
    # NOTE: We do not *create* any user principals.  If the user is not found,
    # this is a failure condition resulting in no user being added.
    response = requests.get(url + f"/api/v1/users/{principal_email}", headers=headers)
    response = json.loads(response.text)
    
    # Compare the emails for a match.
    try:
        if (response["profile"]["email"].lower() == principal_email):
            print("User found")
            return response["id"]
        else:
            # This should be *highly* improbable, but just in case...
            print("Okta user found, but with email/login mismatch!")
            return None
    except:
        # If nothing was found the response will be an error JSON.
        print(principal_email + " was not found in Okta!")
        return None
        
# Assigns user ID to given group.
def assign_user_group(user_id, group_id, secret):
    print(f"Assigning {user_id} to {group_id}...")
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "SSWS " + secret
    }
    response = requests.put(url + "/api/v1/groups/" + group_id + "/users/" + user_id, headers=headers)
    #print(response.text)
    return response.status_code

def lambda_handler(event, context):
    try:
        account_id = event["AccountId"]
        sns_topic = avm_common.get_param("sns_topic_arn")
        sub  = "ERROR: okta create groups"
        func = "avm-okta-create-groups"
        lambda_handler_inner(event, context)
    except ClientError as e:
        body = f"Unexpected error : {e}"
        print(body)
        avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)
        raise e
    except Exception as e:
        body = f"Unexpected error : {e}"
        print(body)
        avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)
        raise e

def lambda_handler_inner(event, context): 
    account_id = event["AccountId"]
    account_info = avm_common.get_account_details(account_id)
    account_details = account_info["org_details"]
    account_contact_email = account_info["request_details"]["accountEmail"].lower()
    #print(account_details)
    account_type = account_details["accountType"].lower()
    try:
        environment_type = json.loads(account_details["account_request"])
        environment_type = environment_type["intEnvironment"].lower()
    except Exception:
        environment_type = "null"

    # Assuming a group was created, attach the contact email address to the admin group.  This involves:
    #   - Determining the principal ID for the corresponding email address
    #   - Adding that principal to each group that makes sense
    secret = okta_config["token"]
    account_contact_userid = get_user_id(account_contact_email, secret)

    group_names = avm_common.generate_okta_group_names(event["AccountId"], account_type, environment_type, account_details["alias"].lower())
    for group_name in group_names:
        print(group_name)
        group_id = get_group_id(group_name, secret)
        print(f"GroupId : {group_id}")
        if not group_id:
            group_id = create_group(group_name, secret)
            print("Group ID is " + group_id + "\nAttaching Apps " + account_type + " to new Group ID.")
        else:
            print("Group ID is " + group_id + "\nAttaching Apps " + account_type + " to new Group ID" + "env_type:" + environment_type )
        
        # If the group name happens to be the 'admin' role name, and there is a user_id to attach, do so:
        # (NOTE: This 'in' test is a little loose for e.g. 'tlz_developer' vs. 'tlz_developer_ro', but for 'tlz_admin' it is fine. )
        if ((group_name.endswith(avm_common.get_delegated_admin_role())) and account_contact_userid):
            if (assign_user_group(account_contact_userid, group_id, secret) == HTTPStatus.OK):
                print("Successfully attached contact email to group...")
            else:
                print("Unable to attach contact email to group (invalid, non-matching, or a DL?)...")


        # Assign the group to app
        app_resp = None
        account_code = avm_common.get_short_account_code(account_type, environment_type)
        app_resp = assign_group_app(group_id, okta_config[account_code + "_APP_ID"], secret)
        if (app_resp == HTTPStatus.OK):
            print("Successfully attached App to Group ID")
        else:
            print("Failed to attach App to Group ID.")


if __name__ == "__main__":
    from optparse import OptionParser
    import pprint
    import json
    import sys

    parser = OptionParser()
    parser.add_option("-a", "--account_number", dest="account_number", help="Account Number to test")
    pp = pprint.PrettyPrinter(indent=4)
    (options, args) = parser.parse_args(sys.argv)
    pp.pprint(options)
    event = { "AccountId": f"{options.account_number}"}
    lambda_handler(event,None)
