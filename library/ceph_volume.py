#!/usr/bin/python
import datetime
import copy
import json
import os

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
            - The action to take. Creating OSDs and zapping or querying devices.
        required: true
        choices: ['create', 'zap', 'batch', 'prepare', 'activate', 'list', 'inventory']
        default: create
    data:
        description:
            - The logical volume name or device to use for the OSD data.
        required: true
    data_vg:
        description:
            - If data is a lv, this must be the name of the volume group it belongs to.
        required: false
    osd_fsid:
        description:
            - The OSD FSID
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
            - If db is a lv, this must be the name of the volume group it belongs to.  # noqa E501
            - Only applicable if objectstore is 'bluestore'.
        required: false
    wal:
        description:
            - A partition or logical volume name to use for block.wal.
            - Only applicable if objectstore is 'bluestore'.
        required: false
    wal_vg:
        description:
            - If wal is a lv, this must be the name of the volume group it belongs to.  # noqa E501
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
    containerized:
        description:
            - Wether or not this is a containerized cluster. The value is
            assigned or not depending on how the playbook runs.
        required: false
        default: None
    list:
        description:
            - List potential Ceph LVM metadata on a device
        required: false
    inventory:
        description:
            - List storage device inventory.
        required: false

author:
    - Andrew Schoen (@andrewschoen)
    - Sebastien Han <seb@redhat.com>
'''

EXAMPLES = '''
- name: set up a filestore osd with an lv data and a journal partition
  ceph_volume:
    objectstore: filestore
    data: data-lv
    data_vg: data-vg
    journal: /dev/sdc1
    action: create

- name: set up a bluestore osd with a raw device for data
  ceph_volume:
    objectstore: bluestore
    data: /dev/sdc
    action: create


- name: set up a bluestore osd with an lv for data and partitions for block.wal and block.db  # noqa e501
  ceph_volume:
    objectstore: bluestore
    data: data-lv
    data_vg: data-vg
    db: /dev/sdc1
    wal: /dev/sdc2
    action: create
