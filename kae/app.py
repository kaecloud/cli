#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import
import pprint
import json
import click
from prettytable import PrettyTable
from kae.utils import (
    get_appname, get_current_branch, get_remote_url, get_git_tag,
    get_specs_text, error, info, fatal, handle_console_err
)


@click.argument('appname', required=False)
@click.option('--raw', default=False, is_flag=True, help='print the raw json')
@click.pass_context
def get_app(ctx, appname, raw):
    kae = ctx.obj['kae_api']
    appname = get_appname(appname=appname)
    with handle_console_err():
        app = kae.get_app(appname)
    if raw:
        click.echo(str(app))
    else:
        table = PrettyTable(['name', 'type', 'git', 'created'])
        table.align['git'] = 'l'
        table.add_row([app['name'], app['type'], app['git'], app['created']])
        click.echo(table)


@click.argument('appname', required=False)
@click.pass_context
def delete_app(ctx, appname):
    kae = ctx.obj['kae_api']
    appname = get_appname(appname=appname)
    with handle_console_err():
        ret = kae.delete_app(appname)

    click.echo(info(json.dumps(ret)))


@click.argument('appname', required=False)
@click.option('--raw', default=False, is_flag=True, help='print the raw json')
@click.pass_context
def get_app_releases(ctx, appname, raw):
    kae = ctx.obj['kae_api']
    appname = get_appname(appname=appname)
    with handle_console_err():
        releases = kae.get_app_releases(appname)

    if raw:
        click.echo(str(releases))
    else:
        table = PrettyTable(['name', 'tag', 'created'])
        for r in releases:
            table.add_row([appname, r['tag'], r['created']])
        click.echo(table)


@click.argument('appname', required=False)
@click.option('--raw', default=False, is_flag=True, help='print the raw json')
@click.pass_context
def get_app_pods(ctx, appname, raw):
    kae = ctx.obj['kae_api']
    appname = get_appname(appname=appname)
    with handle_console_err():
        pods = kae.get_app_pods(appname)

    if raw:
        click.echo(str(pods))
    else:
        table = PrettyTable(['name', 'status', 'ready'])
        for item in pods['items']:
            name = item['metadata']['name']
            status = item['status']['phase']
            ready = sum([1 if c_status['ready'] else 0 for c_status in item['status']['container_statuses']])
            table.add_row([name, status, ready])
        click.echo(table)


@click.argument('appname', required=False)
@click.argument('tag', required=False)
@click.option('--raw', default=False, is_flag=True, help='print the raw json')
@click.pass_context
def get_release(ctx, appname, tag, raw):
    kae = ctx.obj['kae_api']
    appname = get_appname(appname=appname)
    tag = get_git_tag(git_tag=tag)

    with handle_console_err():
        r = kae.get_release(appname, tag)

    if raw:
        click.echo(str(r))
    else:
        table = PrettyTable(['name', 'tag', 'created'])
        table.add_row([appname, r['tag'], r['created']])
        click.echo(table)


@click.argument('appname', required=False)
@click.argument('tag', required=False)
@click.pass_context
def get_release_specs(ctx, appname, tag):
    kae = ctx.obj['kae_api']
    appname = get_appname(appname=appname)
    tag = get_git_tag(git_tag=tag)

    with handle_console_err():
        release = kae.get_release(appname, tag)
    click.echo(info(release['specs_text']))


@click.argument('appname', required=False)
@click.pass_context
def get_secret(ctx, appname):
    kae = ctx.obj['kae_api']
    appname = get_appname(appname=appname)
    with handle_console_err():
        d = kae.get_secret(appname)

    ss = pprint.pformat(d)
    click.echo(info(ss))


@click.argument('appname', required=False)
@click.option('-f', help='filename of secret')
@click.option('--literal')
@click.pass_context
def set_secret(ctx, appname, f, literal):
    data = None
    if literal:
        try:
            data = json.loads(literal)
        except Exception:
            fatal("can't load secret from literal, pls ensure it's a valid json")
    try:
        if f:
            with open(f, "r") as fp:
                data = json.load(fp)
    except Exception:
        fatal("can't read secret data from {}".format(f))
    if data is None:
        fatal("you must specify literal or filename")
    for k, v in data.items():
        if not isinstance(v, str):
            fatal("value of secret must be string")
        if not isinstance(k, str):
            fatal("key of secret must be string")
    kae = ctx.obj['kae_api']
    appname = get_appname(appname=appname)
    with handle_console_err():
        d = kae.set_secret(appname, data)
    click.echo(info(str(d)))


@click.argument('appname', required=False)
@click.pass_context
def get_config(ctx, appname):
    kae = ctx.obj['kae_api']
    appname = get_appname(appname=appname)
    with handle_console_err():
        d = kae.get_config(appname)
    if isinstance(d, dict):
        for k, v in d.items():
            click.echo(info("key:"))
            click.echo(k)
            click.echo(info("data:"))
            click.echo(v)
    else:
        click.echo(d)


@click.argument('appname', required=False)
@click.option('--name', default="config", help='key of the config')
@click.option('-f', help='filename of secret')
@click.option('--literal')
@click.pass_context
def set_config(ctx, appname, name, f, literal):
    kae = ctx.obj['kae_api']
    appname = get_appname(appname=appname)
    if literal:
        data = literal
    elif f:
        try:
            with open(f, "r") as fp:
                data = fp.read()
        except Exception:
            fatal("can't read config data from {}".format(f))
    with handle_console_err():
        d = kae.set_config(appname, name, data)
    ss = pprint.pformat(d)
    click.echo(info(ss))


@click.argument('appname', required=False)
@click.argument('tag', required=False)
@click.argument('git', required=False)
@click.option('-f', help='filename of specs')
@click.option('--literal')
@click.pass_context
def register_release(ctx, appname, tag, git, f, literal):
    appname = get_appname(appname=appname)
    tag = get_git_tag(git_tag=tag)

    specs_text = get_specs_text(f, literal)
    kae = ctx.obj['kae_api']
    git = git or get_remote_url(remote=ctx.obj['remotename'])
    if not git:
        fatal("git url not found, please check repository or pass argument")
    branch = get_current_branch()
    with handle_console_err():
        kae.register_release(appname, tag, git, specs_text, branch=branch)
    click.echo(info('Register %s %s %s done.' % (appname, tag, git)))


@click.argument('appname', required=False)
@click.argument('revision', default=0)
@click.pass_context
def rollback(ctx, appname, revision):
    appname = get_appname(appname=appname)
    kae = ctx.obj['kae_api']
    with handle_console_err():
        kae.rollback(appname, revision)
    click.echo(info('Rollback %s(revision %s) done.' % (appname, revision)))


@click.argument('appname', required=False)
@click.pass_context
def renew(ctx, appname):
    appname = get_appname(appname=appname)
    kae = ctx.obj['kae_api']
    with handle_console_err():
        kae.renew(appname)
    click.echo(info('Renew %s done.' % (appname, )))
