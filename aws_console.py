#!/usr/bin/env python2

import argparse
import json
import urllib2
import webbrowser
from urllib import urlencode
import os
import boto3

parser = argparse.ArgumentParser()
parser.add_argument('--profile', type=str, default=None)
parser.add_argument('--to-terminal', action="store_true")
parser.add_argument('--url', type=str, default="https://console.aws.amazon.com/console/home")

args = parser.parse_args()

if os.environ.get('AWS_SESSION_TOKEN'):
    federation_token = {
        'Credentials': {
            'AccessKeyId': os.environ['AWS_ACCESS_KEY_ID'],
            'SecretAccessKey': os.environ['AWS_SECRET_ACCESS_KEY'],
            'SessionToken': os.environ['AWS_SESSION_TOKEN']
        }
    }
else:
    session = boto3.session.Session(profile_name=args.profile)
    sts_client = session.client('sts')

    my_identity = sts_client.get_caller_identity()
    federation_token = sts_client.get_federation_token(
        Name=my_identity['Arn'].split('/')[-1],
        Policy=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "*",
                        "Resource": "*"
                    }
                ]
            }
        ),
        #DurationSeconds=1800
    )

signin_url = "https://signin.aws.amazon.com/federation"
url_params = {
    "Action": "getSigninToken",
    "Session": json.dumps(
        {
            "sessionId": federation_token['Credentials']['AccessKeyId'],
            "sessionKey": federation_token['Credentials']['SecretAccessKey'],
            "sessionToken": federation_token['Credentials']['SessionToken']
        }
    )
}
signin_token = json.loads(urllib2.urlopen(signin_url + "?" + urlencode(url_params)).read())['SigninToken']

url_params = {
    "Action": "login",
    "Destination": args.url,
    "SigninToken": signin_token
}
if not args.to_terminal:
    webbrowser.open(signin_url + "?" + urlencode(url_params))
else:
    print(signin_url + "?" + urlencode(url_params))
