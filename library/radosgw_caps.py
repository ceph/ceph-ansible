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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

try:
    from ansible.module_utils.ca_common import (
        exit_module,
        exec_command,
        is_containerized,
        container_exec,
    )
except ImportError:
    from module_utils.ca_common import (
        exit_module,
        exec_command,
        is_containerized,
        container_exec,
    )
import datetime
import json
import re
from enum import IntFlag


ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = """
---
module: radosgw_caps

short_description: Manage RADOS Gateway Admin capabilities

version_added: "2.10"

description:
    - Manage RADOS Gateway capabilities addition and deletion.
options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
        type: str
    name:
        description:
            - name of the RADOS Gateway user (uid).
        required: true
        type: str
    state:
        description:
            If 'present' is used, the module will assign capabilities
            defined in `caps`.
            If 'absent' is used, the module will remove the capabilities.
        required: false
        choices: ['present', 'absent']
        default: present
        type: str
    caps:
        description:
            - The set of capabilities to assign or remove.
        required: true
        type: list
        elements: str

author:
    - Mathias Chapelain <mathias.chapelain@proton.ch>
"""

EXAMPLES = """
- name: add users read capabilties to a user
  radosgw_caps:
    name: foo
    state: present
    caps:
      - users=read

- name: add users read write and all buckets capabilities
  radosgw_caps:
    name: foo
    state: present
    caps:
      - users=read,write
      - buckets=*

- name: remove usage write capabilities
  radosgw_caps:
    name: foo
    state: absent
    caps:
      - usage=write
"""

RETURN = """
---
cmd:
  description: The radosgw-admin command being run by the module to apply caps settings.
  returned: always
  type: str
start:
  description: Timestamp of module execution start.
  returned: always
  type: str
end:
  description: Timestamp of module execution end.
  returned: always
  type: str
delta:
  description: Time of module execution between start and end.
  returned: always
  type: str
diff:
  description: Dict containing the user capabilities before and after modifications.
  returned: always
  type: dict
  contains:
    before:
      description: Contains user capabilities, json-formatted, as returned by `radosgw-admin user info`.
      returned: always
      type: str
    after:
      description: Contains user capabilities, json-formatted, as returned by `radosgw-admin caps add/rm`.
      returned: success
      type: str
rc:
  description: Return code of the module command executed, see `cmd` return value.
  returned: always
  type: int
stdout:
  description: Output of the executed command.
  returned: always
  type: str
stderr:
  description: Error output of the executed command.
  returned: always
  type: str
changed:
  description: Specify if user capabilities has been changed during module execution.
  returned: always
  type: bool
"""


def pre_generate_radosgw_cmd(container_image=None):
    """
    Generate radosgw-admin prefix comaand
    """
    if container_image:
        cmd = container_exec("radosgw-admin", container_image)
    else:
        cmd = ["radosgw-admin"]

    return cmd


def generate_radosgw_cmd(cluster, args, container_image=None):
    """
    Generate 'radosgw' command line to execute
    """

    cmd = pre_generate_radosgw_cmd(container_image=container_image)

    base_cmd = ["--cluster", cluster, "caps"]

    cmd.extend(base_cmd + args)

    return cmd


def add_caps(module, container_image=None):
    """
    Add capabilities
    """

    cluster = module.params.get("cluster")
    name = module.params.get("name")
    caps = module.params.get("caps")

    args = ["add", "--uid=" + name, "--caps=" + ";".join(caps)]

    cmd = generate_radosgw_cmd(
        cluster=cluster, args=args, container_image=container_image
    )

    return cmd


def remove_caps(module, container_image=None):
    """
    Remove capabilities
    """

    cluster = module.params.get("cluster")
    name = module.params.get("name")
    caps = module.params.get("caps")

    args = ["rm", "--uid=" + name, "--caps=" + ";".join(caps)]

    cmd = generate_radosgw_cmd(
        cluster=cluster, args=args, container_image=container_image
    )

    return cmd


def get_user(module, container_image=None):
    """
    Get existing user
    """

    cluster = module.params.get("cluster")
    name = module.params.get("name")

    args = ["info", "--uid=" + name, "--format=json"]

    cmd = pre_generate_radosgw_cmd(container_image=container_image)

    base_cmd = ["--cluster", cluster, "user"]

    cmd.extend(base_cmd + args)

    return cmd


class RGWUserCaps(IntFlag):
    INVALID = 0x0
    READ = 0x1
    WRITE = 0x2
    ALL = READ | WRITE


def perm_string_to_flag(perm):
    splitted = re.split(",|=| |\t", perm)
    if ("read" in splitted and "write" in splitted) or "*" in splitted:
        return RGWUserCaps.ALL
    elif "read" in splitted:
        return RGWUserCaps.READ
    elif "write" in splitted:
        return RGWUserCaps.WRITE
    return RGWUserCaps.INVALID


def perm_flag_to_string(perm):
    if perm == RGWUserCaps.ALL:
        return "*"
    elif perm == RGWUserCaps.READ:
        return "read"
    elif perm == RGWUserCaps.WRITE:
        return "write"
    else:
        return "invalid"


def params_to_caps_output(current_caps, params, deletion=False):
    out_caps = current_caps
    for param in params:
        splitted = param.split("=", maxsplit=1)
        cap = splitted[0]

        new_perm = perm_string_to_flag(splitted[1])
        current = next((item for item in out_caps if item["type"] == cap), None)

        if not current:
            if not deletion:
                out_caps.append(dict(type=cap, perm=perm_flag_to_string(new_perm)))
            continue

        current_perm = perm_string_to_flag(current["perm"])

        new_perm = current_perm & ~new_perm if deletion else new_perm | current_perm

        if new_perm == 0x0:
            out_caps.remove(current)

        current["perm"] = perm_flag_to_string(new_perm)

    return out_caps


def run_module():
    module_args = dict(
        cluster=dict(type="str", required=False, default="ceph"),
        name=dict(type="str", required=True),
        state=dict(
            type="str", required=False, choices=["present", "absent"], default="present"
        ),
        caps=dict(type="list", required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    # Gather module parameters in variables
    name = module.params.get("name")
    state = module.params.get("state")
    caps = module.params.get("caps")

    startd = datetime.datetime.now()
    changed = False

    # will return either the image name or None
    container_image = is_containerized()

    diff = dict(before="", after="")

    # get user infos for diff
    rc, cmd, out, err = exec_command(
        module, get_user(module, container_image=container_image)
    )

    if rc == 0:
        before_user = json.loads(out)
        before_caps = sorted(before_user["caps"], key=lambda d: d["type"])
        diff["before"] = json.dumps(before_caps, indent=4)

        out = ""
        err = ""

        if state == "present":
            cmd = add_caps(module, container_image=container_image)
        elif state == "absent":
            cmd = remove_caps(module, container_image=container_image)

        if not module.check_mode:
            rc, cmd, out, err = exec_command(module, cmd)
        else:
            out_caps = params_to_caps_output(
                before_user["caps"], caps, deletion=(state == "absent")
            )
            out = json.dumps(dict(caps=out_caps))

        if rc == 0:
            after_user = json.loads(out)["caps"]
            after_user = sorted(after_user, key=lambda d: d["type"])
            diff["after"] = json.dumps(after_user, indent=4)
            changed = diff["before"] != diff["after"]
    else:
        out = "User {} doesn't exist".format(name)

    exit_module(
        module=module,
        out=out,
        rc=rc,
        cmd=cmd,
        err=err,
        startd=startd,
        changed=changed,
        diff=diff,
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
