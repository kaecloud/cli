#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import
import sys
import os
import re
import errno
from os import getenv
from contextlib import contextmanager

import click
import delegator
import json
import yaml
from click import ClickException
from reprint import output
from prettytable import PrettyTable
from kaelib import KaeAPIError

_GITLAB_CI_REMOTE_URL_PATTERN = re.compile(r'http://gitlab-ci-token:(.+)@([\.\w]+)/([-\w]+)/([-/\w]+).git')


def warn(text):
    return click.style(text, fg='yellow')


def error(text):
    return click.style(text, fg='red', bold=True)


def normal(text):
    return click.style(text, fg='white')


def info(text):
    return click.style(text, fg='green')


def debug_log(fmt, *args):
    return normal(fmt % args)


def fatal(msg):
    click.echo(error(msg))
    sys.exit(1)


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


@contextmanager
def handle_console_err():
    try:
        yield
    except KaeAPIError as e:
        if e.http_code == 404:
            fatal("resource not found: {}".format(str(e)))
        elif 400 <= e.http_code <= 409:
            fatal(e.msg)
        else:
            fatal("Internel Error: {}".format(e.msg))


def get_current_branch(cwd=None):
    """inside gitlab-ci, repo is at detached state, so you cannot get branch
    name from the current git repo, but luckily there's a environment
    variable called CI_BUILD_REF_NAME"""
    ctx = click.get_current_context()
    r = delegator.run('git rev-parse --abbrev-ref HEAD', cwd=cwd)
    if r.return_code:
        if ctx.obj['debug']:
            click.echo(debug_log('get_current_branch error: (stdout)%s, (stderr)%s', r.out, r.err))

        return ''

    branch = r.out.strip()
    if branch == 'HEAD':
        branch = getenv('CI_BUILD_REF_NAME', '')

    if ctx.obj['debug']:
        click.echo(debug_log('get_branch: %s', branch))

    return branch


def get_commit_hash(cwd=None):
    """拿cwd的最新的commit hash."""
    ctx = click.get_current_context()

    r = delegator.run('git rev-parse HEAD', cwd=cwd)
    if r.return_code:
        raise ClickException(r.err)

    commit_hash = r.out.strip()
    if ctx.obj['debug']:
        click.echo(debug_log('get_commit_hash: %s', commit_hash))
    return commit_hash


def get_git_tag(cwd=None, git_tag=None, required=True):
    if git_tag is not None:
        return git_tag
    ctx = click.get_current_context()

    r = delegator.run('git describe --exact-match --abbrev=0 --tags', cwd=cwd)
    if r.return_code:
        if required is True:
            fatal(r.err)
        else:
            click.echo(warn(r.err))
            return None

    git_tag = r.out.strip()
    if ctx.obj['debug']:
        click.echo(debug_log('get_git_tag: %s', git_tag))
    if (not git_tag) and (required is True):
        fatal('git tag not specified, check repo or pass argument to it.')
    return git_tag


def get_remote_url(cwd=None, remote='origin'):
    """拿cwd的remote的url.
    发现envoy.run的command只能是bytes, 不能是unicode.
    """
    ctx = click.get_current_context()

    r = delegator.run('git remote get-url %s' % str(remote), cwd=cwd)
    if r.return_code:
        raise ClickException(r.err)

    remote = r.out.strip()

    # 对gitlab ci需要特殊处理一下
    # 丫有个特殊的格式, 不太好支持...
    match = _GITLAB_CI_REMOTE_URL_PATTERN.match(remote)
    if match:
        host = match.group(2)
        group = match.group(3)
        project = match.group(4)
        return 'git@{host}:{group}/{project}.git'.format(host=host, group=group, project=project)

    if ctx.obj['debug']:
        click.echo(debug_log('get_remote_url: %s', remote))
    return remote


