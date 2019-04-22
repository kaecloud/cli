#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import

from .action import (
    deploy_app,
    deploy_app_canary,
    build_app,
    scale_app,
)


from .app import (
    get_app,
    delete_app,
    delete_app_canary,
    get_app_releases,
    get_app_pods,
    get_release,
    get_release_specs,
    watch_app_pods,

    get_secret,
    set_secret,
    get_config,
    set_config,

    register_release,
    rollback,
    renew,

    set_app_abtesting_rules,
)

from .job import (
    create_job,
    list_job,
    delete_job,
    get_job_log,
)

from .spark import (
    create_sparkapp,
    list_sparkapp,
    delete_sparkapp,
    restart_sparkapp,
    get_sparkapp_log,
    upload,
)

from .test import test, build_local
from .create_app import create_web_app


commands = {
    'app:get': get_app,
    'app:release': get_app_releases,
    'app:delete': delete_app,
    'app:delete_canary': delete_app_canary,
    'app:pods': get_app_pods,
    'app:watch_pods': watch_app_pods,

    'app:set_abtesting': set_app_abtesting_rules,

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
    'app:deploy_canary': deploy_app_canary,
    'app:build': build_app,
    'app:scale': scale_app,

    'job:create': create_job,
    'job:list': list_job,
    'job:delete': delete_job,
    'job:log': get_job_log,

    'spark:create': create_sparkapp,
    'spark:list': list_sparkapp,
    'spark:delete': delete_sparkapp,
    'spark:restart': restart_sparkapp,
    'spark:log': get_sparkapp_log,
    'spark:upload': upload,

    'create-web-app': create_web_app,
    'test': test,
    'build': build_local,
}
