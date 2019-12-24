import json
import stashy
import avm_common
import urllib3
import boto3
import base64
from botocore.exceptions import ClientError

urllib3.disable_warnings()
# import pprint
# pp = pprint.PrettyPrinter(indent=4)


class gitMgr:
    """Class that manages access to bitbucket resources"""

    def __init__(self):
        self._token = self.get_token()
        secret = self._token
        self._stashy = stashy.connect(secret["url"],secret["user"], secret["password"], verify=False)

    def get_token(self):
        return avm_common.get_secret("bitbucket")

    def get_repo(self, repo_name,project=None):
        print(f"Get the repo {repo_name} in project {project}")
        import inspect
        try:

            if project:
                repos = [r for r in self._stashy.repos.all() if (r["name"] == repo_name and r["project"]["key"] == project)]
                for r in repos:
                    print(f'{r["project"]["key"]}')

                if len(repos) == 1:
                    print(f"Trying to find {repo_name} in {project}")
                    repo = self._stashy.projects[project].repos[repo_name]
                    #pp.pprint(inspect.getmembers(repo))
                    return repo
            else:
                repos = [r for r in self._stashy.repos.all() if r["name"] == repo_name ]
                if len(repos) == 1:
                    project = repos[0]["project"]["key"]
                    print(f"Found {project}/{repo_name}")
                    return self._stashy.projects[project].repos[repo_name]
                else:
                    return
        except:
            raise

    def get_baseline_template_repo(self, repo_name):
        print("starting get_baseline_template_repo function...")
        baseline_map = {
            "sandbox" : "sandbox-account",
            "core_master_payer" : "core-master-payer",
            "core_logging" : "core-logging",
            "core_security" : "core-security",
            "core_shared_services" : "core-shared-services",
            "core_network" : "core-network",
            "baseline" : "application-account",
            "app" : "application-account"

        }
        baseline_key = None
        for key in repo_name.split("-"):
            if key in baseline_map.keys():
                baseline_key = baseline_map[key]
                break

        return baseline_key

    def fork_repo(self,source_repo_name,target_project,target_repo_name):
        print("starting clone_repo function...")
        # Steps
        #  1. Check if repo exists
        target_repo = self.get_repo(target_repo_name,target_project)
        print(target_repo)
        if not target_repo:
            templates_project = avm_common.get_param("project_for_templates")
            src_repo = self.get_repo(source_repo_name, templates_project)
            if src_repo:
                print(f"Create a new repo {target_repo_name} in {target_project}")
                try:
                    response = src_repo.fork(target_repo_name,target_project)
                    return response
                except stashy.errors.GenericException as e:
                    raise e
            else:
                print(f"{source_repo_name} repo not found")
        else:
            print(f"{target_repo_name} repo already exists. Nothing to fork")

    def create_group(self, group):
        """Create a group in Bitbucket using the Stashy API."""
        try:
            return self._stashy.admin.groups.add(group)
        except stashy.errors.GenericException as e:
            # Does the group already exist (409)?
            # Stashy can't handle it, so do it explicitly:
            msg = e.data["errors"][0]["exceptionName"]
            if (msg == "com.atlassian.bitbucket.IntegrityException"):
                print(f"Group {group} already exists, not creating...")
            else:
                raise e

    def grant_repository_access(self, project, repository, group, permission):
        """Grant a group access to a repository."""
        try:
            return self._stashy.projects[project].repos[repository].permissions.groups.grant(group, permission)
        except stashy.errors.GenericException as e:
            raise e

def get_repository_access_for_role(role_name, repository_type):
    """Return a Bitbucket permission level for a *role* (not a team) to a particular repository."""
    access_for_roles = {
        "tlz_admin": {
            "baseline": "REPO_WRITE",
            "resource": "REPO_ADMIN"
        },
        "tlz_developer": {
            "baseline": "REPO_WRITE",
            "resource": "REPO_WRITE"
        },
        "tlz_developer_ro": {
            "baseline": "REPO_READ",
            "resource": "REPO_READ"            
        }
    }
    try:
        return access_for_roles[role_name][repository_type]
    except KeyError:
        return None

def lambda_handler(event, context):
    repo_name = None
    account_Id = event["AccountId"]
    account_info = avm_common.get_account_details(account_Id)
    account_details = account_info["org_details"]
    #pp.pprint(account_details)
    baseline_details = json.loads(account_details["baseline_details"])
    account_type  = account_details["accountType"]

    baseline_repo = baseline_details["git"]

    repo_name = baseline_repo.split("/")[-1].replace(".git","")
    print(repo_name)
    ## Might want to make this a global variable
    vended_baselines_project = avm_common.get_param("vended_baselines_project")
    #project = "tlz-vb"
    #pp.pprint(project.upper())

    git = gitMgr()
    template = git.get_baseline_template_repo(repo_name)
    print(template)
    # Create baseline repo
    git.fork_repo(template,vended_baselines_project.upper(),repo_name)

    #print(account_details)
    try:
        account_request = json.loads(account_details["account_request"])
        environment_type = account_request["intEnvironment"].lower()
    except Exception:
        environment_type = "null"

    user_managed_roles = avm_common.get_delegated_user_managed_roles()
    group_list = avm_common.generate_okta_group_names(account_Id, account_type, environment_type, account_details["alias"].lower())
    
    for group in group_list:
        for role in user_managed_roles:
            if group.endswith(role):
                print(f"Group to be granted permissions to Bitbucket baseline repo: {group}")
                git.create_group(group)
                git.grant_repository_access(vended_baselines_project.upper(), repo_name, group, get_repository_access_for_role(role, "baseline"))
                # TODO: Add merge check restriction

    if avm_common.resource_workspace_required(account_type):
        # Create an additional repo for the application and sandbox
        # app-repo template
        app_details = json.loads(account_details["app_details"])
        print("App details")
        print(app_details)
        app_repo = app_details["git"]
        repo_name = app_repo.split("/")[-1].replace(".git","")
        print(repo_name)
        vended_applications_project = avm_common.get_param("vended_applications_project")
        template = f"{account_type.lower()}-resources"
        git.fork_repo(template,vended_applications_project.upper(),repo_name)

        for group in group_list:
            for role in user_managed_roles:
                if group.endswith(role):
                    print(f"Group to be granted permissions to Bitbucket resource repo: {group}")
                    git.grant_repository_access(vended_applications_project.upper(), repo_name, group, get_repository_access_for_role(role, "resource"))

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
