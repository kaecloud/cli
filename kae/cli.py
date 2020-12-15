#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import
import sys
import logging
from os import getenv
from os.path import expanduser

import click

from kaelib import KaeAPI

from kae import __VERSION__
from kae.commands import commands
from kae.utils import read_yaml_file, write_yaml_file, error, get_sso_token

__local_commands = ("version", "test", "create-web-app", "build")


@click.group(invoke_without_command=True)
@click.option('--config-path', default=expanduser('~/.kae/config.yaml'),
              help='config file, yaml', envvar='KAE_CONFIG_PATH')
@click.option('--remotename', default='origin', help='git remote name, default to origin', envvar='KAE_REPO_NAME')
@click.option('--debug', default=False, help='enable debug output', is_flag=True)
@click.option('--totp', default=None, help='time-based one time password')
@click.option('-v', '--version', default=False, help='show version', is_flag=True)
@click.pass_context
def kae_commands(ctx, config_path, remotename, debug, totp, version):
    if ctx.invoked_subcommand is None:
        if version:
            print("KAE version: {}".format(__VERSION__))
            return
        else:
            click.echo(error("only -v is valid when called without command"))
            sys.exit(-1)

    ctx.obj['debug'] = debug

    if ctx.invoked_subcommand not in __local_commands:
        config = read_yaml_file(config_path)
        if not config:
            config = {}
            config['sso_username'] = getenv('SSO_USERNAME')
            config['sso_password'] = getenv('SSO_PASSWORD')
            config['sso_host'] = getenv('SSO_HOST')
            config['sso_realm'] = getenv("SSO_REALM", "kae")
            config['sso_client_id'] = getenv("SSO_CLIENT_ID", "kae-cli")

            config['kae_url'] = getenv('KAE_URL', 'https://console.gtapp.xyz')
            write_yaml_file(config, config_path)
            click.echo('config saved to {}'.format(config_path))

        if debug:
            logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] [%(process)d] [%(levelname)s] [%(filename)s @ %(lineno)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S %z')

        token = get_sso_token(
            user=config['sso_username'],
            password=config['sso_password'],
            sso_host=config['sso_host'],
            realm=config.get('sso_realm', "kae"),
            client_id=config.get('sso_client_id', "kae-cli"),
            totp=totp
        )
        kae_api = KaeAPI(config['kae_url'].strip('/'), access_token=token)
        ctx.obj['kae_api'] = kae_api
        ctx.obj['remotename'] = remotename


for command, function in commands.items():
    kae_commands.command(command)(function)


@kae_commands.command()
def version():
    print("KAE version: {}, python: {}".format(__VERSION__, sys.version))


def main():
    kae_commands(obj={})
