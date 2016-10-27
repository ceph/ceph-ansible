# This is the most basic tests that can be executed remotely. It will trigger
# a series of checks for paths, permissions and flags. Whatever is not
# dependant on particular component of ceph should go here (for example,
# nothing related to just OSDs)

# Basic information about ceph and its configuration
ceph = {
    'releases': ['jewel', 'infernalis'],
    'cluster_name': 'ceph'
}

# remote nodes to test, with anything specific to them that might be useful for
# tests to get. Each one of these can get requested as a py.test fixture to
# validate information.
nodes = {
    'mon0': {
        'username': 'vagrant',
        'components': ['mon']
    },
    'osd0': {
        'username': 'vagrant',
        'components': ['osd']
    },
}
