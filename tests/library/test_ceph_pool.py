import os
import sys
import ceph_pool
from mock.mock import patch

sys.path.append('./library')
fake_user = 'client.admin'
fake_user_key = '/etc/ceph/ceph.client.admin.keyring'
fake_pool_name = 'foo'
fake_cluster_name = 'ceph'
fake_container_image_name = 'quay.ceph.io/ceph-ci/daemon:latest-octopus'


@patch.dict(os.environ, {'CEPH_CONTAINER_BINARY': 'podman'})
class TestCephPoolModule(object):
    def setup_method(self):
        self.fake_running_pool_details = {
            'pool_id': 39,
            'pool_name': 'foo2',
            'create_time': '2020-05-12T12:32:03.696673+0000',
            'flags': 32769,
            'flags_names': 'hashpspool,creating',
            'type': 1,
            'size': 2,
            'min_size': 1,
            'crush_rule': 0,
            'object_hash': 2,
            'pg_autoscale_mode': 'on',
            'pg_num': 32,
            'pg_placement_num': 32,
            'pg_placement_num_target': 32,
            'pg_num_target': 32,
            'pg_num_pending': 32,
            'last_pg_merge_meta': {
                'source_pgid': '0.0',
                'ready_epoch': 0,
                'last_epoch_started': 0,
                'last_epoch_clean': 0,
                'source_version': "0'0",
                'target_version': "0'0"
            },
            'last_change': '109',
            'last_force_op_resend': '0',
            'last_force_op_resend_prenautilus': '0',
            'last_force_op_resend_preluminous': '0',
            'auid': 0,
            'snap_mode': 'selfmanaged',
            'snap_seq': 0,
            'snap_epoch': 0,
            'pool_snaps': [],
            'removed_snaps': '[]',
            'quota_max_bytes': 0,
            'quota_max_objects': 0,
            'tiers': [],
            'tier_of': -1,
            'read_tier': -1,
            'write_tier': -1,
            'cache_mode': 'none',
            'target_max_bytes': 0,
            'target_max_objects': 0,
            'cache_target_dirty_ratio_micro': 400000,
            'cache_target_dirty_high_ratio_micro': 600000,
            'cache_target_full_ratio_micro': 800000,
            'cache_min_flush_age': 0,
            'cache_min_evict_age': 0,
            'erasure_code_profile': '',
            'hit_set_params': {
                'type': 'none'
            },
            'hit_set_period': 0,
            'hit_set_count': 0,
            'use_gmt_hitset': True,
            'min_read_recency_for_promote': 0,
            'min_write_recency_for_promote': 0,
            'hit_set_grade_decay_rate': 0,
            'hit_set_search_last_n': 0,
            'grade_table': [],
            'stripe_width': 0,
            'expected_num_objects': 0,
            'fast_read': False,
            'options': {},
            # 'target_size_ratio' is a key present in the dict above
            # 'options': {}
            # see comment in get_pool_details() for more details
            'target_size_ratio': 0.3,
            'application_metadata': {
                'rbd': {}
            },
            'application': 'rbd'
            }
        self.fake_user_pool_config = {
            'pool_name': {
                'value': 'foo2'
            },
            'pg_num': {
                'value': '32',
                'cli_set_opt': 'pg_num'
            },
            'pgp_num': {
                'value': '0',
                'cli_set_opt': 'pgp_num'
            },
            'pg_autoscale_mode': {
                'value': 'on',
                'cli_set_opt': 'pg_autoscale_mode'
            },
            'target_size_ratio': {
                'value': '0.3',
                'cli_set_opt': 'target_size_ratio'
            },
            'application': {
                'value': 'rbd'
            },
            'type': {
                'value': 'replicated'
            },
            'erasure_profile': {
                'value': 'default'
            },
            'crush_rule': {
                'value': 'replicated_rule',
                'cli_set_opt': 'crush_rule'
            },
            'expected_num_objects': {
                'value': '0'
            },
            'size': {
                'value': '2',
                'cli_set_opt': 'size'
            },
            'min_size': {
                'value': '0',
                'cli_set_opt': 'min_size'
            },
            'pg_placement_num': {
                'value': '32',
                'cli_set_opt': 'pgp_num'
            }}

    def test_check_pool_exist(self):
        expected_command_list = [
            'podman',
            'run',
            '--rm',
            '--net=host',
            '-v',
            '/etc/ceph:/etc/ceph:z',
            '-v',
            '/var/lib/ceph/:/var/lib/ceph/:z',
            '-v',
            '/var/log/ceph/:/var/log/ceph/:z',
            '--entrypoint=ceph',
            fake_container_image_name,
            '-n',
            fake_user,
            '-k',
            fake_user_key,
            '--cluster',
            'ceph',
            'osd',
            'pool',
            'stats',
            self.fake_user_pool_config['pool_name']['value'],
            '-f',
            'json'
            ]

        cmd = ceph_pool.check_pool_exist(fake_cluster_name,
                                         self.fake_user_pool_config['pool_name']['value'],
                                         fake_user, fake_user_key, output_format='json',
                                         container_image=fake_container_image_name)
        assert cmd == expected_command_list

    def test_get_default_running_config(self):
        params = ['osd_pool_default_size',
                  'osd_pool_default_min_size',
                  'osd_pool_default_pg_num',
                  'osd_pool_default_pgp_num']

        expected_command_list = []
        cmd_list = []

        for param in params:
            expected_command_list.append([
                'podman',
                'run',
                '--rm',
                '--net=host',
                '-v',
                '/etc/ceph:/etc/ceph:z',
                '-v',
                '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v',
                '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=ceph',
                fake_container_image_name,
                '-n',
                'client.admin',
                '-k',
                '/etc/ceph/ceph.client.admin.keyring',
                '--cluster',
                'ceph',
                'config',
                'get',
                'mon.*',
                param
            ])
            cmd_list.append(ceph_pool.generate_get_config_cmd(param,
                                                              fake_cluster_name,
                                                              fake_user, fake_user_key,
                                                              container_image=fake_container_image_name))
        assert cmd_list == expected_command_list

    def test_get_application_pool(self):
        expected_command = [
                'podman',
                'run',
                '--rm',
                '--net=host',
                '-v',
                '/etc/ceph:/etc/ceph:z',
                '-v',
                '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v',
                '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=ceph',
                fake_container_image_name,
                '-n',
                'client.admin',
                '-k',
                '/etc/ceph/ceph.client.admin.keyring',
                '--cluster',
                'ceph',
                'osd',
                'pool',
                'application',
                'get',
                self.fake_user_pool_config['pool_name']['value'],
                '-f',
                'json'
        ]

        cmd = ceph_pool.get_application_pool(fake_cluster_name,
                                             self.fake_user_pool_config['pool_name']['value'],
                                             fake_user, fake_user_key, 'json',
                                             container_image=fake_container_image_name)

        assert cmd == expected_command

    def test_enable_application_pool(self):
        expected_command = [
                'podman',
                'run',
                '--rm',
                '--net=host',
                '-v',
                '/etc/ceph:/etc/ceph:z',
                '-v',
                '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v',
                '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=ceph',
                fake_container_image_name,
                '-n',
                'client.admin',
                '-k',
                '/etc/ceph/ceph.client.admin.keyring',
                '--cluster',
                'ceph',
                'osd',
                'pool',
                'application',
                'enable',
                self.fake_user_pool_config['pool_name']['value'],
                'rbd'
        ]

        cmd = ceph_pool.enable_application_pool(fake_cluster_name,
                                                self.fake_user_pool_config['pool_name']['value'],
                                                'rbd', fake_user, fake_user_key,
                                                container_image=fake_container_image_name)

        assert cmd == expected_command

    def test_disable_application_pool(self):
        expected_command = [
                'podman',
                'run',
                '--rm',
                '--net=host',
                '-v',
                '/etc/ceph:/etc/ceph:z',
                '-v',
                '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v',
                '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=ceph',
                fake_container_image_name,
                '-n',
                'client.admin',
                '-k',
                '/etc/ceph/ceph.client.admin.keyring',
                '--cluster',
                'ceph',
                'osd',
                'pool',
                'application',
                'disable',
                self.fake_user_pool_config['pool_name']['value'],
                'rbd',
                '--yes-i-really-mean-it'
        ]

        cmd = ceph_pool.disable_application_pool(fake_cluster_name,
                                                 self.fake_user_pool_config['pool_name']['value'],
                                                 'rbd', fake_user, fake_user_key,
                                                 container_image=fake_container_image_name)

        assert cmd == expected_command

    def test_compare_pool_config_no_diff(self):
        delta = ceph_pool.compare_pool_config(self.fake_user_pool_config, self.fake_running_pool_details)

        assert delta == {}

    def test_compare_pool_config_std_diff(self):
        self.fake_user_pool_config['size']['value'] = '3'
        delta = ceph_pool.compare_pool_config(self.fake_user_pool_config, self.fake_running_pool_details)

        assert delta == {'size': {'cli_set_opt': 'size', 'value': '3'}}

    def test_compare_pool_config_target_size_ratio_diff(self):
        self.fake_user_pool_config['target_size_ratio']['value'] = '0.5'
        delta = ceph_pool.compare_pool_config(self.fake_user_pool_config, self.fake_running_pool_details)

        assert delta == {'target_size_ratio': {'cli_set_opt': 'target_size_ratio', 'value': '0.5'}}

    def test_compare_pool_config_application_diff(self):
        self.fake_user_pool_config['application']['value'] = 'foo'
        delta = ceph_pool.compare_pool_config(self.fake_user_pool_config, self.fake_running_pool_details)

        assert delta == {'application': {'new_application': 'foo', 'old_application': 'rbd', 'value': 'foo'}}

    def test_list_pools_details(self):
        expected_command = [
                'podman',
                'run',
                '--rm',
                '--net=host',
                '-v',
                '/etc/ceph:/etc/ceph:z',
                '-v',
                '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v',
                '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=ceph',
                fake_container_image_name,
                '-n',
                'client.admin',
                '-k',
                '/etc/ceph/ceph.client.admin.keyring',
                '--cluster',
                'ceph',
                'osd',
                'pool',
                'ls',
                'detail',
                '-f',
                'json'
        ]

        cmd = ceph_pool.list_pools(fake_cluster_name, fake_user, fake_user_key, True, 'json', container_image=fake_container_image_name)

        assert cmd == expected_command

    def test_list_pools_nodetails(self):
        expected_command = [
                'podman',
                'run',
                '--rm',
                '--net=host',
                '-v',
                '/etc/ceph:/etc/ceph:z',
                '-v',
                '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v',
                '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=ceph',
                fake_container_image_name,
                '-n',
                'client.admin',
                '-k',
                '/etc/ceph/ceph.client.admin.keyring',
                '--cluster',
                'ceph',
                'osd',
                'pool',
                'ls',
                '-f',
                'json'
        ]

        cmd = ceph_pool.list_pools(fake_cluster_name, fake_user, fake_user_key, False, 'json', container_image=fake_container_image_name)

        assert cmd == expected_command

    def test_create_replicated_pool_pg_autoscaler_enabled(self):
        self.fake_user_pool_config['type']['value'] = 'replicated'
        expected_command = [
                'podman',
                'run',
                '--rm',
                '--net=host',
                '-v',
                '/etc/ceph:/etc/ceph:z',
                '-v',
                '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v',
                '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=ceph',
                fake_container_image_name,
                '-n',
                'client.admin',
                '-k',
                '/etc/ceph/ceph.client.admin.keyring',
                '--cluster',
                'ceph',
                'osd',
                'pool',
                'create',
                self.fake_user_pool_config['pool_name']['value'],
                self.fake_user_pool_config['type']['value'],
                '--target_size_ratio',
                self.fake_user_pool_config['target_size_ratio']['value'],
                self.fake_user_pool_config['crush_rule']['value'],
                '--expected_num_objects',
                self.fake_user_pool_config['expected_num_objects']['value'],
                '--autoscale-mode',
                self.fake_user_pool_config['pg_autoscale_mode']['value'],
                '--size',
                self.fake_user_pool_config['size']['value']
        ]

        cmd = ceph_pool.create_pool(fake_cluster_name,
                                    self.fake_user_pool_config['pool_name']['value'],
                                    fake_user, fake_user_key, self.fake_user_pool_config,
                                    container_image=fake_container_image_name)

        assert cmd == expected_command

    def test_create_replicated_pool_pg_autoscaler_disabled(self):
        self.fake_user_pool_config['type']['value'] = 'replicated'
        self.fake_user_pool_config['pg_autoscale_mode']['value'] = 'off'
        expected_command = [
                'podman',
                'run',
                '--rm',
                '--net=host',
                '-v',
                '/etc/ceph:/etc/ceph:z',
                '-v',
                '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v',
                '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=ceph',
                fake_container_image_name,
                '-n',
                'client.admin',
                '-k',
                '/etc/ceph/ceph.client.admin.keyring',
                '--cluster',
                'ceph',
                'osd',
                'pool',
                'create',
                self.fake_user_pool_config['pool_name']['value'],
                self.fake_user_pool_config['type']['value'],
                '--pg_num',
                self.fake_user_pool_config['pg_num']['value'],
                '--pgp_num',
                self.fake_user_pool_config['pgp_num']['value'],
                self.fake_user_pool_config['crush_rule']['value'],
                '--expected_num_objects',
                self.fake_user_pool_config['expected_num_objects']['value'],
                '--autoscale-mode',
                self.fake_user_pool_config['pg_autoscale_mode']['value'],
                '--size',
                self.fake_user_pool_config['size']['value']
        ]

        cmd = ceph_pool.create_pool(fake_cluster_name,
                                    self.fake_user_pool_config['pool_name']['value'],
                                    fake_user, fake_user_key,
                                    self.fake_user_pool_config,
                                    container_image=fake_container_image_name)

        assert cmd == expected_command

    def test_create_erasure_pool_pg_autoscaler_enabled(self):
        self.fake_user_pool_config['type']['value'] = 'erasure'
        self.fake_user_pool_config['erasure_profile']['value'] = 'erasure-default'
        self.fake_user_pool_config['crush_rule']['value'] = 'erasure_rule'
        expected_command = [
                'podman',
                'run',
                '--rm',
                '--net=host',
                '-v',
                '/etc/ceph:/etc/ceph:z',
                '-v',
                '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v',
                '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=ceph',
                fake_container_image_name,
                '-n',
                'client.admin',
                '-k',
                '/etc/ceph/ceph.client.admin.keyring',
                '--cluster',
                'ceph',
                'osd',
                'pool',
                'create',
                self.fake_user_pool_config['pool_name']['value'],
                self.fake_user_pool_config['type']['value'],
                '--target_size_ratio',
                self.fake_user_pool_config['target_size_ratio']['value'],
                self.fake_user_pool_config['erasure_profile']['value'],
                self.fake_user_pool_config['crush_rule']['value'],
                '--expected_num_objects',
                self.fake_user_pool_config['expected_num_objects']['value'],
                '--autoscale-mode',
                self.fake_user_pool_config['pg_autoscale_mode']['value']
        ]

        cmd = ceph_pool.create_pool(fake_cluster_name,
                                    self.fake_user_pool_config['pool_name']['value'],
                                    fake_user, fake_user_key, self.fake_user_pool_config,
                                    container_image=fake_container_image_name)

        assert cmd == expected_command

    def test_create_erasure_pool_pg_autoscaler_disabled(self):
        self.fake_user_pool_config['type']['value'] = 'erasure'
        self.fake_user_pool_config['erasure_profile']['value'] = 'erasure-default'
        self.fake_user_pool_config['crush_rule']['value'] = 'erasure_rule'
        self.fake_user_pool_config['pg_autoscale_mode']['value'] = 'off'
        expected_command = [
                'podman',
                'run',
                '--rm',
                '--net=host',
                '-v',
                '/etc/ceph:/etc/ceph:z',
                '-v',
                '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v',
                '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=ceph',
                fake_container_image_name,
                '-n',
                'client.admin',
                '-k',
                '/etc/ceph/ceph.client.admin.keyring',
                '--cluster',
                'ceph',
                'osd',
                'pool',
                'create',
                self.fake_user_pool_config['pool_name']['value'],
                self.fake_user_pool_config['type']['value'],
                '--pg_num',
                self.fake_user_pool_config['pg_num']['value'],
                '--pgp_num',
                self.fake_user_pool_config['pgp_num']['value'],
                self.fake_user_pool_config['erasure_profile']['value'],
                self.fake_user_pool_config['crush_rule']['value'],
                '--expected_num_objects',
                self.fake_user_pool_config['expected_num_objects']['value'],
                '--autoscale-mode',
                self.fake_user_pool_config['pg_autoscale_mode']['value']
        ]

        cmd = ceph_pool.create_pool(fake_cluster_name,
                                    self.fake_user_pool_config['pool_name']['value'],
                                    fake_user, fake_user_key, self.fake_user_pool_config,
                                    container_image=fake_container_image_name)

        assert cmd == expected_command

    def test_remove_pool(self):
        expected_command = [
                'podman',
                'run',
                '--rm',
                '--net=host',
                '-v',
                '/etc/ceph:/etc/ceph:z',
                '-v',
                '/var/lib/ceph/:/var/lib/ceph/:z',
                '-v',
                '/var/log/ceph/:/var/log/ceph/:z',
                '--entrypoint=ceph',
                fake_container_image_name,
                '-n',
                'client.admin',
                '-k',
                '/etc/ceph/ceph.client.admin.keyring',
                '--cluster',
                'ceph',
                'osd',
                'pool',
                'rm',
                self.fake_user_pool_config['pool_name']['value'],
                self.fake_user_pool_config['pool_name']['value'],
                '--yes-i-really-really-mean-it'
        ]

        cmd = ceph_pool.remove_pool(fake_cluster_name, self.fake_user_pool_config['pool_name']['value'],
                                    fake_user, fake_user_key, container_image=fake_container_image_name)

        assert cmd == expected_command
