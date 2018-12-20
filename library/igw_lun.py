#!/usr/bin/env python

__author__ = 'pcuzner@redhat.com'

DOCUMENTATION = """
---
module: igw_lun
short_description: Manage ceph rbd images to present as iscsi LUNs to clients
description:
  - This module calls the 'lun' configuration management module installed
    on the iscsi gateway node(s). The lun module handles the creation and resize  # noqa E501
    of rbd images, and then maps these rbd devices to the gateway node(s) to be
    exposed through the kernel's LIO target.

    To support module debugging, this module logs to /var/log/ansible-module-igw_config.log  # noqa E501
    on the target machine(s).

option:
  pool:
    description:
      - The ceph pool where the image should exist or be created in.

        NOTE - The pool *must* exist prior to the Ansible run.

    required: true

  image:
    description:
      - this is the rbd image name to create/resize - if the rbd does not exist it
        is created for you with the settings optimised for exporting over iscsi.
    required: true

  size:
    description:
      - The size of the rbd image to create/resize. The size is numeric suffixed by
        G or T (GB or TB). Increasing the size of a LUN is supported, but if a size
        is provided that is smaller that the current size, the request is simply ignored.

        e.g. 100G
    required: true

  host:
    description:
      - the host variable defines the name of the gateway node that will be
        the allocation host for this rbd image. RBD creation and resize can
        only be performed by one gateway, the other gateways in the
        configuration will wait for the operation to complete.
    required: true

  features:
    description:
      - placeholder to potentially allow different rbd features to be set at
        allocation time by Ansible. NOT CURRENTLY USED
    required: false

  state:
    description:
      - desired state for this LUN - absent or present. For a state='absent'
      request, the lun module will verify that the rbd image is not allocated to
      a client. As long as the rbd image is not in use, the LUN definition will be
      removed from LIO, unmapped from all gateways AND DELETED.

      USE WITH CARE!
    required: true

requirements: ['ceph-iscsi-config']

author:
  - 'Paul Cuzner'

"""
import os  # noqa E402
import logging  # noqa E402
from logging.handlers import RotatingFileHandler  # noqa E402

from ansible.module_utils.basic import *  # noqa E402

from ceph_iscsi_config.lun import LUN  # noqa E402
from ceph_iscsi_config.utils import valid_size  # noqa E402
import ceph_iscsi_config.settings as settings  # noqa E402

# the main function is called ansible_main to allow the call stack
# to be checked to determine whether the call to the ceph_iscsi_config
# modules is from ansible or not


def ansible_main():

    # Define the fields needs to create/map rbd's the the host(s)
    # NB. features and state are reserved/unused
    fields = {
        "pool": {"required": False, "default": "rbd", "type": "str"},
        "image": {"required": True, "type": "str"},
        "size": {"required": True, "type": "str"},
        "host": {"required": True, "type": "str"},
        "features": {"required": False, "type": "str"},
        "state": {
            "required": False,
            "default": "present",
            "choices": ['present', 'absent'],
            "type": "str"
        },
    }

    # not supporting check mode currently
    module = AnsibleModule(argument_spec=fields,  # noqa F405
                           supports_check_mode=False)

    pool = module.params["pool"]
    image = module.params['image']
    size = module.params['size']
    allocating_host = module.params['host']
    desired_state = module.params['state']

    ################################################
    # Validate the parameters passed from Ansible  #
    ################################################
    if not valid_size(size):
        logger.critical("image '{}' has an invalid size specification '{}' "
                        "in the ansible configuration".format(image,
                                                              size))
        module.fail_json(msg="(main) Unable to use the size parameter '{}' "
                             "for image '{}' from the playbook - "
                             "must be a number suffixed by M,G "
                             "or T".format(size,
                                           image))

    # define a lun object and perform some initial parameter validation
    lun = LUN(logger, pool, image, size, allocating_host)
    if lun.error:
        module.fail_json(msg=lun.error_msg)

    logger.info("START - LUN configuration started for {}/{}".format(pool,
                                                                     image))

    # attempt to create/allocate the LUN for LIO
    lun.manage(desired_state)
    if lun.error:
        module.fail_json(msg=lun.error_msg)

    if lun.num_changes == 0:
        logger.info("END   - No changes needed")
    else:
        logger.info("END   - {} configuration changes "
                    "made".format(lun.num_changes))

    module.exit_json(changed=(lun.num_changes > 0),
                     meta={"msg": "Configuration updated"})


if __name__ == '__main__':

    module_name = os.path.basename(__file__).replace('ansible_module_', '')
    logger = logging.getLogger(os.path.basename(module_name))
    logger.setLevel(logging.DEBUG)
    handler = RotatingFileHandler('/var/log/ansible-module-igw_config.log',
                                  maxBytes=5242880,
                                  backupCount=7)
    log_fmt = logging.Formatter('%(asctime)s %(name)s %(levelname)-8s : '
                                '%(message)s')
    handler.setFormatter(log_fmt)
    logger.addHandler(handler)

    # initialise global variables used by all called modules
    # e.g. ceph conffile, keyring etc
    settings.init()

    ansible_main()
