#!/usr/bin/env python
__author__ = 'pcuzner@redhat.com'


DOCUMENTATION = """
---
module: igw_gateway
short_description: Manage the iscsi gateway definition
description:
  - This module calls the 'gateway' configuration management module installed
    on the iscsi gateway node(s) to handle the definition of iscsi gateways.
    The module will configure;
    * the iscsi target and target portal group (TPG)
    * rbd maps to the gateway and registration of those rbds as LUNs to the
      kernels LIO subsystem

    The actual configuration modules are provided by ceph-iscsi-config rpm
    which is installed on the gateway nodes.

    To support module debugging, this module logs to
    /var/log/ansible-module-igw_config.log on the target machine(s).

option:
  gateway_iqn:
    description:
      - iqn that all gateway nodes will use to present a common system image
        name to iscsi clients
    required: true

  gateway_ip_list:
    description:
      - comma separated string providing the IP addresses that will be used
        as iSCSI portal IPs to accept iscsi client connections. Each IP address
        should equate to an IP on a gateway node - typically dedicated to iscsi
        traffic. The order of the IP addresses determines the TPG sequence
        within the target definition - so once defined, new gateways can be
        added but *must* be added to the end of this list to preserve the tpg
        sequence

        e.g. 192.168.122.101,192.168.122.103
    required: true

  mode:
    description:
      - mode in which to run the gateway module. Two modes are supported
        target ... define the iscsi target iqn, tpg's and portals
        map ...... map luns to the tpg's, and also define the ALUA path setting
                   for each LUN (activeOptimized/activenonoptimized)
    required: true


requirements: ['ceph-iscsi-config']

author:
  - 'Paul Cuzner'

"""

import os  # noqa E402
import logging  # noqa E402

from logging.handlers import RotatingFileHandler  # noqa E402
from ansible.module_utils.basic import *  # noqa E402

import ceph_iscsi_config.settings as settings  # noqa E402
from ceph_iscsi_config.common import Config  # noqa E402

from ceph_iscsi_config.gateway import GWTarget  # noqa E402
from ceph_iscsi_config.utils import valid_ip  # noqa E402


# the main function is called ansible_main to allow the call stack
# to be checked to determine whether the call to the ceph_iscsi_config
# modules is from ansible or not
def ansible_main():
    # Configures the gateway on the host. All images defined are added to
    # the default tpg for later allocation to clients
    fields = {"gateway_iqn": {"required": True, "type": "str"},
              "gateway_ip_list": {"required": True},    # "type": "list"},
              "mode": {
                  "required": True,
                  "choices": ['target', 'map']
    }
    }

    module = AnsibleModule(argument_spec=fields,  # noqa F405
                           supports_check_mode=False)

    cfg = Config(logger)
    if cfg.config['version'] > 3:
        module.fail_json(msg="Unsupported iscsigws.yml/iscsi-gws.yml setting "
                             "detected. Remove depreciated iSCSI target, LUN, "
                             "client, and gateway settings from "
                             "iscsigws.yml/iscsi-gws.yml. See "
                             "iscsigws.yml.sample for list of supported "
                             "settings")

    gateway_iqn = module.params['gateway_iqn']
    gateway_ip_list = module.params['gateway_ip_list'].split(',')
    mode = module.params['mode']

    if not valid_ip(gateway_ip_list):
        module.fail_json(msg="Invalid gateway IP address(es) provided - port "
                             "22 check failed ({})".format(gateway_ip_list))

    logger.info("START - GATEWAY configuration started - mode {}".format(mode))

    gateway = GWTarget(logger, gateway_iqn, gateway_ip_list)
    if gateway.error:
        logger.critical("(ansible_main) Gateway init failed - "
                        "{}".format(gateway.error_msg))
        module.fail_json(msg="iSCSI gateway initialisation failed "
                             "({})".format(gateway.error_msg))

    gateway.manage(mode)

    if gateway.error:
        logger.critical("(main) Gateway creation or load failed, "
                        "unable to continue")
        module.fail_json(msg="iSCSI gateway creation/load failure "
                             "({})".format(gateway.error_msg))

    logger.info("END - GATEWAY configuration complete")
    module.exit_json(changed=gateway.changes_made,
                     meta={"msg": "Gateway setup complete"})


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
