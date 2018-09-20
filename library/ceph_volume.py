#!/usr/bin/python
import datetime
import json


ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: ceph_volume

short_description: Create ceph OSDs with ceph-volume

description:
    - Using the ceph-volume utility available in Ceph this module
      can be used to create ceph OSDs that are backed by logical volumes.
    - Only available in ceph versions luminous or greater.

options:
    cluster:
        description:
            - The ceph cluster name.
        required: false
        default: ceph
    objectstore:
        description:
            - The objectstore of the OSD, either filestore or bluestore
            - Required if action is 'create'
        required: false
        choices: ['bluestore', 'filestore']
        default: bluestore
    action:
        description:
            - The action to take. Either creating OSDs or zapping devices.
        required: true
        choices: ['create', 'zap', 'batch']
        default: create
    data:
        description:
            - The logical volume name or device to use for the OSD data.
        required: true
    data_vg:
        description:
            - If data is a lv, this must be the name of the volume group it belongs to.
        required: false
    journal:
        description:
            - The logical volume name or partition to use as a filestore journal.
            - Only applicable if objectstore is 'filestore'.
        required: false
    journal_vg:
        description:
            - If journal is a lv, this must be the name of the volume group it belongs to.
            - Only applicable if objectstore is 'filestore'.
        required: false
    db:
        description:
            - A partition or logical volume name to use for block.db.
            - Only applicable if objectstore is 'bluestore'.
        required: false
    db_vg:
        description:
            - If db is a lv, this must be the name of the volume group it belongs to.
            - Only applicable if objectstore is 'bluestore'.
        required: false
    wal:
        description:
            - A partition or logical volume name to use for block.wal.
            - Only applicable if objectstore is 'bluestore'.
        required: false
    wal_vg:
        description:
            - If wal is a lv, this must be the name of the volume group it belongs to.
            - Only applicable if objectstore is 'bluestore'.
        required: false
    crush_device_class:
        description:
            - Will set the crush device class for the OSD.
        required: false
    dmcrypt:
        description:
            - If set to True the OSD will be encrypted with dmcrypt.
        required: false
    batch_devices:
        description:
            - A list of devices to pass to the 'ceph-volume lvm batch' subcommand.
            - Only applicable if action is 'batch'.
        required: false
    osds_per_device:
        description:
            - The number of OSDs to create per device.
            - Only applicable if action is 'batch'.
        required: false
        default: 1
    journal_size:
        description:
            - The size in MB of filestore journals.
            - Only applicable if action is 'batch'.
        required: false
        default: 5120
    block_db_size:
        description:
            - The size in bytes of bluestore block db lvs.
            - The default of -1 means to create them as big as possible.
            - Only applicable if action is 'batch'.
        required: false
        default: -1
    report:
        description:
            - If provided the --report flag will be passed to 'ceph-volume lvm batch'.
            - No OSDs will be created.
            - Results will be returned in json format.
            - Only applicable if action is 'batch'.
        required: false


author:
    - Andrew Schoen (@andrewschoen)
'''

EXAMPLES = '''
- name: set up a filestore osd with an lv data and a journal partition
  ceph_volume:
    objectstore: filestore
    data: data-lv
    data_vg: data-vg
    journal: /dev/sdc1

- name: set up a bluestore osd with a raw device for data
  ceph_volume:
    objectstore: bluestore
    data: /dev/sdc

- name: set up a bluestore osd with an lv for data and partitions for block.wal and block.db
  ceph_volume:
    objectstore: bluestore
    data: data-lv
    data_vg: data-vg
    db: /dev/sdc1
    wal: /dev/sdc2