'''


from ansible.module_utils.basic import AnsibleModule  # noqa 4502


def fatal(message, module):
    '''
    Report a fatal error and exit
    '''

    if module:
        module.fail_json(msg=message, changed=False, rc=1)
    else:
        raise(Exception(message))


def container_exec(binary, container_image):
    '''
    Build the docker CLI to run a command inside a container
    '''
    container_binary = os.getenv('CEPH_CONTAINER_BINARY')
    command_exec = [container_binary, 'run',
                    '--rm', '--privileged', '--net=host', '--ipc=host',
                    '--ulimit', 'nofile=1024:4096',
                    '-v', '/run/lock/lvm:/run/lock/lvm:z',
                    '-v', '/var/run/udev/:/var/run/udev/:z',
                    '-v', '/dev:/dev', '-v', '/etc/ceph:/etc/ceph:z',
                    '-v', '/run/lvm/:/run/lvm/',
                    '-v', '/var/lib/ceph/:/var/lib/ceph/:z',
                    '-v', '/var/log/ceph/:/var/log/ceph/:z',
                    '--entrypoint=' + binary, container_image]
    return command_exec


def build_ceph_volume_cmd(action, container_image, cluster=None):
    '''
    Build the ceph-volume command
    '''

    if container_image:
        binary = 'ceph-volume'
        cmd = container_exec(
            binary, container_image)
    else:
        binary = ['ceph-volume']
        cmd = binary

    if cluster:
        cmd.extend(['--cluster', cluster])

    cmd.extend(action)

    return cmd


def exec_command(module, cmd):
    '''
    Execute command
    '''

    rc, out, err = module.run_command(cmd)
    return rc, cmd, out, err


def is_containerized():
    '''
    Check if we are running on a containerized cluster
    '''

    if 'CEPH_CONTAINER_IMAGE' in os.environ:
        container_image = os.getenv('CEPH_CONTAINER_IMAGE')
    else:
        container_image = None

    return container_image


def get_data(data, data_vg):
    if data_vg:
        data = '{0}/{1}'.format(data_vg, data)
    return data


def get_journal(journal, journal_vg):
    if journal_vg:
        journal = '{0}/{1}'.format(journal_vg, journal)
    return journal


def get_db(db, db_vg):
    if db_vg:
        db = '{0}/{1}'.format(db_vg, db)
    return db


def get_wal(wal, wal_vg):
    if wal_vg:
        wal = '{0}/{1}'.format(wal_vg, wal)
    return wal


def batch(module, container_image):
    '''
    Batch prepare OSD devices
    '''

    # get module variables
    cluster = module.params['cluster']
    objectstore = module.params['objectstore']
    batch_devices = module.params.get('batch_devices', None)
    crush_device_class = module.params.get('crush_device_class', None)
    journal_size = module.params.get('journal_size', None)
    block_db_size = module.params.get('block_db_size', None)
    block_db_devices = module.params.get('block_db_devices', None)
    wal_devices = module.params.get('wal_devices', None)
    dmcrypt = module.params.get('dmcrypt', None)
    osds_per_device = module.params.get('osds_per_device', 1)

    if not osds_per_device:
        fatal('osds_per_device must be provided if action is "batch"', module)

    if osds_per_device < 1:
        fatal('osds_per_device must be greater than 0 if action is "batch"', module)  # noqa E501

    if not batch_devices:
        fatal('batch_devices must be provided if action is "batch"', module)

    # Build the CLI
    action = ['lvm', 'batch']
    cmd = build_ceph_volume_cmd(action, container_image, cluster)
    cmd.extend(['--%s' % objectstore])
    cmd.append('--yes')

    if container_image:
        cmd.append('--prepare')

    if crush_device_class:
        cmd.extend(['--crush-device-class', crush_device_class])

    if dmcrypt:
        cmd.append('--dmcrypt')

    if osds_per_device > 1:
        cmd.extend(['--osds-per-device', str(osds_per_device)])

    if objectstore == 'filestore':
        cmd.extend(['--journal-size', journal_size])

    if objectstore == 'bluestore' and block_db_size != '-1':
        cmd.extend(['--block-db-size', block_db_size])

    cmd.extend(batch_devices)

    if block_db_devices:
        cmd.extend(['--db-devices', ' '.join(block_db_devices)])

    if wal_devices:
        cmd.extend(['--wal-devices', ' '.join(wal_devices)])

    return cmd


def ceph_volume_cmd(subcommand, container_image, cluster=None):
    '''
    Build ceph-volume initial command
    '''

    if container_image:
        binary = 'ceph-volume'
        cmd = container_exec(
            binary, container_image)
    else:
        binary = ['ceph-volume']
        cmd = binary

    if cluster:
        cmd.extend(['--cluster', cluster])

    cmd.append('lvm')
    cmd.append(subcommand)

    return cmd


def prepare_or_create_osd(module, action, container_image):
    '''
    Prepare or create OSD devices
    '''

    # get module variables
    cluster = module.params['cluster']
    objectstore = module.params['objectstore']
    data = module.params['data']
    data_vg = module.params.get('data_vg', None)
    data = get_data(data, data_vg)
    journal = module.params.get('journal', None)
    journal_vg = module.params.get('journal_vg', None)
    db = module.params.get('db', None)
    db_vg = module.params.get('db_vg', None)
    wal = module.params.get('wal', None)
    wal_vg = module.params.get('wal_vg', None)
    crush_device_class = module.params.get('crush_device_class', None)
    dmcrypt = module.params.get('dmcrypt', None)

    # Build the CLI
    action = ['lvm', action]
    cmd = build_ceph_volume_cmd(action, container_image, cluster)
    cmd.extend(['--%s' % objectstore])
    cmd.append('--data')
    cmd.append(data)

    if journal:
        journal = get_journal(journal, journal_vg)
        cmd.extend(['--journal', journal])

    if db:
        db = get_db(db, db_vg)
        cmd.extend(['--block.db', db])

    if wal:
        wal = get_wal(wal, wal_vg)
        cmd.extend(['--block.wal', wal])

    if crush_device_class:
        cmd.extend(['--crush-device-class', crush_device_class])

    if dmcrypt:
        cmd.append('--dmcrypt')

    return cmd


def list_osd(module, container_image):
    '''
    List will detect wether or not a device has Ceph LVM Metadata
    '''

    # get module variables
    cluster = module.params['cluster']
    data = module.params.get('data', None)
    data_vg = module.params.get('data_vg', None)
    data = get_data(data, data_vg)

    # Build the CLI
    action = ['lvm', 'list']
    cmd = build_ceph_volume_cmd(action, container_image, cluster)
    if data:
        cmd.append(data)
    cmd.append('--format=json')

    return cmd

def list_storage_inventory(module, container_image):
    '''
    List storage inventory.
    '''

    action = ['inventory']
    cmd = build_ceph_volume_cmd(action, container_image)
    cmd.append('--format=json')

    return cmd

def activate_osd():
    '''
    Activate all the OSDs on a machine
    '''

    # build the CLI
    action = ['lvm', 'activate']
    container_image = None
    cmd = build_ceph_volume_cmd(action, container_image)
    cmd.append('--all')

    return cmd


def zap_devices(module, container_image):
    '''
    Will run 'ceph-volume lvm zap' on all devices, lvs and partitions
    used to create the OSD. The --destroy flag is always passed so that
    if an OSD was originally created with a raw device or partition for
    'data' then any lvs that were created by ceph-volume are removed.
    '''

    # get module variables
    data = module.params.get('data', None)
    data_vg = module.params.get('data_vg', None)
    journal = module.params.get('journal', None)
    journal_vg = module.params.get('journal_vg', None)
    db = module.params.get('db', None)
    db_vg = module.params.get('db_vg', None)
    wal = module.params.get('wal', None)
    wal_vg = module.params.get('wal_vg', None)
    osd_fsid = module.params.get('osd_fsid', None)

    # build the CLI
    action = ['lvm', 'zap']
    cmd = build_ceph_volume_cmd(action, container_image)
    cmd.append('--destroy')

    if osd_fsid:
        cmd.extend(['--osd-fsid', osd_fsid])

    if data:
        data = get_data(data, data_vg)
        cmd.append(data)

    if journal:
        journal = get_journal(journal, journal_vg)
        cmd.extend([journal])

    if db:
        db = get_db(db, db_vg)
        cmd.extend([db])

    if wal:
        wal = get_wal(wal, wal_vg)
        cmd.extend([wal])

    return cmd


def run_module():
    module_args = dict(
        cluster=dict(type='str', required=False, default='ceph'),
        objectstore=dict(type='str', required=False, choices=[
                         'bluestore', 'filestore'], default='bluestore'),
        action=dict(type='str', required=False, choices=[
                    'create', 'zap', 'batch', 'prepare', 'activate', 'list',
                    'inventory'], default='create'),  # noqa 4502
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
        journal_size=dict(type='str', required=False, default='5120'),
        block_db_size=dict(type='str', required=False, default='-1'),
        block_db_devices=dict(type='list', required=False, default=[]),
        wal_devices=dict(type='list', required=False, default=[]),
        report=dict(type='bool', required=False, default=False),
        containerized=dict(type='str', required=False, default=False),
        osd_fsid=dict(type='str', required=False),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        stdout='',
        stderr='',
        rc='',
        start='',
        end='',
        delta='',
    )

    if module.check_mode:
        return result

    # start execution
    startd = datetime.datetime.now()

    # get the desired action
    action = module.params['action']

    # will return either the image name or None
    container_image = is_containerized()

    # Assume the task's status will be 'changed'
    changed = True

    if action == 'create' or action == 'prepare':
        # First test if the device has Ceph LVM Metadata
        rc, cmd, out, err = exec_command(
            module, list_osd(module, container_image))

        # list_osd returns a dict, if the dict is empty this means
        # we can not check the return code since it's not consistent
        # with the plain output
        # see: http://tracker.ceph.com/issues/36329
        # FIXME: it's probably less confusing to check for rc

        # convert out to json, ansible returns a string...
        try:
            out_dict = json.loads(out)
        except ValueError:
            fatal("Could not decode json output: {} from the command {}".format(out, cmd), module)  # noqa E501

        if out_dict:
            data = module.params['data']
            result['stdout'] = 'skipped, since {0} is already used for an osd'.format(  # noqa E501
            data)
            result['rc'] = 0
            module.exit_json(**result)

        # Prepare or create the OSD
        rc, cmd, out, err = exec_command(
            module, prepare_or_create_osd(module, action, container_image))

    elif action == 'activate':
        if container_image:
            fatal(
                "This is not how container's activation happens, nothing to activate", module)  # noqa E501

        # Activate the OSD
        rc, cmd, out, err = exec_command(
            module, activate_osd())

    elif action == 'zap':
        # Zap the OSD
        rc, cmd, out, err = exec_command(
            module, zap_devices(module, container_image))

    elif action == 'list':
        # List Ceph LVM Metadata on a device
        rc, cmd, out, err = exec_command(
            module, list_osd(module, container_image))

    elif action == 'inventory':
        # List storage device inventory.
        rc, cmd, out, err = exec_command(
            module, list_storage_inventory(module, container_image))

    elif action == 'batch':
        # Batch prepare AND activate OSDs
        report = module.params.get('report', None)

        # Add --report flag for the idempotency test
        report_flags = [
            '--report',
            '--format=json',
        ]

        cmd = batch(module, container_image)
        batch_report_cmd = copy.copy(cmd)
        batch_report_cmd.extend(report_flags)

        # Run batch --report to see what's going to happen
        # Do not run the batch command if there is nothing to do
        rc, cmd, out, err = exec_command(
            module, batch_report_cmd)
        try:
            report_result = json.loads(out)
        except ValueError:
            strategy_change = "strategy changed" in out
            if strategy_change:
                out = json.dumps(
                    {"changed": False, "stdout": out.rstrip("\r\n")})
                rc = 0
                changed = False
            else:
                out = out.rstrip("\r\n")
            result = dict(
                cmd=cmd,
                stdout=out.rstrip('\r\n'),
                stderr=err.rstrip('\r\n'),
                rc=rc,
                changed=changed,
            )
            if strategy_change:
                module.exit_json(**result)
            module.fail_json(msg='non-zero return code', **result)

        if not report:
            # if not asking for a report, let's just run the batch command
            changed = report_result['changed']
            if changed:
                # Batch prepare the OSD
                rc, cmd, out, err = exec_command(
                    module, batch(module, container_image))
        else:
            cmd = batch_report_cmd

    else:
        module.fail_json(
            msg='State must either be "create" or "prepare" or "activate" or "list" or "zap" or "batch" or "inventory".', changed=False, rc=1)  # noqa E501

    endd = datetime.datetime.now()
    delta = endd - startd

    result = dict(
        cmd=cmd,
        start=str(startd),
        end=str(endd),
        delta=str(delta),
        rc=rc,
        stdout=out.rstrip('\r\n'),
        stderr=err.rstrip('\r\n'),
        changed=changed,
    )

    if rc != 0:
        module.fail_json(msg='non-zero return code', **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
