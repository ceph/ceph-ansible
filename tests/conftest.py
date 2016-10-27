import os

import pytest
import imp


def pytest_addoption(parser):
    default = 'scenario.py'
    parser.addoption(
        "--scenario",
        action="store",
        default=default,
        help="YAML file defining scenarios to test. Currently defaults to: %s" % default
    )


def load_scenario_config(filepath, **kw):
    '''
    Creates a configuration dictionary from a file.

    :param filepath: The path to the file.
    '''

    abspath = os.path.abspath(os.path.expanduser(filepath))
    conf_dict = {}
    if not os.path.isfile(abspath):
        raise RuntimeError('`%s` is not a file.' % abspath)

    # First, make sure the code will actually compile (and has no SyntaxErrors)
    with open(abspath, 'rb') as f:
        compiled = compile(f.read(), abspath, 'exec')

    # Next, attempt to actually import the file as a module.
    # This provides more verbose import-related error reporting than exec()
    absname, _ = os.path.splitext(abspath)
    basepath, module_name = absname.rsplit(os.sep, 1)
    imp.load_module(
        module_name,
        *imp.find_module(module_name, [basepath])
    )

    # If we were able to import as a module, actually exec the compiled code
    exec(compiled, globals(), conf_dict)
    conf_dict['__file__'] = abspath
    return conf_dict


def pytest_configure_node(node):
    node_id = node.slaveinput['slaveid']
    scenario_path = os.path.abspath(node.config.getoption('--scenario'))
    scenario = load_scenario_config(scenario_path)
    node.slaveinput['node_config'] = scenario['nodes'][node_id]
    node.slaveinput['scenario_config'] = scenario


@pytest.fixture(scope='session')
def node_config(request):
    return request.config.slaveinput['node_config']


@pytest.fixture(scope="session")
def scenario_config(request):
    return request.config.slaveinput['scenario_config']


def pytest_report_header(config):
    """
    Hook to add extra information about the execution environment and to be
    able to debug what did the magical args got expanded to
    """
    lines = []
    scenario_path = str(config.rootdir.join(config.getoption('--scenario')))
    if not config.remote_execution:
        lines.append('execution environment: local')
    else:
        lines.append('execution environment: remote')
        lines.append('loaded scenario: %s' % scenario_path)
    lines.append('expanded args: %s' % config.extended_args)
    return lines


def pytest_cmdline_preparse(args, config):
    # Note: we can only do our magical args expansion if we aren't already in
    # a remote node via xdist/execnet so return quickly if we can't do magic.
    # TODO: allow setting an environment variable that helps to skip this kind
    # of magical argument expansion
    if os.getcwd().endswith('pyexecnetcache'):
        return

    scenario_path = os.path.abspath(config.getoption('--scenario'))

    scenarios = load_scenario_config(scenario_path, args=args)
    rsync_dir = os.path.dirname(str(config.rootdir.join('functional')))
    test_path = str(config.rootdir.join('functional/tests'))
    nodes = []
    config.remote_execution = True
    for node in scenarios.get('nodes', []):
        nodes.append('--tx')
        nodes.append('vagrant_ssh={node_name}//id={node_name}'.format(node_name=node))
    args[:] = args + ['--max-slave-restart', '0', '--dist=each'] + nodes + ['--rsyncdir', rsync_dir, test_path]
    config.extended_args = ' '.join(args)
