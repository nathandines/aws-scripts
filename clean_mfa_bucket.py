#!/usr/bin/python
from __future__ import print_function

from six.moves import input
import boto3

BUCKET = 'example-bucket'

def main():
    sts_client = boto3.client('sts')
    aws_account_id = sts_client.get_caller_identity()['Account']
    mfa_serial = 'arn:aws:iam::{}:mfa/root-account-mfa-device'.format(aws_account_id)

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(BUCKET)
    object_versions = bucket.object_versions.all()
    delete_objects = []
    for object_version in object_versions:
        is_latest = object_version.is_latest
        delete_marker = not object_version.e_tag
        if (
                delete_marker
                or not is_latest
            ):
            print('{}'.format(object_version.object_key))
            delete_objects.append(
                {
                    'Key': object_version.object_key,
                    'VersionId': object_version.id
                }
            )

    delete_lists = []
    REQUEST_LENGTH = 1000
    while True:
        this_list = []
        for i in range(REQUEST_LENGTH):
            try:
                this_list.append(delete_objects.pop(0))
            except IndexError:
                break
        delete_lists.append(this_list)
        if len(this_list) < REQUEST_LENGTH:
            break
    for delete_request in delete_lists:
        mfa_token = input('MFA token for {}: '.format(mfa_serial))
        bucket.delete_objects(
            MFA='{} {}'.format(mfa_serial, mfa_token),
            Delete={'Objects': delete_request}
        )

if __name__ == '__main__':
    main()
