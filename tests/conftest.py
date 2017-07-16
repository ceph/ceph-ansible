import pytest
import os


@pytest.fixture()
def node(Ansible, Interface, Command, request):
    """
    This fixture represents a single node in the ceph cluster. Using the
    Ansible fixture provided by testinfra it can access all the ansible variables
    provided to it by the specific test scenario being ran.

    You must include this fixture on any tests that operate on specific type of node
    because it contains the logic to manage which tests a node should run.
    """
    ansible_vars = Ansible.get_variables()
    # tox will pass in this environment variable. we need to do it this way
    # because testinfra does not collect and provide ansible config passed in
    # from using --extra-vars
    ceph_stable_release = os.environ.get("CEPH_STABLE_RELEASE", "kraken")
    node_type = ansible_vars["group_names"][0]
    docker = ansible_vars.get("docker")
    if not request.node.get_marker(node_type) and not request.node.get_marker('all'):
        pytest.skip("Not a valid test for node type: %s" % node_type)

    if request.node.get_marker("no_docker") and docker:
        pytest.skip("Not a valid test for containerized deployments or atomic hosts")

    if request.node.get_marker("docker") and not docker:
        pytest.skip("Not a valid test for non-containerized deployments or atomic hosts")

    if node_type == "mgrs" and ceph_stable_release == "jewel":
        pytest.skip("mgr nodes can not be tested with ceph release jewel")

    journal_collocation_test = ansible_vars.get("journal_collocation") or ansible_vars.get("dmcrypt_journal_collocation")
    if request.node.get_marker("journal_collocation") and not journal_collocation_test:
        pytest.skip("Scenario is not using journal collocation")

    osd_ids = []
    osds = []
    cluster_address = ""
    # I can assume eth1 because I know all the vagrant
    # boxes we test with use that interface
    address = Interface("eth1").addresses[0]
    subnet = ".".join(ansible_vars["public_network"].split(".")[0:-1])
    num_mons = len(ansible_vars["groups"]["mons"])
    num_devices = len(ansible_vars["devices"])
    num_osd_hosts = len(ansible_vars["groups"]["osds"])
    total_osds = num_devices * num_osd_hosts
    cluster_name = ansible_vars.get("cluster", "ceph")
    conf_path = "/etc/ceph/{}.conf".format(cluster_name)
    if node_type == "osds":
        # I can assume eth2 because I know all the vagrant
        # boxes we test with use that interface. OSDs are the only
        # nodes that have this interface.
        cluster_address = Interface("eth2").addresses[0]
        cmd = Command('sudo ls /var/lib/ceph/osd/ | sed "s/.*-//"')
        if cmd.rc == 0:
            osd_ids = cmd.stdout.rstrip("\n").split("\n")
            osds = osd_ids
            if docker:
                osds = [device.split("/")[-1] for device in ansible_vars["devices"]]

    data = dict(
        address=address,
        subnet=subnet,
        vars=ansible_vars,
        osd_ids=osd_ids,
        num_mons=num_mons,
        num_devices=num_devices,
        num_osd_hosts=num_osd_hosts,
        total_osds=total_osds,
        cluster_name=cluster_name,
        conf_path=conf_path,
        cluster_address=cluster_address,
        docker=docker,
        osds=osds,
        ceph_stable_release=ceph_stable_release,
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
        elif "rgw" in test_path:
            item.add_marker(pytest.mark.rgws)
        else:
            item.add_marker(pytest.mark.all)

        if "journal_collocation" in test_path:
            item.add_marker(pytest.mark.journal_collocation)
