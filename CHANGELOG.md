
# Change Log

## [v0.1.3] - 09-11-2019
- CIRRUS-571: Adding the tlz_billing_admin role

## [v0.1.0] - 09-04-2019
- CIRRUS-606: Rewrite and initial refactor to centralize group permissions management across AVM resources.

## [v0.0.109] - 08-26-2019
- CIRRUS-616: Updated avm_create_workspaces to be more resilient

## [v0.0.108] - 08-26-2019
- CIRRUS-616: Updated avm_create_workspaces to be more resilient

## [v0.0.107] - 08-10-2019
- CIRRUS-616: Added avm_config table information to outputs

## [v0.0.106] - 08-10-2019
- CIRRUS-386: Updated layers to include get_all_accounts and updated initial assume_role_policy

## [v0.0.104] - 08-07-2019
- CIRRUS-336 Corrected account naming so okta would pick up network account

## [v0.0.102] - 08-06-2019
- CIRRUS-536 Add SMTP relay for shared svcs resources

## [v0.0.100] - 08-04-2019
- CIRRUS-554: removed extra function

## [v0.0.99] - 08-04-2019
- CIRRUS-554: fix to function calls

## [v0.0.98] - 08-04-2019
- CIRRUS-554: added a method to handle resource specific workspace creation

## [v0.0.97] - 08-01-2019
- CIRRUS-554: created a sandbox resources account template

## [v0.0.96] - 08-01-2019
- CIRRUS-554: added a terraform_service_user avm config parameter

## [v0.0.95] - 07-31-2019
- CIRRUS-554: changed to automation document naming

## [v0.0.94] - 07-31-2019
- CIRRUS-554: updated workspace names, update the sandbox automation document

## [v0.0.93] - 07-31-2019
- CIRRUS-554: Working on sandbox workspaces

## [v0.0.92] - 07-27-2019
- CIRRUS-561: Accounted for a restriction in redlock that required globally unique account names

## [v0.0.89] - 07-27-2019
- CIRRUS-425: Changed the okta group name for sandbox tlz_developer_RO  -> tlz_developer_ro match the role name

## [v0.0.88] - 07-27-2019
- CIRRUS-425: Changed the okta group name from tlz_developer_RO  -> tlz_developer_ro match the role name

## [v0.0.87] - 07-26-2019
- CIRRUS-476: Addressed the issue that guardduty master cannot send invites to itself
## [v0.0.86] - 07-25-2019

- CIRRUS-475: Updated the create okta groups logic to reflect current federated roles

## [v0.0.85] - 07-25-2019

- CIRRUS-475: CW destinations were re-named to use "_" instead of "-"

## [v0.0.75] - 07-16-2019

- CIRRUS-475: Updated the create_workspace lambda to tlz_org_account_access_role and role_name parameters to workspace

## [v0.0.74] - 07-16-2019

- CIRRUS-475: Added automation to create tlz-avm-automation role if does not exist

## [v0.0.73]
- CIRRUS-506: Added regions to the application resource workspace

## [v0.0.61]

- CIRRUS-506: Changed the app-resources template name from account-resources -> application-resources

## [v0.0.60]

- CIRRUS-506: Added new variables to app-resources workspace and fixed the git repo creation for app-resources

## [v0.0.59]
- Fixed the syntax error in the master lambda CIRRUS-506

## [v0.0.58]
- Fixed the syntax error in the master lambda CIRRUS-506

## [v0.0.57]
- Updated the create_git_repos and master lambdas to address the issues found in CIRRUS-506

## [v0.0.52]
- changes to allow for region to be driven by the account request form.

## [v0.0.51]
- allow VPC deletion for sandbox type accounts in lambda avm-vpc-defaultdelete.py.

## [v0.0.50]
- Adding in delete default VPC for sandbox.

## [v0.0.49]
- Updated the avm_master to create alias names with _ for core accounts
- Fixed a defect naming for application repos to use appropriate project

## [v0.0.48]
- Removed the hardcoded project names
- Verified that core accounts are vended correctly
- Updated the create_workspaces to use the appropriate okta ids to workspace

## [v0.0.42]
- added core-network to create-bitbucket fork function
## [v0.0.38]
- updated avm-create-bitbucket.py to utilize new repository names and bitbucket project codes

## [v0.0.36] - 2019-06-14
- CIRRUS-351: Changed the okta related TFE workspace variables to sensitive

## [v0.0.35] - 2019-06-13
- CIRRUS-351: Added varibales region_secondary,intEnvironment to tfe_workspaces lambda

## [v0.0.32] - 2019-06-10
- CIRRUS-351: Added okta_provider_domain and okta_app_id as TFE workspace variables

## [v0.0.31] - 2019-06-07
- Updated iam policy needed for avm_tfe_role used by lambdas
## [v0.0.30] - 2019-06-07
## Comments
- Tested CIRRUS-308 changes
## [v0.0.27] - 2019-06-04
## Comments
- Tested CIRRUS-310 incorporated the changes suggsted by PR: https://stash.ec2.local/projects/CPMR/repos/terraform-aws-avm/pull-requests/12/overview

## [v0.0.26] - 2019-06-04
## Comments
- Tested CIRRUS-310 with alb-logs, cloudtrail, config , guardduty and vpc-flowlogs

## [v0.0.27] - 2019-06-04

- Added lambdas for avm-dns-invites
- Updated delete vpcs
- Updated the create-git-repos tp account for application repos
- Updated the create-workspaces to account for application workspaces


## [v0.0.4] - 2019-05-22
## Added
- Removed the self reference

## [v0.0.2] - 2019-05-22
## Added
- Added lambda for creating the tfe workspaces to tlz-avm

## Changed
- Removed the defaults for subnet-ids, security-group variables


## [v0.0.1] - 2019-05-21
## Changed
- README.md : Updated the input paramaters
- avm-vpc-defaultdelete.py: Parameterized master-admin role
- lambdas.tf: Added delete-vpcs-lambda

### First Commit
Initial code checkin

The format is based on [Keep a Changelog][changelog] and this project adheres
to [Semantic Versioning][semver].

<!-- Links -->
[changelog]:http://keepachangelog.com
[semver]:http://semver.org
