#!/usr/bin/env python

DOCUMENTATION = """
---
module: igw_purge
short_description: Provide a purge capability to remove an iSCSI gateway
environment
description:
  - This module handles the removal of a gateway configuration from a ceph
    environment.
    The playbook that calls this module prompts the user for the type of purge
    to perform.
    The purge options are;
    all ... purge all LIO configuration *and* delete all defined rbd images
    lio ... purge only the LIO configuration (rbd's are left intact)

    USE WITH CAUTION

    To support module debugging, this module logs to
    /var/log/ansible-module-igw_config.log on each target machine(s).

option:
  mode:
    description:
      - the mode defines the type of purge requested
        gateway ... remove the LIO configuration only
        disks   ... remove the rbd disks defined to the gateway
    required: true

requirements: ['ceph-iscsi-config', 'python-rtslib']

author:
  - 'Paul Cuzner'

"""

import os  # noqa E402
import logging  # noqa E402
import socket  # noqa E402
import rados  # noqa E402
import rbd  # noqa E402

from logging.handlers import RotatingFileHandler  # noqa E402
from ansible.module_utils.basic import *  # noqa E402

import ceph_iscsi_config.settings as settings  # noqa E402
from ceph_iscsi_config.common import Config  # noqa E402
from ceph_iscsi_config.lun import RBDDev  # noqa E402

__author__ = 'pcuzner@redhat.com'


def delete_images(cfg):
    changes_made = False

    for disk_name, disk in cfg.config['disks'].items():
        image = disk['image']

        logger.debug("Deleing image {}".format(image))

        backstore = disk.get('backstore')
        if backstore is None:
            # ceph iscsi-config based.
            rbd_dev = RBDDev(image, 0, disk['pool'])
        else:
            # ceph-iscsi based.
            rbd_dev = RBDDev(image, 0, backstore, disk['pool'])

        try:
            rbd_dev.delete()
        except rbd.ImageNotFound as err:
            # Just log and ignore. If we crashed while purging we could delete
            # the image but not removed it from the config
            logger.debug("Image already deleted.")
        except rbd.ImageHasSnapshots as err:
            logger.error("Image still has snapshots.")
            # Older versions of ceph-iscsi-config do not have a error_msg
            # string.
            if not rbd_dev.error_msg:
                rbd_dev.error_msg = "Image has snapshots."

        if rbd_dev.error:
            if rbd_dev.error_msg:
                logger.error("Could not remove {}. Error: {}. Manually run the "
                             "rbd command line tool to delete.".
                             format(image, rbd_error_msg))
            else:
                logger.error("Could not remove {}. Manually run the rbd "
                             "command line tool to delete.".format(image))
        else:
            changes_made = True

    return changes_made

def delete_gateway_config(cfg):
    ioctx = cfg._open_ioctx()
    try:
        size, mtime = ioctx.stat(cfg.config_name)
    except rados.ObjectNotFound:
        logger.debug("gateway.conf already removed.")
        return false

    try:
        ioctx.remove_object(cfg.config_name)
    except Exception as err:
        module.fail_json(msg="Gateway config object failed: {}".format(err))

    return True


def ansible_main():

    fields = {"mode": {"required": True,
                       "type": "str",
                       "choices": ["gateway", "disks"]
                       }
              }

    module = AnsibleModule(argument_spec=fields,  # noqa F405
                           supports_check_mode=False)

    run_mode = module.params['mode']
    changes_made = False

    logger.info("START - GATEWAY configuration PURGE started, run mode "
                "is {}".format(run_mode))
    cfg = Config(logger)
    #
    # Purge gateway configuration, if the config has gateways
    if run_mode == 'gateway':
        changes_made = delete_gateway_config(cfg)
    elif run_mode == 'disks' and len(cfg.config['disks'].keys()) > 0:
        #
        # Remove the disks on this host, that have been registered in the
        # config object
        changes_made = delete_images(cfg)

    logger.info("END   - GATEWAY configuration PURGE complete")

    module.exit_json(changed=changes_made,
                     meta={"msg": "Purge of iSCSI settings ({}) "
                                  "complete".format(run_mode)})


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

    settings.init()

    ansible_main()
