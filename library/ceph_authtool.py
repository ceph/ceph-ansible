from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
try:
    from ansible.module_utils.ca_common import container_exec, \
                                               is_containerized
except ImportError:
    from module_utils.ca_common import container_exec, \
                                       is_containerized
import datetime
import os


class KeyringExists(Exception):
    pass


def build_cmd(create_keyring=False,
              gen_key=False,
              add_key=False,
              import_keyring=None,
              caps={},
              name=None,
              path=None,
              container_image=None,
              **a):

    auth_tool_binary: str = 'ceph-authtool'

    if container_image:
        c = container_exec(auth_tool_binary,
                           container_image)
    else:
        c = [auth_tool_binary]

    if name:
        c.extend(['-n', name])
    if create_keyring:
        if os.path.exists(path):
            raise KeyringExists
        c.append('-C')
    if gen_key:
        c.append('-g')
    if caps:
        for k, v in caps.items():
            c.extend(['--cap'] + [k] + [v])

    c.append(path)

    if import_keyring:
        c.extend(['--import-keyring', import_keyring])

    return c


def run_module():
    module_args = dict(
        name=dict(type='str', required=False),
        create_keyring=dict(type='bool', required=False, default=False),
        gen_key=dict(type='bool', required=False, default=False),
        add_key=dict(type='str', required=False, default=None),
        import_keyring=dict(type='str', required=False, default=None),
        caps=dict(type='dict', required=False, default=None),
        path=dict(type='str', required=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        add_file_common_args=True,
    )

    cmd = []
    changed = False

    result = dict(
        changed=changed,
        stdout='',
        stderr='',
        rc=0,
        start='',
        end='',
        delta='',
    )

    if module.check_mode:
        module.exit_json(**result)

    startd = datetime.datetime.now()

    # will return either the image name or None
    container_image = is_containerized()
    try:
        cmd = build_cmd(**module.params, container_image=container_image)
    except KeyringExists:
        rc = 0
        out = f"{module.params['path']} already exists. Skipping"
        err = ""
    else:
        rc, out, err = module.run_command(cmd)
        if rc == 0:
            changed = True

    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        cmd=cmd,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        rc=rc,
        stdout=out.rstrip("\r\n"),
        stderr=err.rstrip("\r\n"),
        changed=changed,
    )
    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    # file_args = module.load_file_common_arguments(module.params)
    # module.set_fs_attributes_if_different(file_args, False)
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
