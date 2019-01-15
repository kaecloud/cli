#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import
import click
from tqdm import tqdm
from reprint import output
from prettytable import PrettyTable
from .utils import (
    error, info, get_git_tag, get_remote_url, get_specs_text,
    get_appname, get_current_branch, fatal, handle_console_err,
    merge_list, display_pods,
)

def cfg_list_to_dict(lst):
    _dict = {}
    for line in lst:
        parts = line.split(',')
        if len(parts) == 2:
            _dict['*'] = {
                'request': parts[0],
                'limit': parts[1],
            }
        elif len(parts) == 3:
            try:
                idx = int(parts[0])
                if idx in _dict:
                    fatal("duplicate index")
                _dict[idx] = {
                    'request': parts[1],
                    'limit': parts[2],
                }
            except:
                fatal("invalid index")
    return _dict


@click.argument('appname', required=False)
@click.argument('tag', required=False)
@click.option('--block', default=False, is_flag=True, help='block when exist other build task for this app')
@click.pass_context
def build_app(ctx, appname, tag, block):
    tag = get_git_tag(git_tag=tag)
    appname = get_appname(appname=appname)

    kae = ctx.obj['kae_api']
    gen = kae.build_app(appname, tag, block)
    phase = ""
    try:
        m = next(gen)
        while True:
            if m['success'] is False:
                click.echo(error(m['error']))
                raise click.Abort()
            if phase != m['phase']:
                phase = m['phase']
                click.echo(info("***** PHASE {}".format(m['phase'])))

            # if m['progress']:
            #     name = m['progress']['name']
            #     click.echo(name)
            #     with tqdm(total=m['progress']['max_count']) as pbar:
            #         pbar.update(m['progress']['cur_count'])
            #         for m in gen:
            #             if not m['progress'] or m['progress']['name'] != name:
            #                 break
            #             pbar.update(m['progress']['cur_count'])
            #     continue
            raw_data = m.get('raw_data', None)
            if raw_data is None:
                raw_data = {}
            if raw_data.get('error', None):
                click.echo(error(str(raw_data)))
                raise click.Abort()

            if phase.lower() == "pushing":
                if len(raw_data) == 1 and 'status' in raw_data:
                    click.echo(raw_data['status'])
                elif 'id' in raw_data and 'status' in raw_data:
                    # TODO: make the output like docker push
                    click.echo("{}:{}".format(raw_data['id'], raw_data['status']))
                elif 'digest' in raw_data:
                    click.echo("{}: digest: {} size: {}".format(raw_data.get('status'), raw_data['digest'], raw_data.get('size')))
                else:
                    click.echo(str(m))
            else:
                click.echo(m['msg'])
            m = next(gen)
    except StopIteration:
        pass

    if phase.lower() != "finished":
        click.echo(error("Connection is closed prematurely, build task is still running in background and KAE will send you an email after build task finished."))
        raise click.Abort()
    click.echo(info('\nBuild %s %s done.' % (appname, tag)))


@click.argument('appname', required=False)
@click.argument('tag', required=False)
@click.option('--cpus', multiple=True, help='how many CPUs to set, format `idx,req,limit` or `req,limit`, e.g. --cpu 0,1.5,2')
@click.option('--memories', multiple=True, help='how much memory to set, format `idx,req,limit` or `req,limit` e.g. --memory 0,64M,256M')
@click.option('--replicas', type=int, help='repliocas of app, e.g. --replicas 2')
@click.option('--yaml-name', default='default', help="app yaml name")
@click.option('--cluster', default='default', help='cluster name')
@click.option('--watch', default=False, is_flag=True, help='watch pods')
@click.pass_context
def deploy_app(ctx, appname, cluster, tag, cpus, memories, replicas, yaml_name, watch):
    tag = get_git_tag(git_tag=tag)
    appname = get_appname(appname=appname)

    cpus_dict = cfg_list_to_dict(cpus)
    memories_dict = cfg_list_to_dict(memories)

    kae = ctx.obj['kae_api']
    kae.set_cluster(cluster)

    with handle_console_err():
        kae.deploy_app(appname, tag, cpus_dict, memories_dict,
                       replicas, app_yaml_name=yaml_name)
    if watch:
        watcher = kae.get_app_pods(appname, watch=True)
        display_pods(kae, watcher, appname)
    click.echo(info("deploy done.."))


@click.argument('appname', required=False)
@click.argument('tag', required=False)
@click.option('--cpus', multiple=True, help='how many CPUs to set, format `idx,req,limit` or `req,limit`, e.g. --cpu 0,1.5,2')
@click.option('--memories', multiple=True, help='how much memory to set, format `idx,req,limit` or `req,limit` e.g. --memory 0,64M,256M')
@click.option('--replicas', type=int, help='repliocas of app, e.g. --replicas 2')
@click.option('--yaml-name', default='default', help="app yaml name")
@click.option('--cluster', default='default', help='cluster name')
@click.option('--watch', default=False, is_flag=True, help='watch pods')
@click.pass_context
def deploy_app_canary(ctx, appname, cluster, tag, cpus, memories, replicas, yaml_name, watch):
    tag = get_git_tag(git_tag=tag)
    appname = get_appname(appname=appname)

    cpus_dict = cfg_list_to_dict(cpus)
    memories_dict = cfg_list_to_dict(memories)

    kae = ctx.obj['kae_api']
    kae.set_cluster(cluster)

    with handle_console_err():
        kae.deploy_app_canary(appname, tag, cpus_dict, memories_dict,
                              replicas, app_yaml_name=yaml_name)
    if watch:
        watcher = kae.get_app_pods(appname, canary=True, watch=True)
        display_pods(kae, watcher, appname, canary=True)
    click.echo(info("deploy done.."))


@click.argument('appname', required=False)
@click.option('--cpus', multiple=True, help='how many CPUs to set, format `idx,req,limit` or `req,limit`, e.g. --cpu 0,1.5,2')
@click.option('--memories', multiple=True, help='how much memory to set, format `idx,req,limit` or `req,limit` e.g. --memory 0,64M,256M')
@click.option('--replicas', default=0, type=int, help='repliocas of app, e.g. --replicas 2')
@click.option('--cluster', default='default', help='cluster name')
@click.option('--watch', default=False, is_flag=True, help='watch pods')
@click.pass_context
def scale_app(ctx, appname, cpus, memories, replicas, cluster, watch):
    appname = get_appname(appname=appname)

    if not (cpus or memories or replicas):
        fatal("you must at least sapecify one of cpu memory and replicas")
    cpus_dict = cfg_list_to_dict(cpus)
    memories_dict = cfg_list_to_dict(memories)

    kae = ctx.obj['kae_api']

    kae.set_cluster(cluster)
    with handle_console_err():
        kae.scale_app(appname, cpus_dict, memories_dict, replicas)

    if watch:
        watcher = kae.get_app_pods(appname, watch=True)
        display_pods(kae, watcher, appname)
    click.echo(info("scale done.."))
