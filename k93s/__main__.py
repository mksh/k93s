"""Main k93 CLI module."""
import contextlib
import logging
import tempfile
import os
import yaml

import click

import k93s
import k93s.config
import k93s.provision
import k93s.vms
import k93s.utils


logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _with_config(ctx):
    config_file = k93s.utils.ensure_config_file_location(ctx.obj['config'])
    try:
        config_contents = k93s.utils.read_config(config_file)
    except FileNotFoundError:
        logger.exception('Config %s does not exist.', config_file)
        exit(5)
    else:
        ctx.obj['config_contents'] = config_contents
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield tmpdirname
            pass


@click.group()
@click.option('-f', '--config-file',
              default=os.environ.setdefault('K_93_CONFIG', '.k93s.default.config'),
              help='Config file location.')
@click.pass_context
def cli(ctx, config_file):
    ctx.ensure_object(dict)
    ctx.obj['config'] = config_file


@cli.command()
@click.pass_context
def config(ctx):
    """Create a new configuration file in specified location."""
    config_file = k93s.utils.ensure_config_file_location(ctx.obj['config'])
    _existconfig = os.path.exists(config_file)
    if _existconfig and not click.confirm('A config file at {!r} already exists. '
                                          ' Do you want to re-create it?'.format(config_file)):
        exit(4)
    else:
        if _existconfig:
            os.unlink(config_file)

    with open(config_file, 'w') as fl:
        k93s.config.create_new_config_file()
        yaml.dump({'k93s': k93s.config.k93s}, fl, default_flow_style=False)


@cli.command()
@click.pass_context
def spinup(ctx):
    """Create VMs for Kubernetes cluster without provisioning them."""
    with _with_config(ctx) as tmpdirname:
        k93s.vms.spinup(tmpdirname, **ctx.obj)


@cli.command()
@click.pass_context
def teardown(ctx):
    """Remove the VMs for current cluster."""
    with _with_config(ctx) as tmpdirname:
        if click.confirm('Do you really want to tear down k93s cluster, set up '
                         'with config {!s}'.format(ctx.obj['config'])):
            k93s.vms.teardown(tmpdirname, **ctx.obj)


@cli.command()
@click.pass_context
def kubernetes(ctx):
    """Make sure VMs are set up, and provision cluster with Ansible."""
    with _with_config(ctx) as tmpdirname:
        k93s.vms.spinup(tmpdirname, **ctx.obj)
        # New hosts may have been created, so re-read inventory
        inventory_contents = k93s.vms.inventory(tmpdirname, **ctx.obj)
        k93s.provision.ansible_kubernetes(inventory_contents,
                                          ctx.obj['config_contents'],
                                          tmpdirname)


@cli.command()
@click.pass_context
def kubectl(ctx):
    """Configure kubectl for current user to facilitate cluster."""
    with _with_config(ctx) as tmpdirname:
        inventory_contents = k93s.vms.inventory(tmpdirname, **ctx.obj)
        k93s.provision.configure_kubectl(
            inventory_contents,
            tmpdirname,
            click.confirm('REWRITE ./.kube/config ?'),
        )


def main():
    """Bind CLI application logic."""
    cli()  # pragma: no cover


if __name__ == '__main__':
    main()  # pragma: no cover
