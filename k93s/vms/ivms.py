"""Internal interfaces of k93s CLI"""
import enum
import typing

import zope.interface


class KubernetesVMType(enum.Enum):
    """Distinguish master and agent nodes."""
    MASTER = 0
    AGENT = 1


class IKubernetesVM(zope.interface.Interface):
    """Represents single Kubernetes VM."""

    vm_type = zope.interface.Attribute('Kubernetes VM Type integer.')

    def up(self):
        """Spins up single VM."""
        raise NotImplementedError()

    def down(self):
        """Removes single VM."""
        raise NotImplementedError()


class IKubernetesVMCollection(zope.interface.Interface):
    """Actionable collection of Kubernetes VMs."""

    configuration = zope.interface.Attribute('Dictionary of actionable VMs configuration.')
    common_properties = zope.interface.Attribute('A dictionary of properties to use for '
                                                 'configuration when asking user,'
                                                 ' mapping to their default values..')
    vm_properties_master = zope.interface.Attribute('A dictionary of properties to use '
                                                    'for single master VM config.')
    vm_properties_agent = zope.interface.Attribute('A dictionary of properties to use '
                                                   'for single agent VM config.')

    def compute_vms_configuration(self, work_directory,
                                  **fs_config_contents) -> typing.List[IKubernetesVM]:
        """Given filesystem configuration contents, computes VM configuration."""
        raise NotImplementedError()

    def spinup(self, vms: typing.List[IKubernetesVM]):
        """Spins up all needed VMs."""
        raise NotImplementedError()

    def teardown(self, vms: typing.List[IKubernetesVM]):
        raise NotImplementedError()

    def inventory(self, vms: typing.List[IKubernetesVM]):
        raise NotImplementedError()
