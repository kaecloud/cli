#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import

import yaml
import click
from prettytable import PrettyTable
from pprint import pprint
import os

from kae.utils import (
    abort_if_false, fatal, info, handle_console_err, error
)


@click.argument('mainfile', required=True)
@click.argument('arguments', nargs=-1, required=False)
@click.option('--appname', required=True, help='appname')
@click.option('--apptype', required=False, default='sparkapplication', help="Valid value are 'sparkapplication' or 'scheduledsparkapplication ")
@click.option('--schedule', required=False, help='schedule')
@click.option('--concurrency-policy', default='Allow', help='The concurrency policy, Valid values are `Allow` `Forbid` `Replace`')
@click.option('--image', required=True, help='image')
@click.option('--pythonversion', required=False, default='2', help='Specpython version')
@click.option('--conf', required=False, multiple=True, help='configure')
@click.option('--sparkversion', required=False, default='2.4.0', help='spark verion')
@click.option('--mode', required=False, default='client', help='mode')
@click.option('--jars', required=False, help='jars')
@click.option('--files', required=False, help='files')
@click.option('--py-files', required=False, help='pyfiles')
@click.option('--packages', required=False, help='packages')
@click.option('--repositories', required=False, help='repositories')
@click.option('--driver-memory', required=False, default='512m')
@click.option('--driver-cores', type=int, required=False, default=1)
@click.option('--executor-memory', required=False, default='512m')
@click.option('--executor-cores', type=int, required=False, default=1)
@click.option('--number-executors', type=int, required=False, default=1)
@click.option('--selector', required=False, multiple=True, help='Selector')
@click.option('--comment', required=False, help='comment')
@click.pass_context
def create_sparkapp(ctx, mainfile, arguments, appname, apptype, schedule, concurrency_policy,
                    image, pythonversion, conf, sparkversion, mode,
                    jars, files, py_files, packages, repositories, driver_memory, driver_cores,
                    executor_memory, executor_cores, number_executors, selector, comment):
    kae = ctx.obj['kae_api']
    sparkConf = {}
    nodeSelector = {}

    for item in conf:
        k, v = item.split('=')
        sparkConf[k] = v

    for item in selector:
        k, v = item.split('=')
        nodeSelector[k] = v

    data = {
        'appname': appname,
        'apptype': apptype,
        'image': image,
        'pythonVersion': pythonversion,
        'driver': {
            'cpu': driver_cores,
            'memory': driver_memory,
        },
        'executor': {
            'cpu': executor_cores,
            'memory': executor_memory,
            'instances': number_executors
        },
        'deps': {},
    }

    if apptype == 'scheduledsparkapplication':
        if not schedule:
            fatal('Scheduledsparkapplication must should spec `shedule`')
        else:
            data['schedule'] = schedule
        
        data['concurrencyPolicy'] = concurrency_policy

    if sparkConf:
        data['sparkConf'] = sparkConf

    if nodeSelector:
        data['nodeSelector'] = nodeSelector

    if arguments:
        data['arguments'] = list(arguments)

    jars_name_list = []
    files_name_list = []
    pyfiles_name_list = []
    mainfile_obj = []
    jars_obj = []
    files_obj = []
    pyfiles_obj = []

    if not os.path.exists(mainfile):
        fatal('Main file {} not exist'.format(mainfile))
    else:
        mainfile_obj.append(('file', open(mainfile, 'rb')))

    if jars:
        for jar in jars.split(','):
            if not os.path.exists(jar):
                fatal('Jar {} not exist'.format(jar))
            else:
                jars_obj.append(('file', open(jar, 'rb')))
                jars_name_list.append(jar)
    if files:
        for _file in files.split(','):
            if not os.path.exists(_file):
                fatal('File {} not exist'.format(_file))
            else:
                files_obj.append(('file', open(_file, 'rb')))
                files_name_list.append(_file)
    if py_files:
        for pyfile in py_files.split(','):
            if not os.path.exists(pyfile):
                fatal('Pyfile {} not exist'.format(pyfile))
            else:
                pyfiles_obj.append(('file', open(pyfile, 'rb')))
                pyfiles_name_list.append(pyfile)

    with handle_console_err():
        data['mainApplicationFile'] = kae.upload(appname, 'mainfile', mainfile_obj)['data']['path']
        data['deps']['jars'] = kae.upload(appname, 'jars', jars_obj)['data']['path']
        data['deps']['files'] = kae.upload(appname, 'files', files_obj)['data']['path']
        data['deps']['pyFiles'] = kae.upload(appname, 'pyfiles', pyfiles_obj)['data']['path']

        kae.create_sparkapp(data=data)

    click.echo(info('Create sparkapp done.'))


@click.option('--raw', default=False, is_flag=True, help='print the raw json')
@click.pass_context
def list_sparkapp(ctx, raw):
    kae = ctx.obj['kae_api']
    with handle_console_err():
        sparkapps = kae.list_sparkapp()

    if raw:
        pprint(sparkapps)
    else:
        table = PrettyTable(['name', 'type', 'd-cores', 'd-memory', 'e-cores', 'e-memory', 'e-number', 
                            'status', 'user', 'craeted', 'schedule', 'concurrency'])
        for r in sparkapps:
            specs_text = yaml.load(r['specs_text'])

            table.add_row([
                r['name'], specs_text['apptype'], specs_text['driver']['cpu'], specs_text['driver']['memory'],
                specs_text['executor']['cpu'], specs_text['executor']['memory'], specs_text['executor']['instances'],
                r['status'], r['nickname'], r['created'], specs_text.get('schedule', None), specs_text.get('concurrencyPolicy', None)
            ])

        click.echo(table)


@click.option('--yes', is_flag=True, callback=abort_if_false, expose_value=False, prompt='Are you sure you want to delete the app?')
@click.argument('appname', required=True)
@click.pass_context
def delete_sparkapp(ctx, appname):
    kae = ctx.obj['kae_api']
    with handle_console_err():
        result = kae.delete_sparkapp(appname)

    if not result['error']:
        click.echo(info('Delete spark application {} successfully'.format(appname)))
    else:
        click.echo(error(result['error']))


@click.argument('appname', required=True)
@click.pass_context
def restart_sparkapp(ctx, appname):
    kae = ctx.obj['kae_api']
    with handle_console_err():
        result = kae.restart_sparkapp(appname)
    click.echo(str(result))


@click.argument('appname', required=True)
@click.option('-f', '--follow', default=False, is_flag=True, help='follow the log stream')
@click.pass_context
def get_sparkapp_log(ctx, appname, follow):
    kae = ctx.obj['kae_api']
    with handle_console_err():
        if follow is False:
            result = kae.get_sparkapp_log(appname)
            click.echo(result)
        else:
            resp = kae.get_sparkapp_log(appname, follow)
            for m in resp:
                click.echo(m)

    click.echo(info('log end..'))


@click.argument('files', nargs=-1, required=True)
@click.option('--appname', required=True, help='appname')
@click.option('--type', required=True, help='file type. mainfile, jars, pyfiles or files')
@click.pass_context
def upload(ctx, appname, files, type):
    upload_files = []

    kae = ctx.obj['kae_api']

    for f in files:
        if not os.path.exists(f):
            fatal('File {} not exist'.format(f))
        else:
            upload_files.append(('file', (f, open(f, 'rb'))))

    with handle_console_err():
        res = kae.upload(appname, type, upload_files)

    if res['error']:
        fatal(res['error'])

    click.echo(info('upload successful'))
