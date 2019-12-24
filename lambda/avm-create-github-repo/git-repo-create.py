# List all baseline repos

import json
from jinja2 import Template
from github import Github
import avm_common

class gitMgr:
    """Class that manages access to git resources"""
    _git = NotImplementedError

    def __init__(self):
        self._token = self.get_token()
        secret = self._token
        print(secret)
        url = secret["url"]
        if "github.com" in secret["url"]:
            url = "https://api.github.com"
        else:
            url = f"{url}/api/v3"
        self._git = Github(base_url=url, login_or_token=secret["password"])
        #print(self._git)

    def get_token(self):
        return avm_common.get_secret("vcs")

    def get_org(self,org):
        return self._git.get_organization(org)

    def get_repo(self, org_name, repo_name):
        print(f"Getting repo: {org_name}/{repo_name} ")
        if org_name:
            org = self.get_org(org_name)
            all_repos = org.get_repos()
        else:
            all_repos = self._git.get_user().get_repos()
        for repo in all_repos:
            if repo.name == repo_name:
                #print(f"{repo.name} - {repo.organization} - {repo.git_url}")
                return repo
        return None

    def list_all_repos(self):
        count = 0
        for repo in self._git.get_user().get_repos():
            print(f"{repo.name}")
            #print(dir(repo))
            count = count + 1

        print(count)

    def create_a_empty_repo_in_org(self,org_name,repo_name):
        if org_name:
            org = self.get_org(org_name)
            repo = org.create_repo(repo_name)
        else:
            self._git.get_user().create_repo()
        return repo

    def get_account_baseline_version(self, repo):
        main_tf = repo.get_file_contents("main.tf")
        count = 0
        get_version = False
        version = None
        baseline_map = {
            "sandbox" : "baseline-sandbox",
            "baseline" : "account-baseline"
        }
        baseline_key = None
        for key in repo.name.split("-"):
            if key in baseline_map.keys():
                baseline_key = baseline_map[key]
                break
        #print(baseline_key)
        decoded_txt = main_tf.decoded_content.decode('utf-8')
        for l in decoded_txt.split("\n"):
            count = count + 1
            print(f"[{count}] : {l}")
            if baseline_key in l:
                get_version = True
            if "version" in l and get_version:
                version = l.split("=")[-1]
                version = version.replace('"','').replace("\r","")
                return version
        return version

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

    def clone_repo(self,org_name,repo_name, template, account_id, additional_info):
        # Steps
        #  1. Check if repo exists
        #  2. Create an empty repo if not exist
        repo = self.get_repo(org_name,repo_name)
        target_repo = None
        is_new_repo = False
        if not repo:
            print(f"Create a new repo {repo_name}")
            target_repo = self.create_a_empty_repo_in_org(org_name,repo_name)
            is_new_repo = True
        else:
            #print(repos)
            target_repo = repo
        # 3. Iterate the template repo
        # 4. Add every object in template to new repo
        repo = self.get_repo("tlz-at",template)
        print(repo)
        contents = repo.get_contents("")
        if target_repo != None and is_new_repo == True:
            while len(contents) > 0:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    #print(file_content)
                    updated_content = self.parse_contents_using_jina(file_content.decoded_content.decode('utf-8'),account_id,repo_name,additional_info)
                    #print(file_content.decoded_content.decode('utf-8'))
                    target_repo.update_file(file_content.path, f"Baseline - added {file_content.path}", updated_content,file_content.sha)

    def parse_contents_using_jina(self, content, accountId,repoName, additional_info):
        jinja_vars = {
            "AccountId": accountId,
            "RepoName": repoName,
            "AccountName": additional_info["org_details"]["alias"],
            "AccountType": additional_info["org_details"]["accountType"],
            "AccountOrg": additional_info["org_details"]["org_name"],
            #"Owner": additional_info["owner"],
            #"Environment": additional_info["environment"],
            #"intEnvironment": additional_info["intEnvironment"],
            "primaryVpcCidr": additional_info["request_details"]["primaryVpcCidr"],
            "secondaryVpcCidr": additional_info["request_details"]["secondaryVpcCidr"]
        }
        t = Template(content)
        return t.render(jinja_vars)


def lambda_handler(event, context):
    repo_name = None
    account_Id = event["AccountId"]
    account_info = avm_common.get_account_details(account_Id)
    account_details = account_info["org_details"]
    #pp.pprint(account_details)
    #pp.pprint(account_info)
    baseline_details = json.loads(account_details["baseline_details"])
    account_type  = account_details["accountType"]

    baseline_repo = baseline_details["git"]

    repo_name = baseline_repo.split("/")[-1].replace(".git","")

    ## Might want to make this a global variable
    vended_baselines_project = avm_common.get_param("vended_baselines_project")
    print(vended_baselines_project)
    git = gitMgr()
    template = git.get_baseline_template_repo(repo_name)
    print(f"Template: {template}")
    print(f"Repo to create : {repo_name}")

    #git.list_all_repos()
    # Create baseline repo
    git.clone_repo(vended_baselines_project, repo_name, template, account_Id, account_info)

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
        git.clone_repo(vended_applications_project, repo_name, template, account_Id, account_info)


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
