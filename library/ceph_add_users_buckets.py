#!/usr/bin/python

# Copyright 2018 Daniel Pivonka <dpivonka@redhat.com>
# Copyright 2018 Red Hat, Inc.
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_add_users_buckets
short_description: bulk create user and buckets
description:
    - Bulk create Ceph Object Storage users and buckets

option:
    rgw_host:
        description:
            - a radosgw host in the ceph cluster
        required: true
    port:
        description:
            - tcp port of the radosgw host
        required: true
    is_secure:
        description:
            - boolean indicating whether the instance is running over https
        required: false
        default: false
    admin_access_key:
        description:
            - radosgw admin user's access key
        required: true
    admin_secret_key:
        description:
            - radosgw admin user's secret key
        required: true
    users:
        description:
            - list of users to be created containing sub options
        required: false
        sub_options:
            username:
                description:
                    - username for new user
                required: true
            fullname:
                description:
                    - fullname for new user
                required: true
            email:
                description:
                    - email for new user
                required: false
            maxbucket:
                description:
                    - max bucket for new user
                required: false
                default: 1000
            suspend:
                description:
                    - suspend a new user apon creation
                required: false
                default: false
            autogenkey:
                description:
                    - auto generate keys for new user
                required: false
                default: true
            accesskey:
                description:
                    - access key for new user
                required: false
            secretkey:
                description:
                    - secret key for new user
                required: false
            userquota:
                description:
                    - enable/disable user quota for new user
                required: false
                default: false
            usermaxsize:
                description:
                    - with user quota enabled specify quota size in kb
                required: false
                default: unlimited
            usermaxobjects:
                description:
                    - with user quota enabled specify maximum number of objects
                required: false
                default: unlimited
            bucketquota:
                description:
                    - enable/disable bucket quota for new user
                required: false
                default: false
            bucketmaxsize:
                description:
                    - with bucket quota enabled specify bucket size in kb
                required: false
                default: unlimited
            bucketmaxobjects:
                description:
                    - with bucket quota enabled specify maximum number of objects
                required: false
                default: unlimited
    buckets:
        description:
            - list of buckets to be created containing sub options
        required: false
        sub_options:
            bucket:
                description:
                    - name for new bucket
                required: true
            user:
                description:
                    - user new bucket will be linked too
                required: true


requirements: ['radosgw', 'boto']

author:
    - 'Daniel Pivonka'

'''

EXAMPLES = '''
# single basic user
- name: single basic user
    ceph_add_users_buckets:
      rgw_host: '172.16.0.12'
      port: 8080
      admin_access_key: 'N61I8625V4XTWGDTLBLL'
      admin_secret_key: 'HZrkuHHO9usUurDWBQHTeLIjO325bIULaC7DxcoV'
      users:
        - username: 'test1'
          fullname: 'tester'


# single complex user
- name: single complex user
    ceph_add_users_buckets:
      rgw_host: '172.16.0.12'
      port: 8080
      admin_access_key: 'N61I8625V4XTWGDTLBLL'
      admin_secret_key: 'HZrkuHHO9usUurDWBQHTeLIjO325bIULaC7DxcoV'
      users:
        - username: 'test1'
          fullname: 'tester'
          email: 'dan@email.com'
          maxbucket: 666
          suspend: true
          autogenkey: true
          accesskey: 'B3AR4Q33L59YV56A9A2F'
          secretkey: 'd84BRnMysnVGSyZiRlYUMduVgIarQWiNMdKzrF76'
          userquota: true
          usermaxsize: '1000'
          usermaxobjects: 3
          bucketquota: true
          bucketmaxsize: '1000'
          bucketmaxobjects: 3

