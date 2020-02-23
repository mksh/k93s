import pydoc

import click


k93s = {}


def _vm_survey(vm_config, vm_config_defaults, vm_type):
    """Survey user about particular VM tier."""
    for (config_property_name, default_config_property) in vm_config_defaults.items():
        user_configured_val = click.prompt('Please enter VM property %s for '
                                           'group %s' % (config_property_name, vm_type),
                                           default=default_config_property)
        vm_config[config_property_name] = user_configured_val


def create_new_config_file():
    """Survey user on command line about new cluster config."""

    name = click.prompt('Please input a new cluster name.', default='testcluster')
    k93s['name'] = name
    vms_backend = click.prompt('Please specify a VM backend to use', default='k93s.vms.lightning')
    k93s['vms_backend'] = vms_backend

    utils = pydoc.locate('k93s.utils')
    backend = getattr(utils, 'find_vms_backend')(k93s)

    vm_common_configs = {}
    k93s['vms_backend_config'] = vm_common_configs
    for (config_property_name, default_value) in backend.common_properties.items():
        user_configured_value = click.prompt(
            'Please specify a VM config value %s' % config_property_name,
            default=default_value,
        )
        vm_common_configs[config_property_name] = user_configured_value

    masters_config = {}
    k93s['masters'] = masters_config

    agents_config = {}
    k93s['agents'] = agents_config

    _vm_survey(masters_config, backend.vm_properties_master, 'MASTER')
    _vm_survey(agents_config, backend.vm_properties_agent, 'AGENT')
