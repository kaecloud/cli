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
    merge_list,
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
@click.pass_context
def build(ctx, appname, tag):
    tag = get_git_tag(git_tag=tag)
    appname = get_appname(appname=appname)

    kae = ctx.obj['kae_api']
    gen = kae.build(appname, tag)
    try:
        m = next(gen)
        phase = None
        while True:
            if m['success'] is False:
                click.echo(error(m['error']))
                ctx.exit(-1)
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
            if phase.lower() == "pushing":
                raw_data = m['raw_data']
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

    click.echo(info('\nBuild %s %s done.' % (appname, tag)))


@click.argument('appname', required=False)
@click.argument('tag', required=False)
@click.option('--cpus', multiple=True, help='how many CPUs to set, format `idx,req,limit` or `req,limit`, e.g. --cpu 0,1.5,2')
@click.option('--memories', multiple=True, help='how much memory to set, format `idx,req,limit` or `req,limit` e.g. --memory 0,64M,256M')
@click.option('--replicas', default=1, type=int, help='repliocas of app, e.g. --replicas 2')
@click.option('-f', help='filename of specs')
@click.option('--literal')
@click.pass_context
def deploy(ctx, appname, tag, cpus, memories, replicas, f, literal):
    specs_text = get_specs_text(f, literal)
    tag = get_git_tag(git_tag=tag)
    appname = get_appname(appname=appname)

    cpus_dict = cfg_list_to_dict(cpus)
    memories_dict = cfg_list_to_dict(memories)

    kae = ctx.obj['kae_api']
    for m in kae.deploy(appname, tag, cpus_dict, memories_dict, replicas, specs_text=specs_text):
        if m['success'] is True:
            click.echo(info(m['msg']))
        else:
            click.echo(error(m['error']))


@click.argument('appname', required=False)
@click.option('--cpus', multiple=True, help='how many CPUs to set, format `idx,req,limit` or `req,limit`, e.g. --cpu 0,1.5,2')
@click.option('--memories', multiple=True, help='how much memory to set, format `idx,req,limit` or `req,limit` e.g. --memory 0,64M,256M')
@click.option('--replicas', default=0, type=int, help='repliocas of app, e.g. --replicas 2')
@click.pass_context
def scale(ctx, appname, cpus, memories, replicas):
    appname = get_appname(appname=appname)

    if not (cpus or memories or replicas):
        fatal("you must at least sapecify one of cpu memory and replicas")
    cpus_dict = cfg_list_to_dict(cpus)
    memories_dict = cfg_list_to_dict(memories)

    kae = ctx.obj['kae_api']
    with output(output_type="list", initial_len=10, interval=0) as output_list:
        for m in kae.scale(appname, cpus_dict, memories_dict, replicas):
            if m['error']:
                fatal(m['error'])
            else:
                table = PrettyTable(['name', 'status', 'ready'])
                for p in m['pods']:
                    table.add_row([p['name'], p['status'], p['ready']])
                merge_list(output_list, str(table).split('\n'))
    click.echo(info("scale done.."))
