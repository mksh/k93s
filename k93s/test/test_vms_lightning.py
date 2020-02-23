import os
import shutil
import unittest
from unittest import mock

import k93s.vms.ivms
import k93s.vms.lightning
from k93s.network import _state as network_state
from virt_lightning import configuration, shell


class CommandSideEffect:

    def __init__(self, stdout):
        self.stdout = stdout

    def __call__(self, *args, **kwargs):
        print(self.stdout, flush=True)


class LightningVMTest(unittest.TestCase):

    def setUp(self):
        self.lvl_config = mock.Mock(configuration.Configuration)
        self.vm = k93s.vms.lightning.LightningVM(
            'hello', True, self.lvl_config, **{'hello': 'lightning'})

    def test_lightning_vm_type(self):
        self.vm_agent = k93s.vms.lightning.LightningVM(
            'hello', False, self.lvl_config, **{'hello': 'lightning'})
        self.assertEqual(k93s.vms.ivms.KubernetesVMType.MASTER, self.vm.vm_type)
        self.assertEqual(k93s.vms.ivms.KubernetesVMType.AGENT, self.vm_agent.vm_type)

    @mock.patch.object(shell, 'up')
    def test_lightning_vm_up(self, up_patched):
        self.vm.up()
        up_patched.assert_called_once_with(
            [{'hello': 'lightning', 'name': 'hello'}],
            self.lvl_config,
            'k93s',
        )

    @mock.patch.object(shell, 'down')
    def test_lightning_vm_down(self, down_patched):
        self.vm.down()
        down_patched.assert_called_once_with(
            self.lvl_config,
            'k93s',
        )

    def test_vm_str(self):
        self.assertEqual('<LightningVM: hello>', str(self.vm))


