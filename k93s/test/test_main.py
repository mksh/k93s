import os
import shutil
from unittest import mock
import unittest
import yaml

from click.testing import CliRunner

# Import test commands
from k93s.__main__ import cli


class TestVMBackend(mock.MagicMock):

    configuration = {}
    common_properties = {}
    vm_properties_master = {}
    vm_properties_agent = {}


backend = TestVMBackend()


class MainModuleTest(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.testtempdir = os.path.join(os.curdir, 'k93s/test/_temp')
        os.makedirs(self.testtempdir)

    def tearDown(self):
        shutil.rmtree(self.testtempdir)

    def test_config_already_exists(self):
        test_config_path = 'k93s/test/test_config/.k93s.main'
        # Test creating configuration.
        res = self.runner.invoke(cli, ['--config-file', test_config_path, 'config'])
        self.assertEqual(
            'A config file at \'{}\' already'
            ' exists.  Do you want to re-create it? [y/N]: \n'.format(
                os.path.abspath(os.path.join(os.curdir, test_config_path))
            ),
            res.stdout,
        )
        self.assertEqual(4, res.exit_code)

    def test_config_already_exists_recreate(self):
        test_config_path = 'k93s/test/_temp/.k93s.main'
        with open(test_config_path, 'w') as fl:
            fl.write('test')
        res = self.runner.invoke(cli, ['--config-file', test_config_path, 'config'], input='y\n')
        self.assertIn('Please input a new cluster name.', res.output)

    def test_config_create_lightning(self):
        test_config_path = 'k93s/test/_temp/.k93s.main'
        # Test creating configuration with all default values.
        self.runner.invoke(cli, ['--config-file', test_config_path, 'config'],
                           input="""testcluster
k93s.vms.lightning
qemu:///system
root
~/.ssh/id_rsa.pub
centos-8
512
10
1
!hellomaster
centos-8
384
10
1
!helloagent""")

        # Read config
        with open(test_config_path, 'r') as fl:
            config_data = yaml.load(fl, Loader=yaml.FullLoader)

        self.assertDictEqual(
            {
                'k93s': {
                    'masters': {
                        'distro': 'centos-8',
                        'memory': 512,
                        'root_disk_size': 10,
                        'root_password': '!hellomaster',
                        'vcpus': 1,
                    },
                    'agents': {
                        'distro': 'centos-8',
                        'memory': 384,
                        'root_disk_size': 10,
                        'root_password': '!helloagent',
                        'vcpus': 1,
                    },
                    'name': 'testcluster',
                    'vms_backend': 'k93s.vms.lightning',
                    'vms_backend_config': {
                        'libvirt_uri': 'qemu:///system',
                        'root_password': 'root',
                        'ssh_key_file': '~/.ssh/id_rsa.pub',
                    },
                },
            },
            config_data,
        )

    def test_spinup_unknown_config(self):
        test_config_path = 'k93s/test/.notexist'
        # Test creating configuration.
        res = self.runner.invoke(cli, ['--config-file', test_config_path, 'spinup'])
        self.assertEqual(res.exit_code, 5)

    def test_spinup(self):
        test_config_path = 'k93s/test/test_config/.k93s.main'
        # Test creating configuration.
        res = self.runner.invoke(cli, ['--config-file', test_config_path, 'spinup'])
        self.assertEqual(res.exit_code, 0)
        self.assertIn('Going to invoke action spinup on VMs', res.output)

    def test_teardown(self):
        test_config_path = 'k93s/test/test_config/.k93s.main'
        # Test creating configuration.
        res = self.runner.invoke(cli, ['--config-file', test_config_path, 'teardown'], input='y\n')
        self.assertEqual(res.exit_code, 0)
        self.assertIn('Going to invoke action teardown on VMs', res.output)

    def test_kubernetes(self):
        test_config_path = 'k93s/test/test_config/.k93s.main'
        # Test creating configuration.
        res = self.runner.invoke(cli, ['--config-file', test_config_path, 'kubernetes'])
        self.assertIn('Done Ansible, removing directory now', res.output)
