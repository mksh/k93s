import getpass
import os
import shutil
import subprocess
import unittest
from unittest import mock

import k93s
import k93s.provision


class ProvisionTest(unittest.TestCase):

    def setUp(self):
        self.testtempdir = os.path.join(os.curdir, 'k93s/test/_temp')
        os.makedirs(self.testtempdir)

        self.subprocess_patch = mock.patch.object(subprocess, 'check_call')
        self.subprocess_mock = self.subprocess_patch.start()
        self.kubeconfig_patch = mock.patch(
            'k93s.provision.kubeconfig_file',
            os.path.join(self.testtempdir, 'config'),
        )
        self.kubeconfig_mock = self.kubeconfig_patch.start()

        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        shutil.rmtree(self.testtempdir)
        os.chdir(k93s.curdir)

    def test_configure_kubectl_noswitch(self):
        k93s.provision.configure_kubectl('', self.testtempdir, switch_to_new=False)
        self.subprocess_mock.assert_called_once_with(
                [
                    'ansible', '-i', 'inventory.ini', 'kubernetes_master[0]', '-m',
                    'fetch', '-a',
                    'src=/home/{}/.kube/config dest=./k93s/test/_temp/ansible_temp/ '
                    'flat=true'.format(
                        getpass.getuser())]
        )

    def test_configure_kubectl_switch(self):
        # Pre-fill 'kubeconfig' value

        def side_effect_ansible(*args):
            self.shutil_patch = mock.patch.object(shutil, 'copyfile')
            self.shutil_mock = self.shutil_patch.start()

        self.subprocess_mock.side_effect = side_effect_ansible
        k93s.provision.configure_kubectl('', self.testtempdir, switch_to_new=True)
        self.subprocess_mock.assert_called_once_with(
                [
                    'ansible', '-i', 'inventory.ini', 'kubernetes_master[0]', '-m',
                    'fetch', '-a',
                    'src=/home/{}/.kube/config dest=./k93s/test/_temp/ansible_temp/ '
                    'flat=true'.format(
                        getpass.getuser())]
        )
        self.assertEqual(self.shutil_mock.call_count, 2)
        self.shutil_mock.assert_called_with(
            './k93s/test/_temp/ansible_temp/config',
            './k93s/test/_temp/config',
        )
