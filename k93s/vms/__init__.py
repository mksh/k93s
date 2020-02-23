import functools
import logging

import k93s.utils


logger = logging.getLogger(__name__)
spinup = functools.partial(k93s.utils.vms_action, 'spinup')
teardown = functools.partial(k93s.utils.vms_action, 'teardown')
inventory = functools.partial(k93s.utils.vms_action, 'inventory')


__all__ = ['spinup', 'teardown', 'inventory']
