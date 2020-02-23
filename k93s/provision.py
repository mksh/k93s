"""Sets up Kubernetes with Ansible."""
import contextlib
import datetime
import getpass
import logging
import os
import shlex
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
        if os.path.exists(ansible_dir_name):
            shutil.rmtree(ansible_dir_name)
        os.chdir(k93s.curdir)


def ansible_kubernetes(inventory_contents, config_contents, tmpdirname):
    """Copy all necessary files into temporary directory.

    Create Ansible inventory.

    Invoke playbook as subprocess.

    :param inventory_contents: Ansible inventory contents as string.
    :type inventory_contents: str
    :param config_contents: Configuration dictionary.
    :type config_contents: dict
    :param tmpdirname: A temporary operation directory.
    :type tmpdirname: str
    """
    with _ansible_directory(inventory_contents, tmpdirname) as ansible_dir_name:
        os.chdir(ansible_dir_name)  # pragma: no cover
        subprocess.check_call(['ansible-playbook', '-i',
                               'inventory.ini', '-vv',
                               '-e', 'k_93_flavor={!s}'.format(
                                   config_contents.get('flavor', 'k3s'),
                               ),
                               config_contents.get('playbook', 'k8s.yml')])  # pragma: no cover


kubeconfig_file = os.path.expanduser('~/.kube/config')
kubeconfig_new_file = os.path.expanduser('~/.kube/config-new.k93s')
_kubeconfig_backup_tpl = os.path.expanduser('~/.kube/config-old.k93s.{date}')
_copy_node_cmd = 'ansible -i inventory.ini kubernetes_master[0]' + \
                 ' -m fetch -a "src={src} dest={dest} flat=true"'


def configure_kubectl(inventory_contents, tmpdirname, switch_to_new):
    """Set up kubectl on local host to point to remote cluster.

    Usually this means to retrieve ./.kube/config from master.

    :param inventory_contents: Ansible inventory contents as string.
    :type inventory_contents: str
    :param tmpdirname: A temporary operation directory.
    :type tmpdirname: str
    :param switch_to_new: Whether to switch to new kube env with kubectl or not.
    :type switch_to_new: bool
    """
    with _ansible_directory(inventory_contents, tmpdirname) as ansible_dir_name:
        os.chdir(ansible_dir_name)
        src = "/home/{!s}/.kube/config".format(getpass.getuser())
        logger.warning('Copying kubectl from remote %s', src)
        copy_args = shlex.split(_copy_node_cmd.format(
            src=src,
            dest=ansible_dir_name),
        )
        subprocess.check_call(copy_args)
        if switch_to_new:
            kubeconfig_backup_file = _kubeconfig_backup_tpl.format(
                date=datetime.datetime.now().isoformat())
            logger.warning('Old kubectl will be saved as %s.', kubeconfig_backup_file)
            shutil.copyfile(kubeconfig_file, kubeconfig_backup_file)
            shutil.copyfile(os.path.join(ansible_dir_name, 'config'), kubeconfig_file)
            logger.warning('Run kubectl cluster-info to see the cluster status.')


__all__ = ['ansible_kubernetes', 'configure_kubectl']
