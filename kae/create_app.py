#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import
import os
import shutil
from jinja2 import Template
from pkg_resources import resource_string, resource_filename

import click
from kae.utils import (
    get_appname, get_current_branch, get_remote_url, get_git_tag,
    get_specs_text, error, info, fatal, handle_console_err,
    display_pods,
)


@click.argument('app_type', required=True)
@click.pass_context
def create_web_app(ctx, app_type):
    ty = app_type.lower()
    if ty == "flask":
        create_flask_app()
    elif ty == "tornado":
        create_tornado_app()
    elif ty == "go":
        create_go_app()
    elif ty == "node":
        create_node_app()
    else:
        click.echo("unknown app type, flask, tornado, go, node are allowed")
        raise click.Abort()


def _common():
    app_yaml_tpl = Template(resource_string(__name__, "tpl/app.yaml").decode('utf8'))

    appname = click.prompt(info('Please enter app name'), type=str)
    hostname = click.prompt(info('Please enter domain'), type=str)
    port = click.prompt(info('Please enter listen port'), type=int, default=8080)
    replicas = click.prompt(info('Please enter replicas'), type=int, default=1)

    mappings = {
        "appname": appname,
        "hostname": hostname,
        "port": port,
        "replicas": replicas,
    }
    if os.path.exists(appname):
        click.echo(error("dir {} exists".format(appname)))
        raise click.Abort()

    os.mkdir(appname)
    with open(os.path.join(appname, "app.yaml"), "w") as fp:
        fp.write(app_yaml_tpl.render(**mappings))

    shutil.copyfile(
            resource_filename(__name__, "tpl/gitlab-ci.yml"),
            os.path.join(appname, ".gitlab-ci.yml"))
    return mappings


def create_flask_app():
    mappings = _common()

    dockerfile_tpl = Template(resource_string(__name__, "tpl/flask/Dockerfile").decode('utf8'))
    gunicorn_tpl = Template(resource_string(__name__, "tpl/flask/gunicorn_config.py").decode('utf8'))

    entrypoint = click.prompt('Please enter entry point', type=str, default="app:app")
    workers = click.prompt('Please enter gunicorn workers', type=int, default=1)

    mappings.update({
        "entrypoint": entrypoint,
        "workers": workers
    })
    appname = mappings['appname']
    with open(os.path.join(appname, "Dockerfile"), "w") as fp:
        fp.write(dockerfile_tpl.render(**mappings))

    with open(os.path.join(appname, "gunicorn_config.py"), "w") as fp:
        fp.write(gunicorn_tpl.render(**mappings))

    shutil.copyfile(
        resource_filename(__name__, "tpl/flask/requirements.txt"),
        os.path.join(appname, "requirements.txt"))
    shutil.copyfile(
        resource_filename(__name__, "tpl/flask/app.py"),
        os.path.join(appname, "app.py"))


def create_tornado_app():
    mappings = _common()

    dockerfile_tpl = Template(resource_string(__name__, "tpl/tornado/Dockerfile").decode('utf8'))
    app_py_tpl = Template(resource_string(__name__, "tpl/tornado/app.py").decode('utf8'))

    appname = mappings['appname']
    with open(os.path.join(appname, "Dockerfile"), "w") as fp:
        fp.write(dockerfile_tpl.render(**mappings))

    with open(os.path.join(appname, "app.py"), "w") as fp:
        fp.write(app_py_tpl.render(**mappings))

    shutil.copyfile(
        resource_filename(__name__, "tpl/tornado/requirements.txt"),
        os.path.join(appname, "requirements.txt"))


def create_go_app():
    mappings = _common()

    dockerfile_tpl = Template(resource_string(__name__, "tpl/go/Dockerfile").decode('utf8'))
    main_go_tpl = Template(resource_string(__name__, "tpl/go/main.go").decode('utf8'))

    appname = mappings['appname']
    with open(os.path.join(appname, "main.go"), "w") as fp:
        fp.write(main_go_tpl.render(**mappings))

    with open(os.path.join(appname, "Dockerfile"), "w") as fp:
        fp.write(dockerfile_tpl.render(**mappings))


def create_node_app():
    mappings = _common()

    dockerfile_tpl = Template(resource_string(__name__, "tpl/node/Dockerfile").decode('utf8'))

    appname = mappings['appname']

    with open(os.path.join(appname, "Dockerfile"), "w") as fp:
        fp.write(dockerfile_tpl.render(**mappings))
