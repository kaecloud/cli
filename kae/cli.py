#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import
import logging
from os import getenv
from os.path import expanduser

import click

from kae.commands import commands
from kae.console import ConsoleAPI
from kae.utils import read_yaml_file, write_yaml_file


@click.group()
@click.option('--config-path', default=expanduser('~/.kae/config.yaml'),
              help='config file, yaml', envvar='KAE_CONFIG_PATH')
@click.option('--remotename', default='origin', help='git remote name, default to origin', envvar='KAE_REPO_NAME')
@click.option('--debug', default=False, help='enable debug output', is_flag=True)
@click.pass_context
def kae_commands(ctx, config_path, remotename, debug):
    config = read_yaml_file(config_path)
    if not config:
        config = {}
        config['auth_token'] = getenv('KAE_AUTH_TOKEN')
        config['kae_url'] = getenv('KAE_URL', 'https://console.gtapp.xyz')
        write_yaml_file(config, config_path)
        click.echo('config saved to {}'.format(config_path))

    if debug:
        logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] [%(process)d] [%(levelname)s] [%(filename)s @ %(lineno)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S %z')

    if not config['auth_token']:
        raise Exception('KAE_AUTH_TOKEN not found')
    kae_api = ConsoleAPI(config['kae_url'].strip('/'), auth_token=config['auth_token'])
    ctx.obj['kae_api'] = kae_api
    ctx.obj['remotename'] = remotename
    ctx.obj['debug'] = debug


for command, function in commands.items():
    kae_commands.command(command)(function)


def main():
    kae_commands(obj={})
