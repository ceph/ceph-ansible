# Copyright 2021, Red Hat, Inc.
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

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.ca_common import exit_module, generate_ceph_cmd, is_containerized, exec_command
except ImportError:
    from module_utils.ca_common import exit_module, generate_ceph_cmd, is_containerized, exec_command
import datetime


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_dashboard_rgw

short_description: Manage Ceph Dashboard RGW API

version_added: "2.8"

description:
    - Manage Ceph Dashboard rgw api configuration.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    user:
        description:
            - user of the Ceph Rados Gateway API.
        required: true
    access_key:
        description:
            - access key of the Ceph Rados Gateway API.
        required: true
    secret_key:
        description:
            - secret key of the Ceph Rados Gateway API.
        required: true
    host:
        description:
            - host of the Ceph Rados Gateway API.
        required: true
    port:
        description:
            - port of the Ceph Rados Gateway API.
        required: false
    scheme:
        description:
            - scheme of the Ceph Rados Gateway API.
        required: false
    admin_resource:
        description:
            - admin resource of the Ceph Rados Gateway API.
        required: false
    tls_verify:
        description:
            - verify the TLS certificate of the Ceph Rados Gateway API.
        required: false

author:
    - Dimitri Savineau <dsavinea@redhat.com>
'''

EXAMPLES = '''
- name: enabling the Ceph Dashboard RGW frontend
  ceph_dashboard_rgw:
    user: foo
    access_key: LbwDPp2BBo2Sdlts89Um
    secret_key: FavL6ueQWcWuWn0YXyQ3TnJ3mT3Uj5SGVHCUXC5K
    host: 192.168.100.1
    port: 8080
    scheme: https
    admin_resource: admin
    tls_verify: false
'''

RETURN = '''#  '''


def get_rgw_api_user(module, container_image=None):
    '''
    Get rgw api user
    '''

    cluster = module.params.get('cluster')

    args = ['get-rgw-api-user-id']

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def set_rgw_api_user(module, container_image=None):
    '''
    Set rgw api user
    '''

    cluster = module.params.get('cluster')
    user = module.params.get('user')

    args = ['set-rgw-api-user-id', user]

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def get_rgw_api_access_key(module, container_image=None):
    '''
    Get rgw api access key
    '''

    cluster = module.params.get('cluster')

    args = ['get-rgw-api-access-key']

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def set_rgw_api_access_key(module, container_image=None):
    '''
    Set rgw api access key
    '''

    cluster = module.params.get('cluster')

    args = ['set-rgw-api-access-key', '-i', '-']

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image, interactive=True)

    return cmd


def get_rgw_api_secret_key(module, container_image=None):
    '''
    Get rgw api secret key
    '''

    cluster = module.params.get('cluster')

    args = ['get-rgw-api-secret-key']

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def set_rgw_api_secret_key(module, container_image=None):
    '''
    Set rgw api secret key
    '''

    cluster = module.params.get('cluster')

    args = ['set-rgw-api-secret-key', '-i', '-']

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image, interactive=True)

    return cmd


