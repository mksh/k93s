"""IP Addresses for nodes."""
import ipaddress


_state = {'master': 10, 'agent': 110}


def get_next_ip_address(cidr, host_type):
    """Gets next IP address."""

    assert host_type in ('master', 'agent'), \
        'Only master or agent k8s nodes are supported.'

    net = ipaddress.ip_network(cidr)
    first_host = next(net.hosts())
    current_host = first_host + _state[host_type]
    _state[host_type] += 1
    return str(current_host)


__all__ = ['get_next_ip_address', ]