class LightningVMNodesTest(unittest.TestCase):

    def setUp(self):
        self.lvl_config = mock.Mock(configuration.Configuration)
        self.fs_config_contents = {
            'masters': {
                'distro': 'centos-8',
                'memory': 512,
                'root_disk_size': 10,
                'root_password': '!hellomaster',
                'vcpus': 0.5,
                'count': 3,
            },
            'agents': {
                'distro': 'centos-8',
                'memory': 512,
                'root_disk_size': 10,
                'root_password': '!helloagent',
                'vcpus': 0.5,
                'count': 3,
            },
            'name': 'testcluster',
            'vms_backend': 'k93s.vms.lightning',
            'vms_backend_config': {
                'libvirt_uri': 'qemu:///system',
                'root_password': 'root',
                'ssh_key_file': '~/.ssh/id_rsa.pub',
            },
        }
        self.vms = k93s.vms.lightning.LightningVMNodes()
        self.testtempdir = os.path.join(os.curdir, 'k93s/test/_temp')
        os.makedirs(self.testtempdir)
        self.initial_netstate = network_state.copy()

    def tearDown(self):
        shutil.rmtree(self.testtempdir)
        network_state.update(self.initial_netstate)

    def test_lightning_compute_vms_configuration(self):
        vms = self.vms.compute_vms_configuration('test', **self.fs_config_contents)

        self.assertEqual(len(vms), 6)

        for vm in vms[0:3]:
            self.assertEqual(vm.vm_type, k93s.vms.ivms.KubernetesVMType.MASTER)

        for vm in vms[3:6]:
            self.assertEqual(vm.vm_type, k93s.vms.ivms.KubernetesVMType.AGENT)

        self.assertDictEqual(
            {
                "testcluster-agent-1": {
                    "distro": "centos-8",
                    "groups": [
                        "kubernetes_agent"
                    ],
                    "memory": 512,
                    "name": "testcluster-agent-1",
                    "networks": [
                        {
                            "ipv4": "192.168.123.111",
                            "network": "virt-lightning"
                        }
                    ],
                    "password": "root",
                    "root_disk_size": 10,
                    "vcpus": 0
                },
                "testcluster-agent-2": {
                    "distro": "centos-8",
                    "groups": [
                        "kubernetes_agent"
                    ],
                    "memory": 512,
                    "name": "testcluster-agent-2",
                    "networks": [
                        {
                            "ipv4": "192.168.123.112",
                            "network": "virt-lightning"
                        }
                    ],
                    "password": "root",
                    "root_disk_size": 10,
                    "vcpus": 0
                },
                "testcluster-agent-3": {
                    "distro": "centos-8",
                    "groups": [
                        "kubernetes_agent"
                    ],
                    "memory": 512,
                    "name": "testcluster-agent-3",
                    "networks": [
                        {
                            "ipv4": "192.168.123.113",
                            "network": "virt-lightning"
                        }
                    ],
                    "password": "root",
                    "root_disk_size": 10,
                    "vcpus": 0
                },
                "testcluster-master-1": {
                    "distro": "centos-8",
                    "groups": [
                        "kubernetes_master"
                    ],
                    "memory": 512,
                    "name": "testcluster-master-1",
                    "networks": [
                        {
                            "ipv4": "192.168.123.11",
                            "network": "virt-lightning"
                        }
                    ],
                    "root_disk_size": 10,
                    "root_password": "root",
                    "vcpus": 0
                },
                "testcluster-master-2": {
                    "distro": "centos-8",
                    "groups": [
                        "kubernetes_master"
                    ],
                    "memory": 512,
                    "name": "testcluster-master-2",
                    "networks": [
                        {
                            "ipv4": "192.168.123.12",
                            "network": "virt-lightning"
                        }
                    ],
                    "root_disk_size": 10,
                    "root_password": "root",
                    "vcpus": 0
                },
                "testcluster-master-3": {
                    "distro": "centos-8",
                    "groups": [
                        "kubernetes_master"
                    ],
                    "memory": 512,
                    "name": "testcluster-master-3",
                    "networks": [
                        {
                            "ipv4": "192.168.123.13",
                            "network": "virt-lightning"
                        }
                    ],
                    "root_disk_size": 10,
                    "root_password": "root",
                    "vcpus": 0
                }
            },
            self.vms.vms,
        )

        self.assertSetEqual({'centos-8'}, self.vms.distros)

    def test_lightning_down(self):
        vms = self.vms.compute_vms_configuration('k93s/test/_temp', **self.fs_config_contents)
        with mock.patch('k93s.vms.lightning.LightningVM.down') as down_patched:
            self.vms.teardown(vms)
            self.assertEqual(6, down_patched.call_count)

    @mock.patch.object(shell, 'distro_list', side_effect=CommandSideEffect('- distro: centos-8'))
    def test_lightning_up_nofetch(self, distro_list_patched):
        vms = self.vms.compute_vms_configuration('k93s/test/_temp', **self.fs_config_contents)
        with mock.patch('k93s.vms.lightning.LightningVM.up') as up_patched:
            self.vms.spinup(vms)
            self.assertEqual(6, up_patched.call_count)

    @mock.patch.object(shell, 'fetch')
    @mock.patch.object(shell, 'distro_list', side_effect=CommandSideEffect('[]'))
    def test_lightning_up_fetch(self, distro_list_patched, fetch_patched):
        vms = self.vms.compute_vms_configuration('k93s/test/_temp', **self.fs_config_contents)
        with mock.patch('k93s.vms.lightning.LightningVM.up'):
            self.vms.spinup(vms)
            fetch_patched.assert_called_once_with(self.vms.lightning_config, distro='centos-8')

    @mock.patch.object(shell, 'ansible_inventory', side_effect=CommandSideEffect('hello inventory'))
    def test_inventory(self, ansible_inventory_patched):
        vms = self.vms.compute_vms_configuration('k93s/test/_temp', **self.fs_config_contents)
        inventory = self.vms.inventory(vms)
        self.assertEqual(inventory, 'hello inventory\n')
