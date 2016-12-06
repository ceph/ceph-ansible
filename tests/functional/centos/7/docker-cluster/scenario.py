# Basic information about ceph and its configuration
ceph = {
    'releases': ['infernalis', 'jewel'],
    'cluster_name': 'test',
    'subnet': '192.168.15',
}

# remote nodes to test, with anything specific to them that might be useful for
# tests to get. Each one of these can get requested as a py.test fixture to
# validate information.
nodes = {
    'mon0': {
        'username': 'vagrant',
        'components': ['conf_tests']
    },
    'mon1': {
        'username': 'vagrant',
        'components': ['conf_tests']
    },
    'mon2': {
        'username': 'vagrant',
        'components': ['conf_tests']
    },
    'osd0': {
        'username': 'vagrant',
        'components': []
    },
    'mds0': {
        'username': 'vagrant',
        'components': []
    },
    'rgw0': {
        'username': 'vagrant',
        'components': []
    },
}
