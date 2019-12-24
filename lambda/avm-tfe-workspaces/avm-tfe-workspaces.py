# -*- coding: utf-8 -*-
import json
import boto3
import base64
import requests
import avm_common
from botocore.exceptions import ClientError
#import pprint

org = avm_common.get_param("tfe_org_name")
tfe_api = avm_common.get_param("tfe_api_url")
print(f"{tfe_api}/{org}")
#pp = pprint.PrettyPrinter(indent=4)
# AWS Lambda Handler
def lambda_handler(event, context):
    try:
        account_id = event["AccountId"]
        handler_inner(event, context)
    except ClientError as e:
        body = f"Unexpected error : {e}"
        print(body)
        sns_topic = avm_common.get_param("sns_topic_arn")
        print(sns_topic)
        print(account_id)
        sub  = "ERROR: TFE Create Workspaces"
        func = "avm-tfe-create-workspaces"
        avm_common.send_pipeline_notification(account_id,sns_topic,func, sub,body)
        raise e

def handler_inner(event, context):
    account_id = event["AccountId"]
    # Retrieve secrets from AWS Secrets Manager
    aws_secrets = avm_common.get_secret("tfe_aws_keys")
    # Look these single values up directly:
    tfe_key = avm_common.get_secret("terraform")["terraform"]
    vcs_oauth_token = avm_common.get_secret("vcs_oauth_token")["oauth_token"]

    # Get workspace name from dynamodb from event.accountId
    # Grab account details
    account_info = avm_common.get_account_details(account_id)
    #pp.pprint(account_info)
    account_details = account_info["org_details"]
    request_details = account_info["request_details"]
    #print(account_details)

    # Defines both repository names from account_details data
    baseline_details = json.loads(account_details["baseline_details"])
    account_request = json.loads(account_details["account_request"])
    print(baseline_details)
    baseline_repo_concat =  "/".join(baseline_details["git"].split('/')[3:]).replace('.git','')
    ws_name = baseline_details["tfe_workspace"]
    # instantiates workspace creation for baseline & application workspaces
    workspace_id = create_workspace(ws_name, tfe_key, vcs_oauth_token, baseline_repo_concat)
    if not workspace_id:
        return None
    #workspace_id = get_workspace(ws_name, tfe_key)

    # okta variables
    okta_account_type = account_details["accountType"].lower()

    try:
        account_request = json.loads(account_details["account_request"])
        environment_type = account_request["intEnvironment"].lower()
        okta_account_type = f"{okta_account_type}_{environment_type}"
    except Exception:
        environment_type = "NA"

    primary_region, secondary_region = avm_common.get_regions(account_id)
    azs_primary, azs_secondary = avm_common.az_map_by_region(primary_region)

    okta_config = avm_common.get_secret("okta")

    okta_app_id_index = {
        "core" : okta_config["COR_LINK_ID"],
        "sandbox" : okta_config["SBX_LINK_ID"],
        "application_npd" : okta_config["NPD_LINK_ID"],
        "application_prd" :  okta_config["PRD_LINK_ID"]
    }

    okta_url = okta_config["url"].replace("https://","")
    okta_prefix = "aws" + avm_common.get_short_account_code(okta_account_type, environment_type)

    tfe_host_name = avm_common.get_param("tfe_api_url").replace("https://","").replace("/api/v2","")
    workspace_vars = [
        {"key" : "AWS_ACCESS_KEY_ID", "value": aws_secrets["AWS_ACCESS_KEY_ID"], "category": "env","sensitive": False, "hcl":False},
        {"key" : "AWS_SECRET_ACCESS_KEY", "value": aws_secrets["AWS_SECRET_ACCESS_KEY"], "category": "env","sensitive": True, "hcl":False },
        {"key" : "account_id", "value": account_id, "category": "terraform","sensitive": False, "hcl":False },
        {"key" : "repo_name", "value": baseline_repo_concat, "category": "terraform","sensitive": False, "hcl":False },
        {"key" : "name", "value": account_details["name"].lower(), "category": "terraform","sensitive": False, "hcl":False },
        {"key" : "account_type", "value": account_details["accountType"].lower(), "category": "terraform","sensitive": False, "hcl":False },
        {"key" : "account_org", "value": account_details["org_name"].lower(), "category": "terraform","sensitive": False, "hcl":False },
        {"key" : "owner", "value": account_details["email"], "category": "terraform","sensitive": False, "hcl":False },
        {"key" : "environment", "value": account_request["env"].lower(), "category": "terraform","sensitive": True, "hcl":False },
        {"key" : "int_environment", "value": environment_type, "category": "terraform","sensitive": False, "hcl":False },
        {"key" : "cidr_primary", "value": request_details["primaryVpcCidr"], "category":"terraform", "sensitive":False, "hcl":False },
        {"key" : "cidr_secondary", "value": request_details["secondaryVpcCidr"], "category":"terraform", "sensitive":False, "hcl":False },
        {"key" : "region_primary", "value": primary_region, "category":"terraform", "sensitive": False, "hcl":False },
        {"key" : "region_secondary", "value": secondary_region, "category":"terraform", "sensitive": False, "hcl":False },
        {"key" : "azs_primary", "value": azs_primary, "category":"terraform", "sensitive": False, "hcl": True },
        {"key" : "azs_secondary", "value": azs_secondary, "category":"terraform","sensitive": False, "hcl": True },
        {"key" : "okta_provider_domain", "value": okta_url, "category": "terraform","sensitive": False, "hcl":False },
        {"key" : "okta_app_id", "value": okta_app_id_index[okta_account_type] , "category": "terraform","sensitive": False, "hcl":False },
        {"key" : "tfe_org_name", "value": avm_common.get_param("tfe_org_name") , "category": "terraform","sensitive": True, "hcl":False },
        {"key" : "tfe_avm_workspace_name", "value": avm_common.get_param("avm_workspace_name") , "category": "terraform","sensitive": True, "hcl":False },
        {"key" : "tfe_host_name", "value": tfe_host_name, "category": "terraform","sensitive": True, "hcl":False },
        {"key" : "tfe_core_logging_workspace_name", "value": avm_common.get_param("logging_workspace_name") , "category": "terraform","sensitive": True, "hcl":False },
        {"key" : "master_payer_org_id", "value": avm_common.get_param("master_payer_org_id") , "category": "terraform","sensitive": True, "hcl":False },
        {"key" : "master_payer_account", "value": avm_common.get_param("master_payer_account"), "category": "terraform","sensitive": True, "hcl":False },
        {"key" : "core_security_account", "value": avm_common.get_param("core_security_account") , "category": "terraform","sensitive": True, "hcl":False },
        {"key" : "tlz_org_account_access_role", "value": avm_common.get_param("tlz_org_account_access_role") , "category": "terraform","sensitive": True, "hcl":False },
        {"key" : "role_name", "value": avm_common.get_param("tlz_admin_role") , "category": "terraform","sensitive": True, "hcl":False },
        {"key" : "okta_token", "value": okta_config["token"], "category": "terraform","sensitive": True, "hcl":False}
    ]

    for var in workspace_vars:
        print(f"Attaching the var {var['key']}")
        response = attach_vars_to_workspace(ws_name, tfe_key, var["key"], var["value"], var["category"], var["sensitive"], var["hcl"])

    # Make teams with the same name as the Okta role names and assign them privileges to the baseline and resources workspaces.
    # This will be reused in the resources workspace block later.
    user_teams_to_assign = avm_common.get_delegated_user_managed_roles()
    group_list = avm_common.generate_okta_group_names(account_id, okta_account_type, environment_type, account_details["alias"].lower())

    for team in group_list:
        for role in user_teams_to_assign:
            if team.endswith(role):
                # Try to find it first:
                team_id = get_team(tfe_key, team)
                # Otherwise, create it:
                if not team_id:
                    team_id = create_team_for_org(tfe_key, team)

                assign_team_to_workspace(tfe_key, team_id, workspace_id, get_workspace_access_for_role(role, "baseline"))
    
    print(baseline_repo_concat)

    # Add network_account
    core_network_account = avm_common.get_param("core_network_account")
    if core_network_account != None:
        if account_details["accountType"].lower() in ["application"] or (account_details["accountType"].lower() == "core" and account_request["account_name"].lower() == "shared_services"):
            attach_vars_to_workspace(ws_name,tfe_key,"core_network_account",core_network_account,"terraform",False,False)
        


    if avm_common.resource_workspace_required(account_details["accountType"]):
        app_details = json.loads(account_details["app_details"])
        app_repo_concat = "/".join(app_details["git"].split('/')[4:]).replace('.git','')
        baseline_workspace_name = ws_name
        ws_name = app_details["tfe_workspace"]
        create_workspace(ws_name, tfe_key, vcs_oauth_token, app_repo_concat)
        workspace_id = get_workspace(ws_name, tfe_key)        
        print(app_repo_concat)
        workspace_vars = [
            {"key" : "tfe_host_name", "value": tfe_host_name, "category": "terraform","sensitive": True, "hcl":False },
            {"key" : "tfe_org_name", "value": avm_common.get_param("tfe_org_name") , "category": "terraform","sensitive": True, "hcl":False },
            {"key" : "name", "value": account_details["name"].lower(), "category": "terraform","sensitive": False, "hcl":False },
            {"key" : "owner", "value": account_details["email"], "category": "terraform","sensitive": False, "hcl":False },
            {"key" : "environment", "value": account_request["env"].lower(), "category": "terraform","sensitive": True, "hcl":False },
            {"key" : "baseline_workspace_name", "value": baseline_workspace_name , "category": "terraform","sensitive": True, "hcl":False },
            {"key" : "region_primary", "value": primary_region, "category":"terraform", "sensitive": False, "hcl":False },
            {"key" : "region_secondary", "value": secondary_region, "category":"terraform", "sensitive": False, "hcl":False },
            {"key" : "baseline_workspace_name", "value": baseline_workspace_name , "category": "terraform","sensitive": True, "hcl":False },
            {"key" : "tlz_org_account_access_role", "value": avm_common.get_param("tlz_org_account_access_role") , "category": "terraform","sensitive": True, "hcl":False },
            {"key" : "role_name", "value": avm_common.get_param("tlz_admin_role") , "category": "terraform","sensitive": True, "hcl":False }
        ]

        for var in workspace_vars:
            print(f"Attaching the var {var['key']}")
            response = attach_vars_to_workspace(ws_name, tfe_key, var["key"], var["value"], var["category"], var["sensitive"], var["hcl"])
    
        # Assign the teams (already created in the baseline block) to this workspace as well.
        for team in group_list:
            for role in user_teams_to_assign:
                if team.endswith(role):
                    # Get the team ID--it was made in the baseline already.
                    team_id = get_team(tfe_key, team)
                    assign_team_to_workspace(tfe_key, team_id, workspace_id, get_workspace_access_for_role(role, "resource"))

    elif account_details["accountType"].lower() == "core" and account_request["account_name"].lower() == "shared_services":
        workspace_vars = [
            {"key" : "primary_zone_name", "value": avm_common.get_param("primary_zone_name") , "category": "terraform","sensitive": False, "hcl":False }
        ]

        for var in workspace_vars:
            print(f"Attaching the var {var['key']}")
            response = attach_vars_to_workspace(ws_name, tfe_key, var["key"], var["value"], var["category"], var["sensitive"], var["hcl"])

