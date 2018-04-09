#!/usr/bin/python
import datetime

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_volume_zap

short_description: Zap devices used by ceph OSDs with ceph-volume

description:
    - Using the ceph-volume utility available in Ceph this module
      can be used to zap devices used by ceph OSDs.
    - These devices, partitions or logicial volumes can then be reused.
    - All partitions and logical volumes will be kept intact.

options:
    device:
        description:
            - The logical volume name, device or partition to zap.
        required: true
    device_vg:
        description:
            - If device is a lv, this must be the name of the volume group it belongs to.
        required: false
    destroy:
        description:
            - If set to True any logical volumes existing on a given device or partition will be destroyed.
        required: false
        default: true


author:
    - Andrew Schoen (@andrewschoen)
'''

EXAMPLES = '''
- name: zap a raw device
  ceph_volume_zap:
    device: /dev/sdc
    destroy: True

- name: zap a partition
  ceph_volume_zap:
    device: /dev/sdc1
    destroy: True

- name: zap a logical volume
  ceph_volume_zap:
    device: lv1
    device_vg: vg_name
'''


from ansible.module_utils.basic import AnsibleModule


def get_device(device, device_vg):
    if device_vg:
        device = "{0}/{1}".format(device_vg, device)
    return device


def run_module():
    module_args = dict(
        device=dict(type='str', required=True),
        device_vg=dict(type='str', required=False),
        destroy=dict(type='bool', required=False, default=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    device = module.params['device']
    device_vg = module.params.get('device_vg', None)
    destroy = module.params['destroy']

    cmd = [
        'ceph-volume',
        'lvm',
        'zap',
    ]

    device_to_zap = get_device(device, device_vg)
    cmd.append(device_to_zap)

    if destroy:
        cmd.append("--destroy")

    result = dict(
        changed=False,
        cmd=cmd,
        stdout='',
        stderr='',
        rc='',
        start='',
        end='',
        delta='',
    )

    if module.check_mode:
        return result

    startd = datetime.datetime.now()

    rc, out, err = module.run_command(cmd, encoding=None)

    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        cmd=cmd,
        stdout=out.rstrip(b"\r\n"),
        stderr=err.rstrip(b"\r\n"),
        rc=rc,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        changed=True,
    )

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
