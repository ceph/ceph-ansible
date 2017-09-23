#!/usr/bin/env python

__author__ = 'pcuzner@redhat.com'

DOCUMENTATION = """
---
module: igw_client
short_description: Manage iscsi gateway client definitions
description:
  - This module calls the 'client' configuration management module installed
    on the iscsi gateway node to handle the definition of iscsi clients on the
    gateway(s). This definition will setup iscsi authentication (e.g. chap),
    and mask the required rbd images to the client.

    The 'client' configuration module is provided by ceph-iscsi-config
    rpm which is installed on the gateway nodes.

    To support module debugging, this module logs to
    /var/log/ansible-module-igw_config.log on the target machine(s).

option:
  client_iqn:
    description:
      - iqn of the client machine which should be connected or removed from the
        iscsi gateway environment
    required: true

  image_list:
    description:
      - comma separated string providing the rbd images that this
        client definition should have. The rbd images provided must use the
        following format <pool_name>.<rbd_image_name>
        e.g. rbd.disk1,rbd.disk2
    required: true

  chap:
    description:
      - chap credentials for the client to authenticate to the gateways
        to gain access to the exported rbds (LUNs). The credentials is a string
        value of the form 'username/password'. The iscsi client must then use
        these settings to gain access to any LUN resources.
    required: true

  state:
    description:
      - desired state for this client - absent or present
    required: true

requirements: ['ceph-iscsi-config']

author:
  - 'Paul Cuzner'

"""

import os
import logging
from logging.handlers import RotatingFileHandler
from ansible.module_utils.basic import *

from ceph_iscsi_config.client import GWClient
import ceph_iscsi_config.settings as settings

# the main function is called ansible_main to allow the call stack
# to be checked to determine whether the call to the ceph_iscsi_config
# modules is from ansible or not
def ansible_main():

    fields = {
        "client_iqn": {"required": True, "type": "str"},
        "image_list": {"required": True, "type": "str"},
        "chap": {"required": True, "type": "str"},
        "state": {
            "required": True,
            "choices": ['present', 'absent'],
            "type": "str"
            },
        }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)

    client_iqn = module.params['client_iqn']

    if module.params['image_list']:
        image_list = module.params['image_list'].split(',')
    else:
        image_list = []

    chap = module.params['chap']
    desired_state = module.params['state']

    logger.info("START - Client configuration started : {}".format(client_iqn))

    # The client is defined using the GWClient class. This class handles
    # client attribute updates, rados configuration object updates and LIO
    # settings. Since the logic is external to this custom module, clients
    # can be created/deleted by other methods in the same manner.
    client = GWClient(logger, client_iqn, image_list, chap)
    if client.error:
        module.fail_json(msg=client.error_msg)

    client.manage(desired_state)
    if client.error:
        module.fail_json(msg=client.error_msg)

    logger.info("END   - Client configuration complete - {} "
                "changes made".format(client.change_count))

    changes_made = True if client.change_count > 0 else False

    module.exit_json(changed=changes_made,
                     meta={"msg": "Client definition completed {} "
                                  "changes made".format(client.change_count)})

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
