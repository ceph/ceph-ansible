
from ansible.plugins.action import ActionBase
from distutils.version import LooseVersion

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

try:
    import notario
except ImportError:
    msg = "The python-notario library is missing. Please install it on the node you are running ceph-ansible to continue."
    display.error(msg)
    raise SystemExit(msg)

if LooseVersion(notario.__version__) < LooseVersion("0.0.13"):
    msg = "The python-notario libary has an incompatible version. Version >= 0.0.13 is needed, current version: %s" % notario.__version__
    display.error(msg)
    raise SystemExit(msg)

from notario.exceptions import Invalid
from notario.validators import types, chainable, iterables
from notario.decorators import optional
from notario.store import store as notario_store


CEPH_RELEASES = ['jewel', 'kraken', 'luminous', 'mimic']


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
            notario_store["groups"] = host_vars["groups"]
            notario_store["containerized_deployment"] = host_vars["containerized_deployment"]
            notario.validate(host_vars, install_options, defined_keys=True)

            if host_vars["ceph_origin"] == "repository" and not host_vars["containerized_deployment"]:
                notario.validate(host_vars, ceph_origin_repository, defined_keys=True)

                if host_vars["ceph_repository"] == "community":
                    notario.validate(host_vars, ceph_repository_community, defined_keys=True)

                if host_vars["ceph_repository"] == "rhcs":
                    notario.validate(host_vars, ceph_repository_rhcs, defined_keys=True)

                if host_vars["ceph_repository"] == "dev":
                    notario.validate(host_vars, ceph_repository_dev, defined_keys=True)

                if host_vars["ceph_repository"] == "uca":
                    notario.validate(host_vars, ceph_repository_uca, defined_keys=True)

            # store these values because one must be defined and the validation method
            # will need access to all three through the store
            notario_store["monitor_address"] = host_vars.get("monitor_address", None)
            notario_store["monitor_address_block"] = host_vars.get("monitor_address_block", None)
            notario_store["monitor_interface"] = host_vars.get("monitor_interface", None)

            if host_vars["mon_group_name"] in host_vars["group_names"]:
                notario.validate(host_vars, monitor_options, defined_keys=True)

            notario_store["radosgw_address"] = host_vars.get("radosgw_address", None)
            notario_store["radosgw_address_block"] = host_vars.get("radosgw_address_block", None)
            notario_store["radosgw_interface"] = host_vars.get("radosgw_interface", None)

            if host_vars["rgw_group_name"] in host_vars["group_names"]:
                notario.validate(host_vars, rados_options, defined_keys=True)

            # validate osd scenario setup
            if host_vars["osd_group_name"] in host_vars["group_names"]:
                notario.validate(host_vars, osd_options, defined_keys=True)
                notario_store['osd_objectstore'] = host_vars["osd_objectstore"]
                if host_vars["osd_scenario"] == "collocated":
                    if not host_vars.get("osd_auto_discovery", False):
                        notario.validate(host_vars, collocated_osd_scenario, defined_keys=True)

                if host_vars["osd_scenario"] == "non-collocated":
                    notario.validate(host_vars, non_collocated_osd_scenario, defined_keys=True)

                if host_vars["osd_scenario"] == "lvm":
                    if host_vars.get("devices"):
                        notario.validate(host_vars, lvm_batch_scenario, defined_keys=True)
                    elif notario_store['osd_objectstore'] == 'filestore':
                        notario.validate(host_vars, lvm_filestore_scenario, defined_keys=True)
                    elif notario_store['osd_objectstore'] == 'bluestore':
                        notario.validate(host_vars, lvm_bluestore_scenario, defined_keys=True)

        except Invalid as error:
            display.vvvv("Notario Failure: %s" % str(error))
            msg = "[{}] Validation failed for variable: {}".format(host, error.path[0])
            display.error(msg)
            reason = "[{}] Reason: {}".format(host, error.reason)
            try:
                if "schema is missing" not in error.message:
                    for i in range(0, len(error.path)):
                        if i == 0:
                            given = "[{}] Given value for {}".format(
                                    host, error.path[0])
                        else:
                            given = given + ": {}".format(error.path[i])
                    display.error(given)
                else:
                    given = ""
                    reason = "[{}] Reason: {}".format(host, error.message)
            except KeyError:
                given = ""
            display.error(reason)
            result['failed'] = mode == 'strict'
            result['msg'] = "\n".join([msg, reason, given])
            result['stderr_lines'] = msg.split('\n')

        return result

