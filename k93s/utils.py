"""Utility functions and classes."""
import logging
import os.path
import pydoc
import shutil
import sys
import yaml

import k93s


logger = logging.getLogger(__name__)
do_not_remove_after = int(os.environ.setdefault('K_93_NO_REMOVE', '1'))


def subdict_except(d, *keys):
    """Get dict, which contains all keys from argument dict, except given."""
    return {k: v for k, v in d.items() if k not in keys}


def ensure_config_file_location(config_file):
    """Given config_file cmdline argument,
       deduce absolute config file location."""
    if not config_file.startswith('/'):
        if config_file.startswith('~'):
            config_file = os.path.expanduser(config_file)  # pragma: no cover
        else:
            config_file = os.path.join(k93s.curdir, config_file)
    return config_file


def read_config(config_file):
    """Read config from given location into memory."""
    with open(config_file, 'r') as fl:
        return yaml.load(fl, Loader=yaml.FullLoader).get('k93s')


def find_vms_backend(fs_config_contents):
    """Locate VMs backend using pydoc."""
    backend_location = fs_config_contents.get('vms_backend', 'k93s.vms.lightning') + '.backend'
    backend = pydoc.locate(backend_location)
    if backend is None:
        logger.critical('Can\'t find VM backend: %s', backend_location)  # pragma: no cover
        raise RuntimeError('Can not find VM backend.')  # pragma: no cover
    else:
        return backend


def vms_action(action_name, temporary_path, **configuration):
    """Invoke given action on VMs backend within given temporary path.

    :param action_name: An action name to execute. Should be "spinup" or "teardown"
    :type action_name: str

    :param temporary_path: A temporary path to work in context of.
    :type temporary_path: str

    :param configuration: A section 'k93s' of config file.
    :type configuration: dict
    """
    fs_config_contents = configuration['config_contents']
    try:
        os.chdir(temporary_path)
        backend = k93s.utils.find_vms_backend(fs_config_contents)
        vms = backend.compute_vms_configuration(temporary_path, **fs_config_contents)
        logger.warning('Going to invoke action %s on VMs : \n' + '%s\n' * len(vms),
                       action_name, *vms)
        return getattr(backend, action_name)(vms)
    finally:
        if not do_not_remove_after:
            shutil.rmtree(temporary_path)  # pragma: no cover
        os.chdir(k93s.curdir)


class RedirectStdStreams(object):
    # tnx https://stackoverflow.com/a/6796752
    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush()
        self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush()
        self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