'''


from ansible.module_utils.basic import AnsibleModule


def get_data(data, data_vg):
    if data_vg:
        data = "{0}/{1}".format(data_vg, data)
    return data


def get_journal(journal, journal_vg):
    if journal_vg:
        journal = "{0}/{1}".format(journal_vg, journal)
    return journal


def get_db(db, db_vg):
    if db_vg:
        db = "{0}/{1}".format(db_vg, db)
    return db


def get_wal(wal, wal_vg):
    if wal_vg:
        wal = "{0}/{1}".format(wal_vg, wal)
    return wal


def batch(module):
    cluster = module.params['cluster']
    objectstore = module.params['objectstore']
    batch_devices = module.params['batch_devices']
    crush_device_class = module.params.get('crush_device_class', None)
    dmcrypt = module.params['dmcrypt']
    osds_per_device = module.params['osds_per_device']
    journal_size = module.params['journal_size']
    block_db_size = module.params['block_db_size']
    report = module.params['report']

    if not batch_devices:
        module.fail_json(msg='batch_devices must be provided if action is "batch"', changed=False, rc=1)

    cmd = [
        'ceph-volume',
        '--cluster',
        cluster,
        'lvm',
        'batch',
        '--%s' % objectstore,
        '--yes',
    ]

    if crush_device_class:
        cmd.extend(["--crush-device-class", crush_device_class])

    if dmcrypt:
        cmd.append("--dmcrypt")

    if osds_per_device > 1:
        cmd.extend(["--osds-per-device", osds_per_device])

    if objectstore == "filestore":
        cmd.extend(["--journal-size", journal_size])

    if objectstore == "bluestore" and block_db_size != "-1":
        cmd.extend(["--block-db-size", block_db_size])

    if report:
        cmd.extend([
            "--report",
            "--format=json",
        ])

    cmd.extend(batch_devices)

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


def create_osd(module):
    cluster = module.params['cluster']
    objectstore = module.params['objectstore']
    data = module.params['data']
    data_vg = module.params.get('data_vg', None)
    journal = module.params.get('journal', None)
    journal_vg = module.params.get('journal_vg', None)
    db = module.params.get('db', None)
    db_vg = module.params.get('db_vg', None)
    wal = module.params.get('wal', None)
    wal_vg = module.params.get('wal_vg', None)
    crush_device_class = module.params.get('crush_device_class', None)
    dmcrypt = module.params['dmcrypt']

    cmd = [
        'ceph-volume',
        '--cluster',
        cluster,
        'lvm',
        'create',
        '--%s' % objectstore,
        '--data',
    ]

    data = get_data(data, data_vg)
    cmd.append(data)

    if journal:
        journal = get_journal(journal, journal_vg)
        cmd.extend(["--journal", journal])

    if db:
        db = get_db(db, db_vg)
        cmd.extend(["--block.db", db])

    if wal:
        wal = get_wal(wal, wal_vg)
        cmd.extend(["--block.wal", wal])

    if crush_device_class:
        cmd.extend(["--crush-device-class", crush_device_class])

    if dmcrypt:
        cmd.append("--dmcrypt")

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

    # check to see if osd already exists
    # FIXME: this does not work when data is a raw device
    # support for 'lvm list' and raw devices was added with https://github.com/ceph/ceph/pull/20620 but
    # has not made it to a luminous release as of 12.2.4
    rc, out, err = module.run_command(["ceph-volume", "lvm", "list", data], encoding=None)
    if rc == 0:
        result["stdout"] = "skipped, since {0} is already used for an osd".format(data)
        result['rc'] = 0
        module.exit_json(**result)

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


def zap_devices(module):
    """
    Will run 'ceph-volume lvm zap' on all devices, lvs and partitions
    used to create the OSD. The --destroy flag is always passed so that
    if an OSD was originally created with a raw device or partition for
    'data' then any lvs that were created by ceph-volume are removed.
    """
    data = module.params['data']
    data_vg = module.params.get('data_vg', None)
    journal = module.params.get('journal', None)
    journal_vg = module.params.get('journal_vg', None)
    db = module.params.get('db', None)
    db_vg = module.params.get('db_vg', None)
    wal = module.params.get('wal', None)
    wal_vg = module.params.get('wal_vg', None)

    base_zap_cmd = [
        'ceph-volume',
        'lvm',
        'zap',
        # for simplicity always --destroy. It will be needed
        # for raw devices and will noop for lvs.
        '--destroy',
    ]

    commands = []

    data = get_data(data, data_vg)

    commands.append(base_zap_cmd + [data])

    if journal:
        journal = get_journal(journal, journal_vg)
        commands.append(base_zap_cmd + [journal])

    if db:
        db = get_db(db, db_vg)
        commands.append(base_zap_cmd + [db])

    if wal:
        wal = get_wal(wal, wal_vg)
        commands.append(base_zap_cmd + [wal])

    result = dict(
        changed=True,
        rc=0,
    )
    command_results = []
    for cmd in commands:
        startd = datetime.datetime.now()

        rc, out, err = module.run_command(cmd, encoding=None)

        endd = datetime.datetime.now()
        delta = endd - startd

        cmd_result = dict(
            cmd=cmd,
            stdout_lines=out.split("\n"),
            stderr_lines=err.split("\n"),
            rc=rc,
            start=str(startd),
            end=str(endd),
            delta=str(delta),
        )

        if rc != 0:
            module.fail_json(msg='non-zero return code', **cmd_result)

        command_results.append(cmd_result)

    result["commands"] = command_results

    module.exit_json(**result)


def run_module():
    module_args = dict(
        cluster=dict(type='str', required=False, default='ceph'),
        objectstore=dict(type='str', required=False, choices=['bluestore', 'filestore'], default='bluestore'),
        action=dict(type='str', required=False, choices=['create', 'zap', 'batch'], default='create'),
        data=dict(type='str', required=False),
        data_vg=dict(type='str', required=False),
        journal=dict(type='str', required=False),
        journal_vg=dict(type='str', required=False),
        db=dict(type='str', required=False),
        db_vg=dict(type='str', required=False),
        wal=dict(type='str', required=False),
        wal_vg=dict(type='str', required=False),
        crush_device_class=dict(type='str', required=False),
        dmcrypt=dict(type='bool', required=False, default=False),
        batch_devices=dict(type='list', required=False, default=[]),
        osds_per_device=dict(type='int', required=False, default=1),
        journal_size=dict(type='str', required=False, default="5120"),
        block_db_size=dict(type='str', required=False, default="-1"),
        report=dict(type='bool', required=False, default=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    action = module.params['action']

    if action == "create":
        create_osd(module)
    elif action == "zap":
        zap_devices(module)
    elif action == "batch":
        batch(module)

    module.fail_json(msg='State must either be "present" or "absent".', changed=False, rc=1)


def main():
    run_module()


if __name__ == '__main__':
    main()
