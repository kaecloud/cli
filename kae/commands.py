#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import

from .action import (
    deploy,
    build,
    scale,
)


from .app import (
    get_app,
    delete_app,
    get_app_releases,
    get_app_pods,
    get_release,
    get_release_specs,

    get_secret,
    set_secret,
    get_config,
    set_config,

    register_release,
    rollback,
    renew,
)

commands = {
    'app:get': get_app,
    'app:release': get_app_releases,
    'app:delete': delete_app,
    'app:pods': get_app_pods,

    'release:get': get_release,
    'release:specs': get_release_specs,

    'secret:get': get_secret,
    'secret:set': set_secret,

    'config:get': get_config,
    'config:set': set_config,

    'rollback': rollback,
    'register': register_release,
    'renew': renew,

    'deploy': deploy,
    'build': build,
    'scale': scale,
}
