#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import
import json
import click
from prettytable import PrettyTable

from kae.utils import (
    get_current_branch, get_remote_url, get_git_tag,
    get_specs_text, error, info, fatal, handle_console_err
)


@click.argument('jobname', required=False)
@click.argument('git', required=False)
@click.option('-f', help='filename of specs')
@click.option('--literal')
@click.pass_context
def create_job(ctx, jobname, git, f, literal):
    specs_text = get_specs_text(f, literal)
    kae = ctx.obj['kae_api']
    git = git or get_remote_url(remote=ctx.obj['remotename'])
    if not git:
        fatal("git url not found, please check repository or pass argument")
    branch = get_current_branch()
    with handle_console_err():
        kae.create_job(jobname=jobname, git=git, specs_text=specs_text, branch=branch)
    click.echo(info('Create job done.'))


@click.option('--raw', default=False, is_flag=True, help='print the raw json')
@click.pass_context
def list_job(ctx, raw):
    kae = ctx.obj['kae_api']
    with handle_console_err():
        jobs = kae.list_job()

    if raw:
        click.echo(str(jobs))
    else:
        table = PrettyTable(['name', 'status', 'user', 'created'])
        for r in jobs:
            table.add_row([r['name'], r['status'], r['nickname'], r['created']])
        click.echo(table)


@click.argument('jobname', required=True)
@click.pass_context
def delete_job(ctx, jobname):
    kae = ctx.obj['kae_api']
    with handle_console_err():
        result = kae.delete_job(jobname)

    click.echo(str(result))


@click.argument('jobname', required=True)
@click.option('--follow', default=False, is_flag=True, help='follow the log stream')
@click.pass_context
def get_job_log(ctx, jobname, follow):
    kae = ctx.obj['kae_api']
    with handle_console_err():
        if follow is False:
            result = kae.get_job_log(jobname)
            click.echo(result)
        else:
            resp = kae.get_job_log(jobname, follow)
            for m in resp:
                click.echo(m)

    click.echo(info('log end..'))
