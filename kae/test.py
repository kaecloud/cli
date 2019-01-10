#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import
import os
import yaml
import click

from kaelib.spec import app_specs_schema
from kae.utils import (
    get_appname, get_current_branch, get_remote_url, get_git_tag,
    get_specs_text, error, info, fatal, handle_console_err,
    display_pods,
)
from kae.docker import build_image, run_container


@click.argument('appname', required=False)
@click.argument('tag', required=False)
@click.option('-f', help='filename of specs')
@click.option('--literal')
def test(appname, tag, f, literal):
    """build test image and run test script in app.yaml"""
    repo_dir = os.getcwd()
    if f:
        repo_dir = os.path.dirname(os.path.abspath(f))

    appname = get_appname(cwd=repo_dir, appname=appname)
    tag = get_git_tag(cwd=repo_dir, git_tag=tag, required=False)
    if tag is None:
        tag = 'latest'

    specs_text = get_specs_text(f, literal)
    if specs_text is None:
        errmsg = [
            "specs_text is required, please use one of the instructions to specify it.",
            "1. specify --literal or -f in coomand line",
            "2. make the current workdir in the source code dir which contains app.yaml"
        ]
        fatal('\n'.join(errmsg))
    try:
        yaml_dict = yaml.load(specs_text)
    except yaml.YAMLError as e:
        fatal('specs text is invalid yaml {}'.format(str(e)))
    try:
        specs = app_specs_schema.load(yaml_dict).data
    except Exception as e:
        fatal('specs text is invalid: {}'.format(str(e)))
    if "test" not in specs:
        fatal("no test specified in app.yaml")
    builds = specs['test']['builds']
    if len(builds) == 0:
        builds = specs["builds"]
    for build in builds:
        image_tag = build.tag if build.tag else tag
        dockerfile = build.get('dockerfile', None)
        if dockerfile is None:
            dockerfile = os.path.join(repo_dir, "Dockerfile")
        full_image_name = "{}:{}".format(build.name, image_tag)
        build_image(full_image_name, repo_dir, None, dockerfile=dockerfile)

    default_image_name = "{}:{}".format(appname, tag)
    for entrypoint in specs['test']['entrypoints']:
        image = entrypoint.image if entrypoint.image else default_image_name
        cmd = entrypoint.script
        volumes = entrypoint.get('volumes', [])
        run_container(image, volumes, cmd)


@click.argument('appname', required=False)
@click.argument('tag', required=False)
@click.option('-f', help='filename of specs')
@click.option('--literal')
@click.option('--test', default=False, is_flag=True, help='build test image')
def build_local(appname, tag, f, literal, test):
    """build local image """
    repo_dir = os.getcwd()
    if f:
        repo_dir = os.path.dirname(os.path.abspath(f))
    appname = get_appname(cwd=repo_dir, appname=appname)
    tag = get_git_tag(cwd=repo_dir, git_tag=tag, required=False)
    if tag is None:
        tag = 'latest'

    specs_text = get_specs_text(f, literal)
    if specs_text is None:
        errmsg = [
            "specs_text is required, please use one of the instructions to specify it.",
            "1. specify --literal or -f in coomand line",
            "2. make the current workdir in the source code dir which contains app.yaml"
        ]
        fatal('\n'.join(errmsg))
    try:
        yaml_dict = yaml.load(specs_text)
    except yaml.YAMLError as e:
        fatal('specs text is invalid yaml {}'.format(str(e)))
    try:
        specs = app_specs_schema.load(yaml_dict).data
    except Exception as e:
        fatal('specs text is invalid: {}'.format(str(e)))

    builds = specs["builds"]
    if test:
        if "test" not in specs:
            fatal("no test specified in app.yaml")
        builds = specs['test']['builds']
    if len(builds) == 0:
        fatal("no builds found")

    for build in builds:
        image_tag = build.tag if build.tag else tag
        dockerfile = build.get('dockerfile', None)
        if dockerfile is None:
            dockerfile = os.path.join(repo_dir, "Dockerfile")
        full_image_name = "{}:{}".format(build.name, image_tag)
        build_image(full_image_name, repo_dir, None, dockerfile=dockerfile)