# multi user
- name: multi user
    ceph_add_users_buckets:
      rgw_host: '172.16.0.12'
      port: 8080
      admin_access_key: 'N61I8625V4XTWGDTLBLL'
      admin_secret_key: 'HZrkuHHO9usUurDWBQHTeLIjO325bIULaC7DxcoV'
      users:
        - username: 'test1'
          fullname: 'tester'
          email: 'dan@email.com'
          maxbucket: 666
          suspend: true
          autogenkey: true
          accesskey: 'B3AR4Q33L59YV56A9A2F'
          secretkey: 'd84BRnMysnVGSyZiRlYUMduVgIarQWiNMdKzrF76'
          userquota: true
          usermaxsize: '1000K'
          usermaxobjects: 3
          bucketquota: true
          bucketmaxsize: '1000K'
          bucketmaxobjects: 3
        - username: 'test2'
          fullname: 'tester'

# single bucket
- name: single basic user
    ceph_add_users_buckets:
      rgw_host: '172.16.0.12'
      port: 8080
      admin_access_key: 'N61I8625V4XTWGDTLBLL'
      admin_secret_key: 'HZrkuHHO9usUurDWBQHTeLIjO325bIULaC7DxcoV'
      buckets:
        - bucket: 'heyimabucket1'
          user: 'test1'

# multi bucket
- name: single basic user
    ceph_add_users_buckets:
      rgw_host: '172.16.0.12'
      port: 8080
      admin_access_key: 'N61I8625V4XTWGDTLBLL'
      admin_secret_key: 'HZrkuHHO9usUurDWBQHTeLIjO325bIULaC7DxcoV'
      buckets:
        - bucket: 'heyimabucket1'
          user: 'test1'
        - bucket: 'heyimabucket2'
          user: 'test2'
        - bucket: 'heyimabucket3'
          user: 'test2'

# buckets and users
- name: single basic user
    ceph_add_users_buckets:
      rgw_host: '172.16.0.12'
      port: 8080
      admin_access_key: 'N61I8625V4XTWGDTLBLL'
      admin_secret_key: 'HZrkuHHO9usUurDWBQHTeLIjO325bIULaC7DxcoV'
      users:
        - username: 'test1'
          fullname: 'tester'
          email: 'dan@email.com'
          maxbucket: 666
        - username: 'test2'
          fullname: 'tester'
          email: 'dan1@email.com'
          accesskey: 'B3AR4Q33L59YV56A9A2F'
          secretkey: 'd84BRnMysnVGSyZiRlYUMduVgIarQWiNMdKzrF76'
          userquota: true
          usermaxsize: '1000'
          usermaxobjects: 3
          bucketquota: true
          bucketmaxsize: '1000'
          bucketmaxobjects: 3
      buckets:
        - bucket: 'heyimabucket1'
          user: 'test1'
        - bucket: 'heyimabucket2'
          user: 'test2'
        - bucket: 'heyimabucket3'
          user: 'test2'

'''

RETURN = '''
error_messages:
    description: error for failed user or bucket.
    returned: always
    type: list
    sample: [
            "test2: could not modify user: unable to modify user, cannot add duplicate email\n"
        ]

failed_users:
    description: users that were not created.
    returned: always
    type: str
    sample: "test2"

added_users:
    description: users that were created.
    returned: always
    type: str
    sample: "test1"

failed_buckets:
    description: buckets that were not created.
    returned: always
    type: str
    sample: "heyimabucket3"

added_buckets:
    description: buckets that were created.
    returned: always
    type: str
    sample: "heyimabucket1, heyimabucket2"

