import asyncio
import io
import logging
import os
import yaml

import nest_asyncio
from virt_lightning import configuration as virt_config, shell
from zope.interface import implementer

from k93s import utils
from k93s.network import get_next_ip_address
from k93s.vms import ivms


logger = logging.getLogger(__name__)


@implementer(ivms.IKubernetesVM)
class LightningVM:
    """Represents single Lightning VM."""

    @property
    def vm_type(self):
        return self._vm_type

    def __init__(self, name, is_master, lvl_config, **configuration):
        if is_master:
            self._vm_type = ivms.KubernetesVMType.MASTER
        else:
            self._vm_type = ivms.KubernetesVMType.AGENT
        self.name = name
        self.config = configuration
        self.config['name'] = name
        self.lvl_config = lvl_config

    def __str__(self):
        return '<LightningVM: {}>'.format(self.name)

    def up(self):
        """No-action for now."""
        try:
            shell.up([self.config], self.lvl_config, 'k93s')
        except:  # pragma: no cover  # noqa: E731
            logger.exception('Failed to bring up cluster')  # pragma: no cover

    def down(self):
        """No-action for now."""
        try:
            shell.down(self.lvl_config, 'k93s')
        except:  # pragma: no cover  # noqa: E731
            logger.exception('Failed to tear down cluster')  # pragma: no cover