def explode_ghe_url(github_repo):
    return github_repo.split('/')[3:]

def get_workspace_access_for_role(role_name, workspace_type):
    """Return a TFE permission level for a *role* (not a team) to a particular workspace."""
    access_for_roles = {
        "tlz_admin": {
            "baseline": "read",
            "resource": "write"
        },
        "tlz_developer": {
            "baseline": "read",
            "resource": "plan"
        },
        "tlz_developer_ro": {
            "baseline": "read",
            "resource": "read"            
        }
    }
    try:
        return access_for_roles[role_name][workspace_type]
    except KeyError:
        return None

def get_default_headers(token=None):
    """Provide a default TFE API call request header."""
    return {
            "content-type": "application/vnd.api+json",
            "authorization": f"Bearer {token}"
        }

# Retrieves tfe workspace id
def get_workspace(workspace_name, tfe_secret, headers = None):
    """Retrieve the first matching TFE workspace ID for the given organization."""

    print("Entered get_workspace...")
    if not headers:
        print("Headers were not provided, supplying defaults...")
        headers = get_default_headers(tfe_secret)
    
    tfe_url = f'{tfe_api}/organizations/{org}/workspaces/{workspace_name}'

    #print(tfe_url)

    r = requests.get(tfe_url, headers=headers)
    #print(r.json())
    data = r.json()
    if "data" in data.keys():
        if "id" in data["data"].keys():
            return data["data"]["id"]
    return None

