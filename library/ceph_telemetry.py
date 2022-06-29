#!/usr/bin/python

# Copyright 2022, Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: ceph_telemetry

short_description: Manages Ceph Telemetry

version_added: "1.0.0"

description: Manages Ceph Telemetry

options:
    state:
        description: Enable/Disable telemetry if telemetry_accept_license is accepted
        required: false
        choices: ['enable', 'disable']
    channels:
        description: List of channels which need to be enabled
        required: false
        choices: ['basic', 'crash', 'device', 'ident', 'perf']
        default: ['basic', 'crash', 'device']
    submission_interval:
        description: The module compiles and sends a new report every 24 hours by default
        required: false
        default: 24
    proxy_settings:
        description: If the cluster cannot directly connect to the configured telemetry endpoint (default telemetry.ceph.com), you can configure a HTTP/HTTPS proxy server
        required: false
    contact:
        description: A contact can be added to the report
        required: false
    description:
        description: A description can be added to the report
        required: false
  
author:
    - Teoman ONAY (tonay@redhat.com)
'''

EXAMPLES = r'''
- name: Enable Telemetry
  ceph_telemetry:
    state: enable
    channels:
      - basic
      - crash
      - device
      - ident
      - perf
    submission_interval: 24
    proxy_settings: 'http://user:password@localhost.localdomain:8080
    contact: John Doe <john.doe@example.com>
    description: 'My first Ceph Cluster'
'''

RETURN = r'''# '''

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.ca_common import is_containerized, \
                                               exec_command, \
                                               generate_ceph_cmd, \
                                               exit_module
except ImportError:
    from module_utils.ca_common import is_containerized, \
                                       exec_command, \
                                       generate_ceph_cmd, \
                                       exit_module

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type='str', required=True, choices=['enable', 'disable', 'info'], default='disable'), 
        channels=dict(type='list', required=True ,choices=['basic', 'crash', 'device', 'ident', 'perf'], default=['basic', 'crash', 'device']),
        submission_interval=dict(type='int', required=False, default=24),
        proxy_settings=dict(type='str', required=False),
        contact=dict(type='str', required=False),
        description=dict(type='str', required=False)
    )

    state = module.params.get('state')
    channels = module.params.get('channels')
    submission = module.params.get('submission_interval')
    proxy = module.params.get('proxy_settings')
    contact = module.params.get('proxy_settings')
    desc = module.params.get('description')

    startd = datetime.datetime.now()

    container_image = is_containerized()

    cmd = generate_ceph_cmd(['telemetry'],
                            [state],
                            cluster=cluster,
                            container_image=container_image)

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result['original_message'] = module.params['name']
    result['message'] = 'goodbye'

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if module.params['new']:
        result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if module.params['name'] == 'fail me':
        module.fail_json(msg='You requested this to fail', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()