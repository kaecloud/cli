#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import

from .action import (
    deploy_app,
    build_app,
    scale_app,
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

from .job import (
    create_job,
    list_job,
    delete_job,
    get_job_log,
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

    'app:register': register_release,
    'app:rollback': rollback,
    'app:renew': renew,

    'app:deploy': deploy_app,
    'app:build': build_app,
    'app:scale': scale_app,

    'job:create': create_job,
    'job:list': list_job,
    'job:delete': delete_job,
    'job:log': get_job_log,
}