# function that delivers payload to tfe for workspaces to be created
def create_workspace(ws_name, tfe_secret, vcs_oauthToken, repository):
    """Create a workspace in the default TFE organization."""
    workspace_id = get_workspace(ws_name, tfe_secret)
    if workspace_id:
        return workspace_id
    print(f"Inputs: WS: {ws_name}, secret: {tfe_secret}, repo: {repository}, token : {vcs_oauthToken}")
    headers = get_default_headers(tfe_secret)
    payload = {
        "data": {
            "attributes": {
                "name": ws_name,
                "terraform-version": "0.11.14",
                "working_directory": "",
                "vcs-repo": {
                        "identifier": repository,
                        "oauth-token-id": vcs_oauthToken,
                        "branch": "",
                        "ingress-submodules": True,
                        "default-branch": "true"
                }
            },
            "type": "workspaces"
        }
    }
    print("Headers")
    print(headers)
    print("Payload")
    print(payload)
    print("create workspace")
    workspace = requests.post(
        f"{tfe_api}/organizations/{org}/workspaces", data=json.dumps(payload), headers=headers)
    print("end workspace create")
    print(workspace.json())
    if "data" in workspace.json().keys():
        if "id" in workspace.json()["data"].keys():
            return workspace.json()["data"]["id"]
    return None