@implementer(ivms.IKubernetesVMCollection)
class LightningVMNodes:
    """Represent a collection of Kubernetes masters and agents,
    managed with virt_lightning."""

    # We do not support changing these yet.
    blacklisted_config_keys = {'network_cidr', 'network_name', 'storage_pool'}
    common_properties = utils.subdict_except(virt_config.DEFAULT_CONFIGURATION['main'].copy(),
                                             *blacklisted_config_keys)

    _NETWORK = '192.168.123.0/24'
    _NETWORK_NAME = 'virt-lightning'
    _MASTER_NODES_COUNT = 1
    _AGENT_NODES_COUNT = 1

    _MASTER_DISTRO = 'centos-8'
    _MASTER_MEMORY = 512
    _MASTER_VCPUS = 1
    _MASTER_ROOT_DISK_SIZE = 10
    _MASTER_ROOT_PASSWORD = '!!testtesttest'

    _AGENT_DISTRO = 'centos-8'
    _AGENT_MEMORY = 384
    _AGENT_VCPUS = 1
    _AGENT_ROOT_DISK_SIZE = 10
    _AGENT_ROOT_PASSWORD = '!!testtesttest'

    vm_properties_master = {
        'distro': _MASTER_DISTRO,
        'memory': _MASTER_MEMORY,
        'root_disk_size': _MASTER_ROOT_DISK_SIZE,
        'vcpus': _MASTER_VCPUS,
        'root_password': _MASTER_ROOT_PASSWORD,
    }

    vm_properties_agent = {
        'distro': _AGENT_DISTRO,
        'memory': _AGENT_MEMORY,
        'root_disk_size': _AGENT_ROOT_DISK_SIZE,
        'vcpus': _AGENT_VCPUS,
        'root_password': _AGENT_ROOT_PASSWORD,
    }

    def __init__(self):
        self._vms = {}
        self._distros = set()
        self._lightning_file_name = None
        self._network_name = None
        self._lvl_configuration = shell.Configuration()

    @property
    def lightning_config(self):
        return self._lvl_configuration

    @property
    def vms(self):
        return self._vms

    @property
    def distros(self):
        return self._distros

    def _prefetch_distros(self):
        """Prefetch images from https://virt-lightning.org/images/,
           if they are not available yet."""
        iobuf = io.StringIO()
        with utils.RedirectStdStreams(stdout=iobuf):
            shell.distro_list(self._lvl_configuration)
            iobuf.flush()
        iobuf.seek(0)
        distro_list = {d['distro'] for d in
                       yaml.load(iobuf.read(), Loader=yaml.FullLoader) or set()}
        to_fetch = self._distros - distro_list
        for dis in to_fetch:
            logger.warning('Going to fetch distro %s', dis)
            shell.fetch(self._lvl_configuration, distro=dis)

    def _render_config(self):
        """Renders libvirt-lightning configuration."""
        with open(self._lightning_file_name, 'w') as fl:
            yaml.dump([v for v in self._vms.values()], fl, default_flow_style=False)

    def _invoke_lightning(self, vms, action):
        """Invoke particular lightning action."""

        if action == 'up':
            # Fetch non-available distros
            self._prefetch_distros()

        def perform_vm_action(_vm, _action_name, _fut):
            logger.warning('Invoking action %s on VM %s', _action_name, _vm)
            try:
                getattr(_vm, _action_name)()
            finally:
                logger.warning('Done action %s on VM %s', _action_name, _vm)
                _fut.set_result(True)

        @asyncio.coroutine
        def perform_all_vm_actions(loop):
            futs = []
            for vm in vms:
                fut = asyncio.Future(loop=loop)
                loop.call_soon(perform_vm_action, vm, action, fut)
                futs.append(fut)

            yield from asyncio.sleep(1, loop=loop)
            yield from asyncio.gather(*futs, loop=loop, return_exceptions=True)
            logger.warning('Done with VM actions!')

        loop = asyncio.get_event_loop()

        nest_asyncio.apply(loop)

        loop.run_until_complete(perform_all_vm_actions(loop))

    def _create_master_vm_config(self, name, **master_properties):
        cfg = {}
        cfg['name'] = name
        cfg['distro'] = master_properties.get('distro', self._MASTER_DISTRO)
        cfg['vcpus'] = int(master_properties.get('vcpus', self._MASTER_VCPUS))
        cfg['memory'] = int(master_properties.get('memory', self._MASTER_MEMORY))
        cfg['root_disk_size'] = int(master_properties.get('root_disk_size',
                                                          self._MASTER_ROOT_DISK_SIZE))
        cfg['root_password'] = master_properties.get('root_password', self._MASTER_ROOT_PASSWORD)
        cfg['groups'] = ['kubernetes_master']
        cfg['networks'] = [
            {
                'network': self._network_name,
                'ipv4': get_next_ip_address(self._NETWORK, 'master')
            },
        ]
        lvl_config = shell.Configuration()
        lvl_config.data['main'].update({k: str(v) for k, v in cfg.items()})
        return cfg, lvl_config

    def _create_agent_vm_config(self, name, **agent_properties):
        cfg = {}
        cfg['name'] = name
        cfg['distro'] = agent_properties.get('distro', self._AGENT_DISTRO)
        cfg['vcpus'] = int(agent_properties.get('vcpus', self._AGENT_VCPUS))
        cfg['memory'] = int(agent_properties.get('memory', self._AGENT_MEMORY))
        cfg['root_disk_size'] = int(agent_properties.get('root_disk_size',
                                                         self._AGENT_ROOT_DISK_SIZE))
        cfg['password'] = agent_properties.get('root_password', self._AGENT_ROOT_DISK_SIZE)
        cfg['groups'] = ['kubernetes_agent']
        cfg['networks'] = [
            {
                'network': self._network_name,
                'ipv4': get_next_ip_address(self._NETWORK, 'agent')
            },
        ]
        lvl_config = shell.Configuration()
        lvl_config.data['main'].update({k: str(v) for k, v in cfg.items()})
        return cfg, lvl_config

    def compute_vms_configuration(self, work_directory, **fs_config_contents):
        """Generate YAML lightning config in temporary directory.

        This function is stateless, and does not yet create any files.
        """

        self._lightning_file_name = os.path.join(work_directory, 'virt-lightning.yaml')

        for config_key in self.blacklisted_config_keys:
            if config_key in fs_config_contents['vms_backend_config']:
                raise RuntimeError('Config key {!s} is not yet supported '
                                   'by virt-lightning '
                                   ' backend.'.format(config_key))  # pragma: no cover

        self._network_name = self._NETWORK_NAME

        master_nodes_config = {}
        master_nodes_config.update(fs_config_contents.get('masters', {}))
        master_nodes_config.update(fs_config_contents['vms_backend_config'])
        agent_nodes_config = {}
        agent_nodes_config.update(fs_config_contents.get('agents', {}))
        agent_nodes_config.update(fs_config_contents['vms_backend_config'])

        self._lvl_configuration.data['main'].update(
            fs_config_contents.get('vms_backend_config', {}))

        cluster_name = fs_config_contents.get('name', 'K_93_TEST')
        vms = []

        for i in range(0, int(master_nodes_config.get('count', self._MASTER_NODES_COUNT))):
            name = '{}-master-{}'.format(cluster_name, i + 1)
            self._vms[name], lvl_config = self._create_master_vm_config(name, **master_nodes_config)
            self._distros.add(self._vms[name]['distro'])
            vms.append(LightningVM(is_master=True, lvl_config=lvl_config, **self._vms[name]))

        for i in range(0, int(agent_nodes_config.get('count', self._AGENT_NODES_COUNT))):
            name = '{}-agent-{}'.format(cluster_name, i + 1)
            self._vms[name], lvl_config = self._create_agent_vm_config(name, **agent_nodes_config)
            self._distros.add(self._vms[name]['distro'])
            vms.append(LightningVM(is_master=False, lvl_config=lvl_config, **self._vms[name]))

        return vms

    def spinup(self, vms):
        self._render_config()
        self._invoke_lightning(vms, 'up')

    def teardown(self, vms):
        self._render_config()
        self._invoke_lightning(vms, 'down')

    def inventory(self, vms):
        self._render_config()
        iobuf = io.StringIO()
        with utils.RedirectStdStreams(stdout=iobuf):
            shell.ansible_inventory(self._lvl_configuration, 'k93s')
            iobuf.flush()
        iobuf.seek(0)
        r = iobuf.read()
        return r


backend = LightningVMNodes()


__all__ = ['backend', ]