# Schemas


def osd_objectstore_choices(value):
    assert value in ['bluestore', 'filestore'], "osd_objectstore must be either 'bluestore' or 'filestore'"


def ceph_origin_choices(value):
    if not notario_store["containerized_deployment"]:
        assert value in ['repository', 'distro', 'local'], "ceph_origin must be either 'repository', 'distro' or 'local'"


def ceph_repository_choices(value):
    msg = "ceph_repository must be either 'community', 'rhcs', 'dev', 'custom' or 'uca'"
    assert value in ['community', 'rhcs', 'dev', 'custom', 'uca'], msg


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

    assert any([monitor_address_given, monitor_address_block_given, monitor_interface_given]), msg


def validate_dmcrypt_bool_value(value):
    assert value in ["true", True, "false", False], "dmcrypt can be set to true/True or false/False (default)"


def validate_osd_auto_discovery_bool_value(value):
    assert value in ["true", True, "false", False], "osd_auto_discovery can be set to true/True or false/False (default)"


def validate_osd_scenarios(value):
    assert value in ["collocated", "non-collocated", "lvm"], "osd_scenario must be set to 'collocated', 'non-collocated' or 'lvm'"


def validate_objectstore(value):
    assert value in ["filestore", "bluestore"], "objectstore must be set to 'filestore' or 'bluestore'"


def validate_ceph_stable_release(value):
    assert value in CEPH_RELEASES, "ceph_stable_release must be set to one of the following: %s" % ", ".join(CEPH_RELEASES)


def validate_rados_options(value):
    """
    Either radosgw_interface, radosgw_address or radosgw_address_block must
    be defined.
    """
    radosgw_address_given = notario_store["radosgw_address"] != "0.0.0.0"
    radosgw_address_block_given = notario_store["radosgw_address_block"] != "subnet"
    radosgw_interface_given = notario_store["radosgw_interface"] != "interface"

    msg = "Either radosgw_address, radosgw_address_block or radosgw_interface must be provided"

    assert any([radosgw_address_given, radosgw_address_block_given, radosgw_interface_given]), msg


install_options = (
    ("ceph_origin", ceph_origin_choices),
    ("containerized_deployment", types.boolean),
    ('osd_objectstore', osd_objectstore_choices),
)

ceph_origin_repository = ("ceph_repository", ceph_repository_choices)

ceph_repository_community = (
    ("ceph_mirror", types.string),
    ("ceph_stable_key", types.string),
    ("ceph_stable_release", validate_ceph_stable_release),
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

ceph_repository_uca = (
    ("ceph_stable_openstack_release_uca", types.string),
    ("ceph_stable_release_uca", types.string),
    ("ceph_stable_repo_uca", types.string),
)

monitor_options = (
    ("cluster_network", types.string),
    ("fsid", types.string),
    ("monitor_address", validate_monitor_options),
    ("monitor_address_block", validate_monitor_options),
    ("monitor_interface", validate_monitor_options),
    ("public_network", types.string),
)

rados_options = (
    ("radosgw_address", validate_rados_options),
    ("radosgw_address_block", validate_rados_options),
    ("radosgw_interface", validate_rados_options),
)

osd_options = (
    (optional("dmcrypt"), validate_dmcrypt_bool_value),
    (optional("osd_auto_discovery"), validate_osd_auto_discovery_bool_value),
    ("osd_scenario", validate_osd_scenarios),
)

collocated_osd_scenario = ("devices", iterables.AllItems(types.string))

non_collocated_osd_scenario = (
    (optional("bluestore_wal_devices"), iterables.AllItems(types.string)),
    (optional("dedicated_devices"), iterables.AllItems(types.string)),
    ("devices", iterables.AllItems(types.string)),
)

lvm_batch_scenario = ("devices", iterables.AllItems(types.string))

lvm_filestore_scenario = ("lvm_volumes", iterables.AllItems((
    (optional('crush_device_class'), types.string),
    ('data', types.string),
    (optional('data_vg'), types.string),
    ('journal', types.string),
    (optional('journal_vg'), types.string),
)))

lvm_bluestore_scenario = ("lvm_volumes", iterables.AllItems((
    (optional('crush_device_class'), types.string),
    ('data', types.string),
    (optional('data_vg'), types.string),
    (optional('db'), types.string),
    (optional('db_vg'), types.string),
    (optional('wal'), types.string),
    (optional('wal_vg'), types.string),
)))
