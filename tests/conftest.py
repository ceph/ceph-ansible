import pytest


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
    node_type = ansible_vars["group_names"][0]
    if not request.node.get_marker(node_type) and not request.node.get_marker('all'):
        pytest.skip("Not a valid test for node type: %s" % node_type)

    if request.node.get_marker("journal_collocation") and not ansible_vars.get("journal_collocation"):
        pytest.skip("Scenario is not using journal collocation")

    osd_ids = []
    if node_type == "osds":
        result = Command.check_output('sudo ls /var/lib/ceph/osd/ | grep -oP "\d+$"')
        osd_ids = result.split("\n")

    # I can assume eth1 because I know all the vagrant
    # boxes we test with use that interface
    address = Interface("eth1").addresses[0]
    subnet = ".".join(ansible_vars["public_network"].split(".")[0:-1])
    num_mons = len(ansible_vars["groups"]["mons"])
    cluster_name = ansible_vars.get("cluster", "ceph")
    conf_path = "/etc/ceph/{}.conf".format(cluster_name)
    data = dict(
        address=address,
        subnet=subnet,
        vars=ansible_vars,
        osd_ids=osd_ids,
        num_mons=num_mons,
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
