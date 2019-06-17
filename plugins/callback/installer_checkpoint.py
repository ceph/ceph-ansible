"""Ansible callback plugin to print a summary completion status of installation
phases.
"""
from datetime import datetime
from ansible.plugins.callback import CallbackBase
from ansible import constants as C


class CallbackModule(CallbackBase):
    """This callback summarizes installation phase status."""

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'installer_checkpoint'
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self):
        super(CallbackModule, self).__init__()

    def v2_playbook_on_stats(self, stats):

        # Set the order of the installer phases
        installer_phases = [
            'installer_phase_ceph_mon',
            'installer_phase_ceph_mgr',
            'installer_phase_ceph_osd',
            'installer_phase_ceph_mds',
            'installer_phase_ceph_rgw',
            'installer_phase_ceph_nfs',
            'installer_phase_ceph_rbdmirror',
            'installer_phase_ceph_client',
            'installer_phase_ceph_iscsi_gw',
            'installer_phase_ceph_rgw_loadbalancer',
            'installer_phase_ceph_dashboard',
            'installer_phase_ceph_grafana',
            'installer_phase_ceph_node_exporter',
        ]

        # Define the attributes of the installer phases
        phase_attributes = {
            'installer_phase_ceph_mon': {
                'title': 'Install Ceph Monitor',
                'playbook': 'roles/ceph-mon/tasks/main.yml'
            },
            'installer_phase_ceph_mgr': {
                'title': 'Install Ceph Manager',
                'playbook': 'roles/ceph-mgr/tasks/main.yml'
            },
            'installer_phase_ceph_osd': {
                'title': 'Install Ceph OSD',
                'playbook': 'roles/ceph-osd/tasks/main.yml'
            },
            'installer_phase_ceph_mds': {
                'title': 'Install Ceph MDS',
                'playbook': 'roles/ceph-mds/tasks/main.yml'
            },
            'installer_phase_ceph_rgw': {
                'title': 'Install Ceph RGW',
                'playbook': 'roles/ceph-rgw/tasks/main.yml'
            },
            'installer_phase_ceph_nfs': {
                'title': 'Install Ceph NFS',
                'playbook': 'roles/ceph-nfs/tasks/main.yml'
            },
            'installer_phase_ceph_rbdmirror': {
                'title': 'Install Ceph RBD Mirror',
                'playbook': 'roles/ceph-rbd-mirror/tasks/main.yml'
            },
            'installer_phase_ceph_client': {
                'title': 'Install Ceph Client',
                'playbook': 'roles/ceph-client/tasks/main.yml'
            },
            'installer_phase_ceph_iscsi_gw': {
                'title': 'Install Ceph iSCSI Gateway',
                'playbook': 'roles/ceph-iscsi-gw/tasks/main.yml'
            },
            'installer_phase_ceph_rgw_loadbalancer': {
                'title': 'Install Ceph RGW LoadBalancer',
                'playbook': 'roles/ceph-rgw-loadbalancer/tasks/main.yml'
            },
            'installer_phase_ceph_dashboard': {
                'title': 'Install Ceph Dashboard',
                'playbook': 'roles/ceph-dashboard/tasks/main.yml'
            },
            'installer_phase_ceph_grafana': {
                'title': 'Install Ceph Grafana',
                'playbook': 'roles/ceph-grafana/tasks/main.yml'
            },
            'installer_phase_ceph_node_exporter': {
                'title': 'Install Ceph Node Exporter',
                'playbook': 'roles/ceph-node-exporter/tasks/main.yml'
            },
        }

        # Find the longest phase title
        max_column = 0
        for phase in phase_attributes:
            max_column = max(max_column, len(phase_attributes[phase]['title']))

        if '_run' in stats.custom:
            self._display.banner('INSTALLER STATUS')
            for phase in installer_phases:
                phase_title = phase_attributes[phase]['title']
                padding = max_column - len(phase_title) + 2
                if phase in stats.custom['_run']:
                    phase_status = stats.custom['_run'][phase]['status']
                    phase_time = phase_time_delta(stats.custom['_run'][phase])
                    self._display.display(
                        '{}{}: {} ({})'.format(phase_title, ' ' * padding, phase_status, phase_time),
                        color=self.phase_color(phase_status))
                    if phase_status == 'In Progress' and phase != 'installer_phase_initialize':
                        self._display.display(
                            '\tThis phase can be restarted by running: {}'.format(
                                phase_attributes[phase]['playbook']))

        self._display.display("", screen_only=True)

    def phase_color(self, status):
        """ Return color code for installer phase"""
        valid_status = [
            'In Progress',
            'Complete',
        ]

        if status not in valid_status:
            self._display.warning('Invalid phase status defined: {}'.format(status))

        if status == 'Complete':
            phase_color = C.COLOR_OK
        elif status == 'In Progress':
            phase_color = C.COLOR_ERROR
        else:
            phase_color = C.COLOR_WARN

        return phase_color


def phase_time_delta(phase):
    """ Calculate the difference between phase start and end times """
    time_format = '%Y%m%d%H%M%SZ'
    phase_start = datetime.strptime(phase['start'], time_format)
    if 'end' not in phase:
        # The phase failed so set the end time to now
        phase_end = datetime.now()
    else:
        phase_end = datetime.strptime(phase['end'], time_format)
    delta = str(phase_end - phase_start).split(".")[0]  # Trim microseconds

    return delta
