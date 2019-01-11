#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import
import os
import shlex
import subprocess

import click

from .utils import info, error, fatal


def _docker(args, cwd=None, env=os.environ, capture_output=False, print_stdout=True):
    """
    Wrapper of Docker client. Use subprocess instead of docker-py to
    avoid API version inconsistency problems.
    Args:
        args: Argument list to pass to Docker client.
        cwd: Current working directory to run Docker under.
        env: Environemnt variable dict to pass to Docker client.
    Returns:
        Combined output of stdout + stderr, or return code (int).
    Raises:
        None.
    """

    cmd = ['docker'] + args
    env = dict(env)

    if capture_output:
        try:
            output = subprocess.check_output(
                cmd, env=env, cwd=cwd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            output = e.output
        return output
    else:
        retcode = subprocess.call(cmd, env=env, cwd=cwd, stderr=subprocess.STDOUT,
                                  stdout=(None if print_stdout else open('/dev/null', 'w')))
        return retcode


def build_image(name, context, build_args, dockerfile=None, use_cache=True):
    click.echo(info('building image {} ...'.format(name)))
    if use_cache:
        options = ['-t', name, ]
    else:
        options = ['-t', name, '--no-cache', ]

    if build_args:
        options = ['-t', name]
        for arg in build_args:
            key, val = arg.split('=', 1)
            if val.startswith('$'):
                val = os.environ[val[1:]]
            options.append('--build-arg')
            options.append('{}={}'.format(key, val))
    if dockerfile is not None:
        options += ['-f', dockerfile]
    docker_args = ['build'] + options + ['--network', 'host', '.']
    retcode = _docker(docker_args, cwd=context)
    if retcode != 0:
        name = None
        fatal('build failed. See errors above.')
    else:
        click.echo(info('build succeeded: {}'.format(name)))
    return name


def run_container(image, volumes, cmd_list, name=None):
    if name is None:
        docker_args = [
            'run', '--rm', '--network', 'host',
        ]
    else:
        docker_args = [
            'run', '--name', name, '--rm', '--network', 'host',
        ]
    entrypoints_args = ['--entrypoint', "sh"]
    volumes_args = []
    for volume in volumes:
        volumes_args.extend(['-v', volume])
    docker_args += entrypoints_args + volumes_args + \
                   [image, '-c',  '{}'.format(" && ".join(cmd_list))]
    retcode = _docker(docker_args)
    if retcode != 0:
        name = None
        fatal('run container failed. See errors above.')
    else:
        click.echo(info('run container succeeded: {}'.format(name)))
