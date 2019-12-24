import boto3
import os
import io
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import csv
import avm_common
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    try:
        account_id = event["AccountId"]
        sns_topic = avm_common.get_param("sns_topic_arn")
        print(sns_topic)
        print(account_id)
        sub  = "ERROR: avm sns post account creation email"
        func = "avm-sns-post-account-creation-email"
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
    response = None
    newAccountID = event["AccountId"]
    
    client = boto3.client('ses', region_name="us-west-2")
    message = MIMEMultipart()
    message['Subject'] = f"AWS account {newAccountID} created successfully"
    message['From'] = avm_common.get_param('post_account_sender_email')
    print(avm_common.get_param('post_account_sender_email'))
    result = avm_common.get_account_details(newAccountID)
    subscribers = avm_common.get_param('post_account_subscriber_emails')
    print(f"subscribers : {subscribers}")
    target = subscribers.split(",")
    body  = f"""<h1>AWS Account creation details</h1>

    <h4>Account {newAccountID} created successfully!!</h4>
    """

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
    if result["request_details"]:
        body += f"""
    <h2>Request details from webform</h2>
    <table border="1">
      <tr><th>Parameter</th><th>Value</th></tr>
        """
        writer.writerow(["Account Request Details"])
        writer.writerow([",","Parameter", "Value"])
        for k in result["request_details"].keys():
            writer.writerow(["",k, result["request_details"][k]])
            body += f'<tr><td>{k}</td><td>{result["request_details"][k]}</td></tr>'
        body += f"""</table><p/>"""

    body += f"""
    <h2>Response from AccountVendingMachine</h2>
    <table border="1">
      <tr><th>Parameter</th><th>Value</th></tr>
    """
    writer.writerow(["Response from AccountVendingMachine"])
    writer.writerow(["","Parameter", "Value"])
    for k in result["org_details"].keys():
        writer.writerow([",",k, result["org_details"][k]])
        body += f'<tr><td>{k}</td><td>{result["org_details"][k]}</td></tr>'

    body += f"""</table>
    <p/>
    """
    attached_file_name = f"aws_account_{newAccountID}.csv"
    # message body
    part = MIMEText(body, 'html')
    message.attach(part)
    attachment_string = None

    #print(output.getvalue())
    #print(body)
    # attachment
    if attachment_string:   # if bytestring available
        part = MIMEApplication(str.encode('attachment_string'))
    else:    # if file provided
        part = MIMEApplication(output.getvalue())
        part.add_header('Content-Disposition', 'attachment', filename=attached_file_name)
        message.attach(part)
        response = client.send_raw_email(
            Source=message['From'],
            Destinations=target,
            RawMessage={
                'Data': message.as_string()
            }
        )
        print("Sent an email to subscribers")

    # Send the SNS notification
    # Create an SNS client
    sns = boto3.client('sns')

    # Publish a simple message to the specified SNS topic
    response = sns.publish(
        TopicArn=avm_common.get_param('sns_topic_arn'),
        Message=f'account : {newAccountID} created successfully',
    )
    # Print out the response
    print(response)

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
