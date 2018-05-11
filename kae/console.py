#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import
import six
import os
import pickle
import logging
import json as jsonlib
from requests import Session
from .errors import ConsoleAPIError

logger = logging.getLogger(__name__)


class ConsoleAPI:
    def __init__(self, host, version='v1', timeout=None, password='', auth_token='', cookie_dir='~/.kae'):
        self.host = host
        self.version = version
        self.timeout = timeout
        self.auth_token = auth_token
        self.cookie_dir = os.path.expanduser(cookie_dir)

        self.base = '%s/api/%s' % (self.host, version)
        self.session = Session()
        self.session.headers.update({'X-Access-Token': auth_token})

    def _save_cookie(self, cookies):
        fname = os.path.join(self.cookie_dir, "cookie")
        try:
            with open(fname, "wb") as fp:
                pickle.dump(cookies, fp)
        except:
            pass

    def _load_cookie(self):
        fname = os.path.join(self.cookie_dir, "cookie")
        if not os.path.isfile(fname):
            return None
        try:
            with open(fname, "rb") as fp:
                return pickle.load(fp)
        except:
            return None

    def request(self, path, method='GET', params=None, data=None, json=None, **kwargs):
        """Wrap around requests.request method"""
        url = self.base + path
        params = params or {}
        cookies = self._load_cookie() or {}
        resp = self.session.request(url=url,
                                    method=method,
                                    params=params,
                                    cookies=cookies,
                                    data=data,
                                    json=json,
                                    timeout=self.timeout,
                                    **kwargs)
        self._save_cookie(self.session.cookies.get_dict())
        code = resp.status_code
        if code != 200:
            raise ConsoleAPIError(code, resp.text)
        try:
            response = resp.json()
        except ValueError:
            # when console don't return json, it means a bug
            raise ConsoleAPIError(500, 'BUG: Console did not return json, body {}'.format(resp.text))
        return response

    def request_stream(self, path, method='GET', params=None, data=None, json=None, **kwargs):
        url = self.base + path
        params = params or {}
        cookies = self._load_cookie() or {}
        resp = self.session.request(url=url,
                                    method=method,
                                    params=params,
                                    cookies=cookies,
                                    data=data,
                                    json=json,
                                    timeout=self.timeout,
                                    stream=True)

        code = resp.status_code
        if code != 200:
            raise ConsoleAPIError(code, resp.text)
        for line in resp.iter_lines():
            line = line.decode('utf8')
            try:
                yield jsonlib.loads(line)
            except (ValueError, TypeError):
                raise ConsoleAPIError(500, line)

    def get_app(self, appname):
        return self.request('/app/%s' % appname)

    def delete_app(self, appname):
        return self.request('/app/%s' % appname, method='DELETE')

    def get_app_pods(self, appname):
        return self.request('/app/%s/pods' % appname)

    def get_app_releases(self, appname):
        return self.request('/app/%s/releases' % appname)

    def get_app_deployments(self, appname):
        return self.request('/app/%s/deployments' % appname)

    def get_release(self, appname, tag):
        return self.request('/app/%s/version/%s' % (appname, tag))

    def get_secret(self, appname):
        return self.request('/app/%s/secret' % appname)

    def set_secret(self, appname, data):
        payload = {
            'data': data,
        }
        return self.request('/app/%s/secret' % appname, method="POST", json=payload)

    def get_config(self, appname):
        return self.request('/app/%s/configmap' % appname)

    def set_config(self, appname, config_name, data):
        payload = {
            'config_name': config_name,
            'data': data,
        }
        return self.request('/app/%s/configmap' % appname, method="POST", json=payload)

    def register_release(self, appname, tag, git, specs_text, branch=None):
        payload = {
            'appname': appname,
            'tag': tag,
            'git': git,
            'specs_text': specs_text,
            'branch': branch,
        }
        return self.request('/app/register', method='POST', json=payload)

    def rollback(self, appname, revision=0):
        payload = {
            'revision': revision,
        }
        return self.request('/app/%s/rollback' % appname, method='PUT', json=payload)

    def renew(self, appname):
        payload = {
        }
        return self.request('/app/%s/renew' % appname, method='PUT', json=payload)

    def build(self, appname, tag):
        payload = {'tag': tag}
        return self.request_stream('/app/%s/build' % appname, method='PUT', data=payload)

    def deploy(self, appname, tag, cpus, memories, replicas, **kwargs):
        """deploy app.
        tag: 要部署的版本号, git tag的值.
        cpu_quota: 需要的cpu个数, 例如1, 或者1.5, 如果是public的部署, 传0.
        memory: 最小4MB.
        replicas: app的副本数量
        """
        payload = {
            'tag': tag,
            'cpus': cpus,
            'memories': memories,
            'replicas': replicas,
        }

        payload.update(kwargs)
        return self.request_stream('/app/%s/deploy' % appname, method='PUT', data=payload)

    def scale(self, appname, cpus, memories, replicas, **kwargs):
        """deploy app.
        cpu: 需要的cpu个数, 例如1, 或者1.5, 如果是public的部署, 传0.
        memory: 最小4MB.
        replicas: app的副本数量
        """
        payload = {
            'cpus': cpus,
            'memories': memories,
            'replicas': replicas,
        }

        payload.update(kwargs)
        return self.request_stream('/app/%s/scale' % appname, method='PUT', data=payload)