def get_team(tfe_secret, team_name, org_name=org):
    """Retrieve a team ID for an named team in a TFE organization."""
    headers = get_default_headers(tfe_secret)

    tfe_url = f'{tfe_api}/organizations/{org}/teams'
    print("Team : {team_name}")

    print(tfe_url)

    r = requests.get(tfe_url, headers=headers)
    data = r.json()
    print(data)
    try:
        for team in data["data"]:
            if (team["attributes"]["name"] == team_name):
                return team["id"]
    # Just in case...
    except:
        return None

    return None

def create_team_for_org(tfe_secret, team_name, org_name=org):
    """Create a team in the given TFE organization and return its ID."""
    headers = get_default_headers(tfe_secret)

    payload = {
        "data": {
            "type": "teams",
            "attributes": {
                "name": team_name,
                "organization-access": {
                        "manage-policies": False,
                        "manage-workspaces": False,
                        "manage-vcs-settings": False
                }
            }
        }
    }

    team = requests.post(
        f"{tfe_api}/organizations/{org_name}/teams", data=json.dumps(payload), headers=headers)
    data = team.json()
    # print(data)
    team_id = data["data"]["id"]
    return team_id

def assign_team_to_workspace(tfe_secret, team_id, workspace_id, access_level):
    """Assign a team ID to a given TFE workspace ID with an access level (one of read, plan, write, or admin)."""

    if not access_level:
        return None

    headers = get_default_headers(tfe_secret)
    
    payload = {
        "data": {
            "type": "team-workspaces",
            "attributes": {
                "access": access_level
            },
            "relationships": {
                "workspace": {
                    "data": {
                        "type": "workspaces",
                        "id": workspace_id
                    }
                },
                "team": {
                    "data": {
                        "type": "teams",
                        "id": team_id
                    }
                }
            }
        }
    }

    print(f"Calling /team-workspaces to assign team ID {team_id} to workspace {workspace_id} with access {access_level}...")
    team = requests.post(
        f"{tfe_api}/team-workspaces", data=json.dumps(payload), headers=headers)
    print(team.json(), "End assign_team_to_workspace")
    

def attach_vars_to_workspace(workspace_name, tfe_secret, key, value, category="terraform", sensitive=False, hcl=False):
    """Add a single variable to a TFE workspace."""

    headers = get_default_headers(tfe_secret)
    workspace_id = get_workspace(workspace_name, tfe_secret, headers)
    payload_var = {
        "data": {
            "type": "vars",
            "attributes": {
                "key": key,
                "value": value,
                "category": category,
                "hcl": hcl,
                "sensitive": sensitive
            },
            "relationships": {
                "workspace": {
                    "data": {
                        "id": workspace_id,
                        "type": "workspaces"
                    }
                }
            }
        }
    }
    print(f"Attaching variable {key} to {workspace_name}")
    response = requests.post(f"{tfe_api}/vars", data=json.dumps(payload_var), headers=headers)
    return response

if __name__ == "__main__":
    from optparse import OptionParser
    import pprint
    import json
    import sys

    parser = OptionParser()
    parser.add_option("-a", "--account_number", dest="account_number", help="Account number to test")
    pp = pprint.PrettyPrinter(indent=4)
    (options, args) = parser.parse_args(sys.argv)
    pp.pprint(options)
    event = { "AccountId": f"{options.account_number}"}
    lambda_handler(event,None)
