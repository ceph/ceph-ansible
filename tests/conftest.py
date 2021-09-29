import pytest
import os


def str_to_bool(val):
    try:
        val = val.lower()
    except AttributeError:
        val = str(val).lower()
    if val == 'true':
        return True
    elif val == 'false':
        return False
    else:
        raise ValueError("Invalid input value: %s" % val)


@pytest.fixture(scope="module")
def setup(host):
    cluster_address = ""
    osd_ids = []
    osds = []

    ansible_vars = host.ansible.get_variables()
    ansible_facts = host.ansible("setup")

    docker = ansible_vars.get("docker")
    container_binary = ansible_vars.get("container_binary", "")
    osd_auto_discovery = ansible_vars.get("osd_auto_discovery")
    group_names = ansible_vars["group_names"]

    ansible_distribution = ansible_facts["ansible_facts"]["ansible_distribution"]

    if ansible_distribution == "CentOS":
        public_interface = "eth1"
        cluster_interface = "eth2"
    else:
        public_interface = "ens6"
        cluster_interface = "ens7"

    subnet = ".".join(ansible_vars["public_network"].split(".")[0:-1])
    num_mons = len(ansible_vars["groups"].get('mons', []))
    if osd_auto_discovery:
        num_osds = 3
    else:
        num_osds = len(ansible_vars.get("devices", []))
    if not num_osds:
        num_osds = len(ansible_vars.get("lvm_volumes", []))
    osds_per_device = ansible_vars.get("osds_per_device", 1)
    num_osds = num_osds * osds_per_device

    # If number of devices doesn't map to number of OSDs, allow tests to define
    # that custom number, defaulting it to ``num_devices``
    num_osds = ansible_vars.get('num_osds', num_osds)
    cluster_name = ansible_vars.get("cluster", "ceph")
    conf_path = "/etc/ceph/{}.conf".format(cluster_name)
    if "osds" in group_names:
        cluster_address = host.interface(cluster_interface).addresses[0]
        cmd = host.run('sudo ls /var/lib/ceph/osd/ | sed "s/.*-//"')
        if cmd.rc == 0:
            osd_ids = cmd.stdout.rstrip("\n").split("\n")
            osds = osd_ids

    address = host.interface(public_interface).addresses[0]

    if docker and not container_binary:
        container_binary = "podman"

    data = dict(
        cluster_name=cluster_name,
        subnet=subnet,
        osd_ids=osd_ids,
        num_mons=num_mons,
        num_osds=num_osds,
        address=address,
        osds=osds,
        conf_path=conf_path,
        public_interface=public_interface,
        cluster_interface=cluster_interface,
        cluster_address=cluster_address,
        container_binary=container_binary)

    return data


@pytest.fixture()
def node(host, request):
    """
    This fixture represents a single node in the ceph cluster. Using the
    host.ansible fixture provided by testinfra it can access all the ansible
    variables provided to it by the specific test scenario being ran.

    You must include this fixture on any tests that operate on specific type
    of node because it contains the logic to manage which tests a node
    should run.
    """
    ansible_vars = host.ansible.get_variables()
    # tox will pass in this environment variable. we need to do it this way
    # because testinfra does not collect and provide ansible config passed in
    # from using --extra-vars
    ceph_stable_release = os.environ.get("CEPH_STABLE_RELEASE", "octopus")
    rolling_update = os.environ.get("ROLLING_UPDATE", "False")
    group_names = ansible_vars["group_names"]
    docker = ansible_vars.get("docker")
    dashboard = ansible_vars.get("dashboard_enabled", True)
    nfs_file_gw = ansible_vars.get("nfs_file_gw")
    nfs_obj_gw = ansible_vars.get("nfs_obj_gw")
    radosgw_num_instances = ansible_vars.get("radosgw_num_instances", 1)
    ceph_release_num = {
        'jewel': 10,
        'kraken': 11,
        'luminous': 12,
        'mimic': 13,
        'nautilus': 14,
        'octopus': 15,
        'pacific': 16,
        'dev': 99
    }

    # capture the initial/default state
    test_is_applicable = False
    for marker in request.node.iter_markers():
        if marker.name in group_names or marker.name == 'all':
            test_is_applicable = True
            break
    # Check if any markers on the test method exist in the nodes group_names.
    # If they do not, this test is not valid for the node being tested.
    if not test_is_applicable:
        reason = "%s: Not a valid test for node type: %s" % (
            request.function, group_names)
        pytest.skip(reason)

    if request.node.get_closest_marker('ceph_crash') and group_names in [['nfss'], ['iscsigws'], ['clients'], ['grafana-server']]:
        pytest.skip('Not a valid test for nfs, client or iscsigw nodes')

    if request.node.get_closest_marker("no_docker") and docker:
        pytest.skip(
            "Not a valid test for containerized deployments or atomic hosts")

    if request.node.get_closest_marker("docker") and not docker:
        pytest.skip(
            "Not a valid test for non-containerized deployments or atomic hosts")  # noqa E501

    if request.node.get_closest_marker("dashboard") and not dashboard:
        pytest.skip(
            "Not a valid test with dashboard disabled")

    if request.node.get_closest_marker("dashboard") and group_names == ['clients']:
        pytest.skip('Not a valid test for client node')

    if request.node.get_closest_marker("no_nfs_file_gw") and nfs_file_gw:
        pytest.skip('Not a valid test for nfs+cephfs node')

    if request.node.get_closest_marker("no_nfs_obj_gw") and nfs_obj_gw:
        pytest.skip('Not a valid test for nfs+rgw node')

    data = dict(
        vars=ansible_vars,
        docker=docker,
        ceph_stable_release=ceph_stable_release,
        ceph_release_num=ceph_release_num,
        rolling_update=rolling_update,
        radosgw_num_instances=radosgw_num_instances,
        nfs_file_gw=nfs_file_gw,
        nfs_obj_gw=nfs_obj_gw,
    )
    return data


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        test_path = item.location[0]
        if "mon" in test_path:
            item.add_marker(pytest.mark.mons)
        elif "osd" in test_path:
            item.add_marker(pytest.mark.osds)
        elif "mds" in test_path:
            item.add_marker(pytest.mark.mdss)
        elif "mgr" in test_path:
            item.add_marker(pytest.mark.mgrs)
        elif "rbd-mirror" in test_path:
            item.add_marker(pytest.mark.rbdmirrors)
        elif "rgw" in test_path:
            item.add_marker(pytest.mark.rgws)
        elif "nfs" in test_path:
            item.add_marker(pytest.mark.nfss)
        elif "iscsi" in test_path:
            item.add_marker(pytest.mark.iscsigws)
        elif "grafana" in test_path:
            item.add_marker(pytest.mark.grafanas)
        else:
            item.add_marker(pytest.mark.all)

        if "journal_collocation" in test_path:
            item.add_marker(pytest.mark.journal_collocation)
