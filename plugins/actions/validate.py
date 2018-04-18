
from ansible.plugins.action import ActionBase

import notario
from notario.exceptions import Invalid
from notario.validators import types, chainable
from notario.store import store as notario_store

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        # we must use vars, since task_vars will have un-processed variables
        host_vars = task_vars['vars']
        host = host_vars['ansible_hostname']
        mode = self._task.args.get('mode', 'permissive')

        self._supports_check_mode = False # XXX ?
        self._supports_async = True

        result = {}
        result['_ansible_verbose_always'] = True

        try:
            notario.validate(host_vars, install_options, defined_keys=True)

            if host_vars["ceph_origin"] == "repository":
                notario.validate(host_vars, ceph_origin_repository, defined_keys=True)

                if host_vars["ceph_repository"] == "community":
                    notario.validate(host_vars, ceph_repository_community, defined_keys=True)

                if host_vars["ceph_repository"] == "rhcs":
                    notario.validate(host_vars, ceph_repository_rhcs, defined_keys=True)

                if host_vars["ceph_repository"] == "dev":
                    notario.validate(host_vars, ceph_repository_dev, defined_keys=True)

            # store these values because one must be defined and the validation method
            # will need access to all three through the store
            notario_store["monitor_address"] = host_vars.get("monitor_address", None)
            notario_store["monitor_address_block"] = host_vars.get("monitor_address_block", None)
            notario_store["monitor_interface"] = host_vars.get("monitor_interface", None)

            notario.validate(host_vars, monitor_options, defined_keys=True)

        except Invalid as error:
            display.vvvv("Notario Failure: %s" % str(error))
            display.warning("[%s] Validation failed for variable: %s" % (host, error.path[0]))
            msg = "Invalid variable assignment in host: %s\n" % host
            msg += "    %s = %s\n" % (error.path, error.path)
            msg += "    %s   %s\n" % (" " * len(str(error.path)), "^" * len(str(error.path)))
            msg += "Reason: %s" % error.reason
            result['failed'] = mode == 'strict'
            result['msg'] = msg
            result['stderr_lines'] = msg.split('\n')

        return result

# Schemas


def osd_objectstore_choices(value):
    assert value in ['bluestore', 'filestore'], "osd_objectstore must be either 'bluestore' or 'filestore'"


def ceph_origin_choices(value):
    assert value in ['repository', 'distro', 'local'], "ceph_origin must be either 'repository', 'distro' or 'local'"


def ceph_repository_choices(value):
    assert value in ['community', 'rhcs', 'dev'], "ceph_repository must be either 'community', 'rhcs' or 'dev'"


def ceph_repository_type_choices(value):
    assert value in ['cdn', 'iso'], "ceph_repository_type must be either 'cdn' or 'iso'"


def validate_monitor_options(value):
    """
    Either monitor_address, monitor_address_block or monitor_interface must
    be defined.
    """
    monitor_address_given = notario_store["monitor_address"] != "0.0.0.0"
    monitor_address_block_given = notario_store["monitor_address_block"] != "subnet"
    monitor_interface_given = notario_store["monitor_interface"] != "interface"

    msg = "Either monitor_address, monitor_address_block or monitor_interface must be provided"

    assert any(monitor_address_given, monitor_address_block_given, monitor_interface_given), msg


install_options = (
    ("ceph_origin", ceph_origin_choices),
    ('osd_objectstore', osd_objectstore_choices),
)

ceph_origin_repository = ("ceph_repository", ceph_repository_choices)

ceph_repository_community = (
    ("ceph_mirror", types.string),
    ("ceph_stable_key", types.string),
    ("ceph_stable_release", types.string),
    ("ceph_stable_repo", types.string),
)

ceph_repository_rhcs = (
    ("ceph_repository_type", ceph_repository_type_choices),
    ("ceph_rhcs_version", chainable.AnyIn(types.string, types.integer)),
)

ceph_repository_dev = (
    ("ceph_dev_branch", types.string),
    ("ceph_dev_sha1", types.string),
)

monitor_options = (
    ("cluster_network", types.string),
    ("fsid", types.string),
    ("public_network", types.string),
    ("monitor_address", validate_monitor_options),
    ("monitor_address_block", validate_monitor_options),
    ("monitor_interface", validate_monitor_options),
)
