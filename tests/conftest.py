import pytest
import os


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
    ceph_stable_release = os.environ.get("CEPH_STABLE_RELEASE", "luminous")
    group_names = ansible_vars["group_names"]
    docker = ansible_vars.get("docker")
    osd_auto_discovery = ansible_vars.get("osd_auto_discovery")
    lvm_scenario = ansible_vars.get("osd_scenario") == 'lvm'
    ceph_release_num = {
        'jewel': 10,
        'kraken': 11,
        'luminous': 12,
        'mimic': 13,
        'dev': 99
    }

    # capture the initial/default state
    test_is_applicable = False
    for marker in request.node.iter_markers():
        if marker.name in group_names or marker.name == 'all':
            test_is_applicable = True
            break
    # Check if any markers on the test method exist in the nodes group_names. If they do not, this test is not valid for the node being tested.
    if not test_is_applicable:
        reason = "%s: Not a valid test for node type: %s" % (request.function, group_names)
        pytest.skip(reason)

    if request.node.get_closest_marker("no_lvm_scenario") and lvm_scenario:
        pytest.skip("Not a valid test for lvm scenarios")

    if not lvm_scenario and request.node.get_closest_marker("lvm_scenario"):
        pytest.skip("Not a valid test for non-lvm scenarios")

    if request.node.get_closest_marker("no_docker") and docker:
        pytest.skip(
            "Not a valid test for containerized deployments or atomic hosts")

    if request.node.get_closest_marker("docker") and not docker:
        pytest.skip(
            "Not a valid test for non-containerized deployments or atomic hosts")  # noqa E501

    if "mgrs" in group_names and ceph_stable_release == "jewel":
        pytest.skip("mgr nodes can not be tested with ceph release jewel")

    if "nfss" in group_names and ceph_stable_release == "jewel":
        pytest.skip("nfs nodes can not be tested with ceph release jewel")

    if group_names == ["iscsigws"] and ceph_stable_release == "jewel":
        pytest.skip("iscsigws nodes can not be tested with ceph release jewel")  # noqa E501

    if request.node.get_closest_marker("from_luminous") and ceph_release_num[ceph_stable_release] < ceph_release_num['luminous']:  # noqa E501
        pytest.skip(
            "This test is only valid for releases starting from Luminous and above")  # noqa E501

    if request.node.get_closest_marker("before_luminous") and ceph_release_num[ceph_stable_release] >= ceph_release_num['luminous']:  # noqa E501
        pytest.skip("This test is only valid for release before Luminous")

    journal_collocation_test = ansible_vars.get("osd_scenario") == "collocated"
    if request.node.get_closest_marker("journal_collocation") and not journal_collocation_test:  # noqa E501
        pytest.skip("Scenario is not using journal collocation")

    osd_ids = []
    osds = []
    cluster_address = ""
    # I can assume eth1 because I know all the vagrant
    # boxes we test with use that interface
    address = host.interface("eth1").addresses[0]
    subnet = ".".join(ansible_vars["public_network"].split(".")[0:-1])
    num_mons = len(ansible_vars["groups"]["mons"])
    if osd_auto_discovery:
        num_devices = 3
    else:
        num_devices = len(ansible_vars.get("devices", []))
    if not num_devices:
        num_devices = len(ansible_vars.get("lvm_volumes", []))
    cluster_name = ansible_vars.get("cluster", "ceph")
    conf_path = "/etc/ceph/{}.conf".format(cluster_name)
    if "osds" in group_names:
        # I can assume eth2 because I know all the vagrant
        # boxes we test with use that interface. OSDs are the only
        # nodes that have this interface.
        cluster_address = host.interface("eth2").addresses[0]
        cmd = host.run('sudo ls /var/lib/ceph/osd/ | sed "s/.*-//"')
        if cmd.rc == 0:
            osd_ids = cmd.stdout.rstrip("\n").split("\n")
            osds = osd_ids
            if docker:
                osds = []
                for device in ansible_vars.get("devices", []):
                    real_dev = host.run("sudo readlink -f %s" % device)
                    real_dev_split = real_dev.stdout.split("/")[-1]
                    osds.append(real_dev_split)

    data = dict(
        address=address,
        subnet=subnet,
        vars=ansible_vars,
        osd_ids=osd_ids,
        num_mons=num_mons,
        num_devices=num_devices,
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
        else:
            item.add_marker(pytest.mark.all)

        if "journal_collocation" in test_path:
            item.add_marker(pytest.mark.journal_collocation)
