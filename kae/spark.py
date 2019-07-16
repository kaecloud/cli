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
    abort_if_false, fatal, info, handle_console_err, error, read_yaml_file
)


@click.argument('mainFile', required=False)
@click.argument('arguments', nargs=-1, required=False)
@click.option('-f', help='spec yaml file')
@click.option('--appname', help='appname')
@click.option('--apptype', default='sparkapplication', type=click.Choice(['sparkapplication', 'scheduledsparkapplication']), help="app type")
@click.option('--schedule', help='schedule')
@click.option('--concurrency-policy', default='Allow', type=click.Choice(['Allow', 'Forbid', 'Replace']), help='The concurrency policy')
@click.option('--image', help='image')
@click.option('--pythonVersion', default='3', help='python version')
@click.option('--conf', multiple=True, help='configure')
@click.option('--sparkVersion', default='2.4.0', help='spark version')
@click.option('--mode', default='client', help='mode')
@click.option('--jars', help='jars')
@click.option('--files', help='files')
@click.option('--py-files', help='pyfiles')
@click.option('--packages', help='packages')
@click.option('--repositories', help='repositories')
@click.option('--driver-memory', default='512m')
@click.option('--driver-cores', type=int, default=1)
@click.option('--executor-memory', default='512m')
@click.option('--executor-cores', type=int, default=1)
@click.option('--number-executors', type=int, default=1)
@click.option('--selector', multiple=True, help='Selector')
@click.option('--comment', help='comment')
@click.pass_context
def create_sparkapp(ctx, mainfile, arguments, f, appname, apptype, schedule, concurrency_policy,
                    image, pythonversion, conf, sparkversion, mode,
                    jars, files, py_files, packages, repositories, driver_memory, driver_cores,
                    executor_memory, executor_cores, number_executors, selector, comment):
    kae = ctx.obj['kae_api']
    data = {}
    required = ['appname', 'image', 'mainfile']

    if f:
        if not os.path.exists(f):
            fatal('The yaml file not exists!')
        else:
            data = read_yaml_file(f)

            if not data:
                fatal('yaml error')
            else:
                if not data.get('driver'):
                    data['driver'] = {
                        'cpu': 1,
                        'memory': '512m'
                    }

                if not data.get('executor'):
                    data['executor'] = {
                        'cpu': 1,
                        'memory': '512m',
                        'instances': 1
                    }
    else:
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
            'mainfile': mainfile,
            'comment': comment or ''
        }

        sparkConf = {}
        for item in conf:
            k, v = item.split('=')
            sparkConf[k] = v

        if sparkConf:
            data['sparkConf'] = sparkConf

        nodeSelector = {}
        for item in selector:
            k, v = item.split('=')
            nodeSelector[k] = v

        if nodeSelector:
            data['nodeSelector'] = nodeSelector
        if arguments:
            data['arguments'] = list(arguments)
        if data['apptype'] == 'scheduledsparkapplication':
            if not schedule:
                fatal('Scheduledsparkapplication must should spec `shedule`')
            else:
                data['schedule'] = schedule

            data['concurrencyPolicy'] = concurrency_policy

        if jars:
            data['jars'] = jars.split(',')
        if files:
            data['files'] = files.split(',')
        if py_files:
            data['py-files'] = py_files.split(',')

    for require_key in required:
        if require_key not in data.keys():
            fatal('Miss required argument {}'.format(require_key))

    data.setdefault('deps', {})

    jars_obj = []
    files_obj = []
    pyfiles_obj = []

    remote_jars = []
    remote_files = []
    remote_pyfiles = []

    # file_type_map = {
    #     'mainfile': 'mainApplicationFile',
    #     'jars': 'jars',
    #     'files': 'files',
    #     'py-files': 'pyFiles'
    # }
    remote_file_protocol = ['s3a://', 'hdfs://']

    def pre_upload(path):
        protocol = path.split('//')[0] + '//'
        if protocol in remote_file_protocol:
            return False
        if not os.path.exists(path):
            fatal('File {} not exist'.format(path))
        return True

    if pre_upload(data['mainfile']):
        mainfile_obj = (('file', open(data['mainfile'], 'rb')), )
        data['mainApplicationFile'] = kae.upload(data['appname'], 'mainfile', mainfile_obj)['data']['path']
    else:
        data['mainApplicationFile'] = data['mainfile']

    for jar_path in data.get('jars', []):
        if pre_upload(jar_path):
            jars_obj.append(('file', open(jar_path, 'rb')))
        else:
            remote_jars.append(jar_path)
    for file_path in data.get('files', []):
        if pre_upload(file_path):
            files_obj.append(('file', open(file_path, 'rb')))
        else:
            remote_files.append(file_path)
    for pyfile_path in data.get('py-files', []):
        if pre_upload(pyfile_path):
            pyfiles_obj.append(('file', open(pyfile_path, 'rb')))
        else:
            remote_pyfiles.append(pyfile_path)

    data['deps']['jars'] = kae.upload(data['appname'], 'jars', jars_obj)['data']['path'] + remote_jars
    data['deps']['files'] = kae.upload(data['appname'], 'files', files_obj)['data']['path'] + remote_files
    data['deps']['pyFiles'] = kae.upload(data['appname'], 'pyfiles', pyfiles_obj)['data']['path'] + remote_pyfiles

    with handle_console_err():
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
            specs_text = yaml.safe_load(r['specs_text'])

            table.add_row([
                r['name'], specs_text['apptype'], specs_text['driver']['cpu'], specs_text['driver']['memory'],
                specs_text['executor']['cpu'], specs_text['executor']['memory'], specs_text['executor']['instances'],
                r['status'], r['nickname'], r['created'], specs_text.get('schedule', None), specs_text.get('concurrencyPolicy', None)
            ])

        click.echo(table)


@click.option('--yes', is_flag=True, callback=abort_if_false, expose_value=False, prompt='Are you sure you want to delete the app?')
@click.argument('appname', required=False)
@click.option('-f', help='spec yaml file')
@click.pass_context
def delete_sparkapp(ctx, appname, f):
    kae = ctx.obj['kae_api']

    if f:
        if not os.path.exists(f):
            fatal('The yaml file not exists!')
        else:
            data = read_yaml_file(f)

            if not data:
                fatal('yaml error')

            else:
                appname = data['appname']

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