def get_appname(cwd=None, appname=None, required=True):
    if appname:
        return appname
    try:
        with open(os.path.join(cwd or os.getcwd(), 'app.yaml'), 'r') as f:
            specs = yaml.safe_load(f)
    except IOError:
        if required:
            fatal('appname not specified, check app.yaml or pass argument to it.')
        return ''
    appname = specs.get('appname', '')

    if (required is True) and (not appname):
        fatal('appname not specified, check app.yaml or pass argument to it.')
    return appname


def read_json_file(path):
    try:
        with open(path) as f:
            return json.loads(f.read())
    except (OSError, IOError):
        return None


def read_yaml_file(path):
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except (OSError, IOError):
        return None


def write_yaml_file(data, path):
    mkdir_p(os.path.dirname(path))
    try:
        with open(path, 'w') as f:
            yaml.dump(data, f)
    except (OSError, IOError):
        return None


def get_specs_text_from_repo(cwd=None):
    try:
        with open(os.path.join(cwd or os.getcwd(), 'app.yaml'), 'r') as f:
            return f.read()
    except IOError:
        return None


def get_specs_text(fname, literal):
    if literal:
        specs_text = literal
    elif fname:
        try:
            with open(fname, "r") as fp:
                specs_text = fp.read()
        except:
            fatal("can't read specs text from {}".format(fname))
    else:
        specs_text = get_specs_text_from_repo()
    return specs_text


def merge_list(l1, l2):
    len1 = len(l1)
    len2 = len(l2)
    min_len = min(len1, len2)
    l1[:min_len] = l2[:min_len]

    if len1 < len2:
        l1.extend(l2[len1:])
    else:
        l1[len2:] = ["" for i in range(len1 - len2)]


def display_pods(kae, watcher, appname, canary=False, forever=False):
    def get_replicas(appname):
        with handle_console_err():
            dp = kae.get_app_deployment(appname, canary)
            return dp['spec']['replicas']

    def extract_data_from_pod(pod):
        status = pod['status']['phase']
        restart_count = 0
        ready_count = 0
        ready_total = len(pod['spec']['containers'])
        c_status_list = pod['status'].get('container_statuses', None)
        if c_status_list:
            for cont_status in c_status_list:
                if cont_status['ready']:
                    ready_count += 1
                else:
                    if cont_status['state'].get('terminated', None):
                        status = cont_status['state']['terminated']['reason']
                    elif cont_status['state'].get('waiting', None):
                        status = cont_status['state']['waiting']['reason']
            if cont_status['restart_count'] > restart_count:
                restart_count = cont_status['restart_count']
        return {
            'ready_count': ready_count,
            'ready_total': ready_total,
            "ready": "{}/{}".format(ready_count, ready_total),
            "name": pod['metadata']['name'],
            'status': status,
            'restarts': restart_count,
            'ip': pod['status'].get('pod_ip', None),
            'node': pod['status'].get('host_ip', None),
        }

    def print_table(pod_map, output_list):
        ready_pods = 0
        table = PrettyTable(['name', 'status', 'ready', 'restarts', 'ip', 'node'])
        for name, pod in pod_map.items():
            data = extract_data_from_pod(pod)
            table.add_row([name, data['status'], data['ready'], data['restarts'], data['ip'], data['node']])
            if data['ready_count'] == data['ready_total']:
                ready_pods += 1
        merge_list(output_list, str(table).split('\n'))
        return ready_pods

    pod_map = {}
    replicas = get_replicas(appname)

    with output(output_type="list", initial_len=10, interval=0) as output_list:
        ready_pods = print_table(pod_map, output_list)
        if ready_pods == replicas and ready_pods == len(pod_map):
            return

        for m in watcher:
            action = m['action']
            pod = m["object"]
            name = pod['metadata']['name']
            if action == 'DELETED':
                pod_map.pop(name, None)
            else:
                pod_map[name] = pod
            # display table
            ready_pods = print_table(pod_map, output_list)
            if forever is False and ready_pods == replicas and ready_pods == len(pod_map):
                return


def abort_if_false(ctx, param, value):
    if not value:
        ctx.abort()