def get_rgw_api_host(module, container_image=None):
    '''
    Get rgw api host
    '''

    cluster = module.params.get('cluster')

    args = ['get-rgw-api-host']

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def set_rgw_api_host(module, container_image=None):
    '''
    Set rgw api host
    '''

    cluster = module.params.get('cluster')
    host = module.params.get('host')

    args = ['set-rgw-api-host', host]

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def get_rgw_api_port(module, container_image=None):
    '''
    Get rgw api port
    '''

    cluster = module.params.get('cluster')

    args = ['get-rgw-api-port']

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def set_rgw_api_port(module, container_image=None):
    '''
    Set rgw api port
    '''

    cluster = module.params.get('cluster')
    port = module.params.get('port')

    args = ['set-rgw-api-port', str(port)]

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def get_rgw_api_scheme(module, container_image=None):
    '''
    Get rgw api scheme
    '''

    cluster = module.params.get('cluster')

    args = ['get-rgw-api-scheme']

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def set_rgw_api_scheme(module, container_image=None):
    '''
    Set rgw api scheme
    '''

    cluster = module.params.get('cluster')
    scheme = module.params.get('scheme')

    args = ['set-rgw-api-scheme', scheme]

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def get_rgw_api_admin_resource(module, container_image=None):
    '''
    Get rgw api admin resource
    '''

    cluster = module.params.get('cluster')

    args = ['get-rgw-api-admin-resource']

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def set_rgw_api_admin_resource(module, container_image=None):
    '''
    Set rgw api admin resource
    '''

    cluster = module.params.get('cluster')
    admin_resource = module.params.get('admin_resource')

    args = ['set-rgw-api-admin-resource', admin_resource]

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def get_rgw_api_tls_verify(module, container_image=None):
    '''
    Get rgw api tls verify
    '''

    cluster = module.params.get('cluster')

    args = ['get-rgw-api-ssl-verify']

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def set_rgw_api_tls_verify(module, container_image=None):
    '''
    Set rgw api tls verify
    '''

    cluster = module.params.get('cluster')
    tls_verify = module.params.get('tls_verify')

    args = ['set-rgw-api-ssl-verify', str(tls_verify)]

    cmd = generate_ceph_cmd(['dashboard'], args, cluster=cluster, container_image=container_image)

    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cluster=dict(type='str', required=False, default='ceph'),
            user=dict(type='str', required=True),
            access_key=dict(type='str', required=True, no_log=True),
            secret_key=dict(type='str', required=True, no_log=True),
            host=dict(type='str', required=True),
            port=dict(type='int', required=False),
            scheme=dict(type='str', required=False, choices=['http', 'https']),
            admin_resource=dict(type='str', required=False),
            tls_verify=dict(type='bool', required=False),
        ),
        supports_check_mode=True,
    )

    user = module.params.get('user')
    access_key = module.params.get('access_key')
    secret_key = module.params.get('secret_key')
    host = module.params.get('host')
    port = str(module.params.get('port'))
    scheme = module.params.get('scheme')
    admin_resource = module.params.get('admin_resource')
    tls_verify = str(module.params.get('tls_verify'))

    if module.check_mode:
        module.exit_json(
            changed=False,
            stdout='',
            stderr='',
            rc=0,
            start='',
            end='',
            delta='',
        )

    startd = datetime.datetime.now()
    changed = False

    # will return either the image name or None
    container_image = is_containerized()

    cmds = []
    outs = ''
    errs = ''

    rc, cmd, out, err = exec_command(module, get_rgw_api_user(module, container_image=container_image))
    if user != out.rstrip("\r\n"):
        rc, cmd, out, err = exec_command(module, set_rgw_api_user(module, container_image=container_image))
        if rc != 0:
            exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=False)
        changed = True
        outs += out
        errs += err
    cmds.append(' '.join(cmd))

    rc, cmd, out, err = exec_command(module, get_rgw_api_access_key(module, container_image=container_image))
    if access_key != out.rstrip("\r\n"):
        rc, cmd, out, err = exec_command(module, set_rgw_api_access_key(module, container_image=container_image), stdin=access_key)
        if rc != 0:
            exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=False)
        changed = True
        outs += out
        errs += err
    cmds.append(' '.join(cmd))

    rc, cmd, out, err = exec_command(module, get_rgw_api_secret_key(module, container_image=container_image))
    if secret_key != out.rstrip("\r\n"):
        rc, cmd, out, err = exec_command(module, set_rgw_api_secret_key(module, container_image=container_image), stdin=secret_key)
        if rc != 0:
            exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=False)
        changed = True
        outs += out
        errs += err
    cmds.append(' '.join(cmd))

    rc, cmd, out, err = exec_command(module, get_rgw_api_host(module, container_image=container_image))
    if host != out.rstrip("\r\n"):
        rc, cmd, out, err = exec_command(module, set_rgw_api_host(module, container_image=container_image))
        if rc != 0:
            exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=False)
        changed = True
        outs += out
        errs += err
    cmds.append(' '.join(cmd))

    if port:
        rc, cmd, out, err = exec_command(module, get_rgw_api_port(module, container_image=container_image))
        if port != out.rstrip("\r\n"):
            rc, cmd, out, err = exec_command(module, set_rgw_api_port(module, container_image=container_image))
            if rc != 0:
                exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=False)
            changed = True
            outs += out
            errs += err
        cmds.append(' '.join(cmd))

    if scheme:
        rc, cmd, out, err = exec_command(module, get_rgw_api_scheme(module, container_image=container_image))
        if scheme != out.rstrip("\r\n"):
            rc, cmd, out, err = exec_command(module, set_rgw_api_scheme(module, container_image=container_image))
            if rc != 0:
                exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=False)
            changed = True
            outs += out
            errs += err
        cmds.append(' '.join(cmd))

    if admin_resource:
        rc, cmd, out, err = exec_command(module, get_rgw_api_admin_resource(module, container_image=container_image))
        if admin_resource != out.rstrip("\r\n"):
            rc, cmd, out, err = exec_command(module, set_rgw_api_admin_resource(module, container_image=container_image))
            if rc != 0:
                exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=False)
            changed = True
            outs += out
            errs += err
        cmds.append(' '.join(cmd))

    if tls_verify:
        rc, cmd, out, err = exec_command(module, get_rgw_api_tls_verify(module, container_image=container_image))
        if tls_verify != out.rstrip("\r\n"):
            rc, cmd, out, err = exec_command(module, set_rgw_api_tls_verify(module, container_image=container_image))
            if rc != 0:
                exit_module(module=module, out=out, rc=rc, cmd=cmd, err=err, startd=startd, changed=False)
            changed = True
            outs += out
            errs += err
        cmds.append(' '.join(cmd))

    if not changed:
        outs = 'Nothing to update'

    exit_module(module=module, out=outs, rc=rc, cmd=cmds, err=errs, startd=startd, changed=changed)


if __name__ == '__main__':
    main()
