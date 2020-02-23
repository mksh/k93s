"""Sets up Kubernetes with Ansible."""
import contextlib
import logging
import os
import shutil
import subprocess

import k93s


logger = logging.getLogger(__name__)
_ansible_directory_prefix = 'ansible_temp/'


@contextlib.contextmanager
def _ansible_directory(inventory_contents, tmpdirname):
    """Prepare Ansible directory for running."""
    ansible_dir_name = os.path.join(tmpdirname, _ansible_directory_prefix)
    try:
        shutil.copytree(
            os.path.join(k93s.curdir, 'k93s/ansible/'),
            ansible_dir_name,
        )
        with open(os.path.join(ansible_dir_name, 'inventory.ini'), 'w') as fl:
            fl.write(inventory_contents)
        yield ansible_dir_name  # pragma: no cover
    finally:
        logger.warning('Done Ansible, removing directory now')
        shutil.rmtree(ansible_dir_name)


def ansible_kubernetes(inventory_contents, config_contents, tmpdirname):
    """Copy all necessary files into temporary directory.

    Create Ansible inventory.

    Invoke playbook as subprocess.
    """
    with _ansible_directory(inventory_contents, tmpdirname) as ansible_dir_name:
        os.chdir(ansible_dir_name)  # pragma: no cover
        subprocess.check_call(['ansible-playbook', '-i',
                               'inventory.ini', '-vv',
                               '-e', 'k_93_flavor={!s}'.format(
                                   config_contents.get('flavor', 'k3s'),
                               ),
                               config_contents.get('playbook', 'k8s.yml')])  # pragma: no cover


__all__ = ['ansible_kubernetes', ]