'''

from ansible.module_utils.basic import AnsibleModule
from socket import error as socket_error
import boto
import radosgw


def create_users(rgw, users, result):

    added_users = []
    failed_users = []

    for user in users:

        # get info
        username = user['username']
        fullname = user['fullname']
        email = user['email']
        maxbucket = user['maxbucket']
        suspend = user['suspend']
        autogenkey = user['autogenkey']
        accesskey = user['accesskey']
        secretkey = user['secretkey']
        userquota = user['userquota']
        usermaxsize = user['usermaxsize']
        usermaxobjects = user['usermaxobjects']
        bucketquota = user['bucketquota']
        bucketmaxsize = user['bucketmaxsize']
        bucketmaxobjects = user['bucketmaxobjects']

        fail_flag = False

        #  check if user exists
        try:
            user_info = rgw.get_user(uid=username)
        except radosgw.exception.RadosGWAdminError as e:
            # it doesnt exist
            user_info = None

        # user exists can not create
        if user_info:
            result['error_messages'].append(username + ' UserExists')
            failed_users.append(username)
        else:
            # user doesnt exist create it
            if email:
                if autogenkey:
                    try:
                        rgw.create_user(username, fullname, email=email, key_type='s3',
                                        generate_key=autogenkey,
                                        max_buckets=maxbucket, suspended=suspend)
                    except radosgw.exception.RadosGWAdminError as e:
                        result['error_messages'].append(username + ' ' + e.get_code())
                        fail_flag = True
                else:
                    try:
                        rgw.create_user(username, fullname, email=email, key_type='s3',
                                        access_key=accesskey, secret_key=secretkey,
                                        max_buckets=maxbucket, suspended=suspend)
                    except radosgw.exception.RadosGWAdminError as e:
                        result['error_messages'].append(username + ' ' + e.get_code())
                        fail_flag = True
            else:
                if autogenkey:
                    try:
                        rgw.create_user(username, fullname, key_type='s3',
                                        generate_key=autogenkey,
                                        max_buckets=maxbucket, suspended=suspend)
                    except radosgw.exception.RadosGWAdminError as e:
                        result['error_messages'].append(username + ' ' + e.get_code())
                        fail_flag = True
                else:
                    try:
                        rgw.create_user(username, fullname, key_type='s3',
                                        access_key=accesskey, secret_key=secretkey,
                                        max_buckets=maxbucket, suspended=suspend)
                    except radosgw.exception.RadosGWAdminError as e:
                        result['error_messages'].append(username + ' ' + e.get_code())
                        fail_flag = True

            if not fail_flag and userquota:
                try:
                    rgw.set_quota(username, 'user', max_objects=usermaxobjects,
                                  max_size_kb=usermaxsize, enabled=True)
                except radosgw.exception.RadosGWAdminError as e:
                    result['error_messages'].append(username + ' ' + e.get_code())
                    fail_flag = True

            if not fail_flag and bucketquota:
                try:
                    rgw.set_quota(username, 'bucket', max_objects=bucketmaxobjects,
                                  max_size_kb=bucketmaxsize, enabled=True)
                except radosgw.exception.RadosGWAdminError as e:
                    result['error_messages'].append(username + ' ' + e.get_code())
                    fail_flag = True

            if fail_flag:
                try:
                    rgw.delete_user(username)
                except radosgw.exception.RadosGWAdminError as e:
                    pass
                failed_users.append(username)
            else:
                added_users.append(username)

        result['added_users'] = ", ".join(added_users)
        result['failed_users'] = ", ".join(failed_users)


def create_buckets(rgw, buckets, result):

    added_buckets = []
    failed_buckets = []

    for bucket_info in buckets:
        bucket = bucket_info['bucket']
        user = bucket_info['user']

        #  check if bucket exists
        try:
            bucket_info = rgw.get_bucket(bucket_name=bucket)
        except TypeError:
            # it doesnt exist
            bucket_info = None

        # if it exists add to failed list
        if bucket_info:
            failed_buckets.append(bucket)
            result['error_messages'].append(bucket + ' BucketExists')
        else:
            # bucket doesn't exist, so we need to create it
            bucket_info = create_bucket(rgw, bucket)
            if bucket_info:
                # bucket created ok, link to user

                #  check if user exists
                try:
                    user_info = rgw.get_user(uid=user)
                except radosgw.exception.RadosGWAdminError as e:
                    # it doesnt exist
                    user_info = None

                # user exists, link
                if user_info:
                    try:
                        rgw.link_bucket(bucket_name=bucket,
                                        bucket_id=bucket_info.id,
                                        uid=user)
                        added_buckets.append(bucket)
                    except radosgw.exception.RadosGWAdminError as e:
                        result['error_messages'].append(bucket + e.get_code())
                        try:
                            rgw.delete_bucket(bucket, purge_objects=True)
                        except radosgw.exception.RadosGWAdminError as e:
                            pass
                        failed_buckets.append(bucket)

                else:
                    # user doesnt exist cant be link delete bucket
                    try:
                        rgw.delete_bucket(bucket, purge_objects=True)
                    except radosgw.exception.RadosGWAdminError as e:
                        pass
                    failed_buckets.append(bucket)
                    result['error_messages'].append(bucket + ' could not be linked' + ', NoSuchUser ' + user)

            else:
                # something went wrong
                failed_buckets.append(bucket)
                result['error_messages'].append(bucket + ' could not be created')

        result['added_buckets'] = ", ".join(added_buckets)
        result['failed_buckets'] = ", ".join(failed_buckets)


def create_bucket(rgw, bucket):
    conn = boto.connect_s3(aws_access_key_id=rgw.provider._access_key,
                           aws_secret_access_key=rgw.provider._secret_key,
                           host=rgw._connection[0],
                           port=rgw.port,
                           is_secure=rgw.is_secure,
                           calling_format=boto.s3.connection.OrdinaryCallingFormat(),
                           )

    try:
        conn.create_bucket(bucket_name=bucket)
        bucket_info = rgw.get_bucket(bucket_name=bucket)
    except boto.exception.S3ResponseError:
        return None
    else:
        return bucket_info


def main():
    # arguments/parameters that a user can pass to the module
    fields = dict(rgw_host=dict(type='str', required=True),
                  port=dict(type='int', required=True),
                  is_secure=dict(type='bool',
                                 required=False,
                                 default=False),
                  admin_access_key=dict(type='str', required=True),
                  admin_secret_key=dict(type='str', required=True),
                  buckets=dict(type='list', required=False, elements='dict',
                               options=dict(bucket=dict(type='str', required=True),
                                            user=dict(type='str', required=True))),
                  users=dict(type='list', required=False, elements='dict',
                             options=dict(username=dict(type='str', required=True),
                                          fullname=dict(type='str', required=True),
                                          email=dict(type='str', required=False),
                                          maxbucket=dict(type='int', required=False, default=1000),
                                          suspend=dict(type='bool', required=False, default=False),
                                          autogenkey=dict(type='bool', required=False, default=True),
                                          accesskey=dict(type='str', required=False),
                                          secretkey=dict(type='str', required=False),
                                          userquota=dict(type='bool', required=False, default=False),
                                          usermaxsize=dict(type='str', required=False, default='-1'),
                                          usermaxobjects=dict(type='int', required=False, default=-1),
                                          bucketquota=dict(type='bool', required=False, default=False),
                                          bucketmaxsize=dict(type='str', required=False, default='-1'),
                                          bucketmaxobjects=dict(type='int', required=False, default=-1))))

    # the AnsibleModule object
    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)

    # get vars
    rgw_host = module.params.get('rgw_host')
    port = module.params.get('port')
    is_secure = module.params.get('is_secure')
    admin_access_key = module.params.get('admin_access_key')
    admin_secret_key = module.params.get('admin_secret_key')
    users = module.params['users']
    buckets = module.params.get('buckets')

    # seed the result dict in the object
    result = dict(
        changed=False,
        error_messages=[],
        added_users='',
        failed_users='',
        added_buckets='',
        failed_buckets='',
    )

    # radosgw connection
    rgw = radosgw.connection.RadosGWAdminConnection(host=rgw_host,
                                                    port=port,
                                                    access_key=admin_access_key,
                                                    secret_key=admin_secret_key,
                                                    aws_signature='AWS4',
                                                    is_secure=is_secure)

    # test connection
    connected = True
    try:
        rgw.get_usage()
    except radosgw.exception.RadosGWAdminError as e:
        connected = False
        result['error_messages'] = e.get_code()
    except socket_error as e:
        connected = False
        result['error_messages'] = str(e)

    if connected and users:
        create_users(rgw, users, result)

    if connected and buckets:
        create_buckets(rgw, buckets, result)

    if result['added_users'] != '' or result['added_buckets'] != '':
        result['changed'] = True

    # conditional state caused a failure
    if result['added_users'] == '' and result['added_buckets'] == '':
        module.fail_json(msg='No users or buckets were added successfully',
                         **result)

    # EXIT
    module.exit_json(**result)


if __name__ == '__main__':
    main()
