Overview
--------
This module provides a details how TLZ-AVM adds a new AWS account and brings the AWS account



Process
-------
Once Cloud Account Request is approved, CloudOps team receives an servicenow REQ with all the needed inputs for webform which is hosted in S3.Creation of the Account uses AWS SSM, Lambda, S3, IAM Roles and TFE.

The AVM pipeline is made up of the following steps:

1. Fill the required details in Account creation webform and submits the request.
2. On submit the web form,  data is inserted to DynamoDB  table named OrgAccountRequest.
3. Lambda function avm-master-respond-to-account-creation is invoked on insert to OrgAccountRequest dynamodb table.
4. The above lambda query the AWS organizations with the given email-id, if there is no matching AWS account found, it calls the ssm-automation-document **tlz-avm-ssm-document**.
5. master lambda **avm-master-respond-to-account-creation** also writes the data into OrgDetails table with accountid and with few other items.
6. tlz-avm-ssm-document SSM document has a branching logic which defines the dynamic Automation workflow that evaluates different choices based on web form inputs and it will execute either **app account type** or **sandbox account type** SSM document steps.
7. SSM document has a series of below lamba functions which will bring the AWS account to your organizations compliance standards.

 
Usage
-----
The module expects the following inputs and returns listed outputs

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|:----:|:-----:|:-----:|
| avm\_activity\_sns\_subscribers | Emails of avm\_activity\_sns\_subscribers | string | n/a | yes |
| avm\_workspace\_name | Name of the PTFE workspace the AVM will be deployed through | string | `"AVM"` | no |
| core\_logging\_account | AccountID of core-logging account | string | n/a | yes |
| core\_security\_account | AccountID of core\_security account | string | n/a | yes |
| core\_shared\_services\_account | AccountID of shared-services account | string | n/a | yes |
| logging\_workspace\_name | Name of the PTFE workspace the Logging account will be deployed through | string | `"core_logging"` | no |
| master\_payer\_account | AccountID of master\_payer account | string | n/a | yes |
| master\_payer\_org\_id | Organization ID for the organization in the master payer account | string | n/a | yes |
| memory\_size | Timeout value for Lambda function | string | `"150"` | no |
| post\_account\_sender\_email | Email id of post\_account\_sender\_email | string | n/a | yes |
| post\_account\_subscriber\_emails | Email ids of post\_account\_subscriber\_emails | string | n/a | yes |
| project | Project name to tag TLZ resources with | string | `"TLZ"` | no |
| project\_for\_templates | Bitbucket project where the account templates can be found | string | `"TLZ-AT"` | no |
| runtime | Runtime of Lambda function | string | `"python3.7"` | no |
| secondary\_region | Secondary region for accounts that may need it | string | `"us-east-1"` | no |
| security-data\_sensitivity | Data sensitivity classification to tag TLZ resources with | string | `"Confidential"` | no |
| security\_group\_ids | security\_group\_ids used by lambdas that call GHE and TFE | list | n/a | yes |
| stack | Stack name to tag TLZ resources with | string | `"TLZ"` | no |
| stack-builder | Tag value denoting what tool is building TLZ resources | string | `"Terraform"` | no |
| stack-env | Environment type to tag TLZ resources with | string | n/a | yes |
| stack-env-chg\_control | Change control classification to tag TLZ resources with | string | `"true"` | no |
| stack-lifecycle | Lifecycle classification to tag TLZ resources with | string | `"perm"` | no |
| stack-owner | Team to tag TLZ resources with to denote support ownership | string | n/a | yes |
| stack-region | Region to tag TLZ resources with (AMR/EU/APAC) | string | `"AMR"` | no |
| stack-support\_group | Email to tag TLZ resources with to direct support requests | string | n/a | yes |
| stack-version | TLZ version to tag TLZ resources with | string | n/a | yes |
| subnet\_ids | subnet\_ids used by lambdas that call GHE and TFE | list | n/a | yes |
| tfe\_api\_url | URL for the v2 API for PTFE. Should be https://<ptfe\_hostname>/api/v2 | string | n/a | yes |
| tfe\_org\_name | Name of the organization the TLZ will be deployed through in PTFE | string | n/a | yes |
| timeout | Timeout value for Lambda function | string | `"300"` | no |
| tlz\_admin\_role | Admin role that is used | string | n/a | yes |
| tlz\_git\_url | url for bitbucket or github repositores | string | n/a | yes |
| tlz\_org\_account\_access\_role | Name of the role created when accounts are created by organizations | string | `"tlz_org_account_access_role"` | no |
| vended\_applications\_project | Bitbucket project where the user-facing repos will be created | string | `"TLZ-VA"` | no |
| vended\_baselines\_project | Bitbucket project where vended baselines will be forked into | string | `"TLZ-VB"` | no |

## Outputs

| Name | Description |
|------|-------------|
| baseline\_version | Version of the baseline module |
| iam\_role\_arn | ARN of admin IAM role |

=======

# account-pipeline-tools
This repo contains the all the tools needed to support [account-creation pipeline]g(./doc/index.md)
