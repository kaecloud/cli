#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import
import six
from six.moves.urllib.parse import urljoin
import os
import pickle
import logging
import json as jsonlib
import sseclient
from requests import Session
from .errors import ConsoleAPIError

logger = logging.getLogger(__name__)


class ConsoleAPI:
    def __init__(self, host, version='v1', timeout=None,
                 password='', auth_token='', cookie_dir='~/.kae',
                 cluster='default'):
        self.host = host
        self.version = version
        self.timeout = timeout
        self.auth_token = auth_token
        self.cookie_dir = os.path.expanduser(cookie_dir)
        self.cluster = cluster

        self.host = host
        self.base = '%s/api/%s/' % (self.host, version)
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

    def set_cluster(self, cluster):
        self.cluster = cluster

    def request(self, path, method='GET', params=None, data=None, json=None, **kwargs):
        """Wrap around requests.request method"""
        url = urljoin(self.base, path)
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
        url = urljoin(self.base, path)
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

    def request_sse(self, path, method='GET', params=None, data=None, json=None, **kwargs):
        url = urljoin(self.base, path)
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

        client = sseclient.SSEClient(resp)
        for event in client.events():
            try:
                if event.event == 'close':
                    return
                yield jsonlib.loads(event.data)
            except (ValueError, TypeError):
                raise ConsoleAPIError(500, str(event))

    def get_app(self, appname):
        return self.request('app/%s' % appname)

    def delete_app(self, appname):
        return self.request('app/%s' % appname, method='DELETE')

    def get_app_pods(self, appname, watch=False):
        params = {
            'cluster': self.cluster,
        }
        if watch is False:
            return self.request('app/%s/pods' % appname, params=params)
        else:
            return self.request_sse('app/%s/pods/events' % appname, params=params)

    def get_app_releases(self, appname):
        return self.request('app/%s/releases' % appname)

    def get_app_deployment(self, appname):
        params = {
            'cluster': self.cluster,
        }
        return self.request('app/%s/deployment' % appname, params=params)

    def get_release(self, appname, tag):
        return self.request('app/%s/version/%s' % (appname, tag))

    def get_secret(self, appname):
        params = {
            'cluster': self.cluster,
        }
        return self.request('app/%s/secret' % appname, params=params)

    def set_secret(self, appname, data):
        payload = {
            'cluster': self.cluster,
            'data': data,
        }
        return self.request('app/%s/secret' % appname, method="POST", json=payload)

    def get_config(self, appname):
        params = {
            'cluster': self.cluster,
        }
        return self.request('app/%s/configmap' % appname, params=params)

    def set_config(self, appname, config_name, data):
        payload = {
            'cluster': self.cluster,
            'config_name': config_name,
            'data': data,
        }
        return self.request('app/%s/configmap' % appname, method="POST", json=payload)

    def register_release(self, appname, tag, git, specs_text, branch=None):
        payload = {
            'appname': appname,
            'tag': tag,
            'git': git,
            'specs_text': specs_text,
            'branch': branch,
        }
        return self.request('app/register', method='POST', json=payload)

    def rollback(self, appname, revision=0):
        payload = {
            'cluster': self.cluster,
            'revision': revision,
        }
        return self.request('app/%s/rollback' % appname, method='PUT', json=payload)

    def renew(self, appname):
        payload = {
            'cluster': self.cluster,
        }
        return self.request('app/%s/renew' % appname, method='PUT', json=payload)

    def build_app(self, appname, tag):
        payload = {'tag': tag}
        return self.request_sse('app/%s/build' % appname, params=payload)

    def deploy(self, appname, tag, cpus, memories, replicas, **kwargs):
        """deploy app.
        tag: 要部署的版本号, git tag的值.
        cpu_quota: 需要的cpu个数, 例如1, 或者1.5, 如果是public的部署, 传0.
        memory: 最小4MB.
        replicas: app的副本数量
        """
        payload = {
            'cluster': self.cluster,
            'tag': tag,
            'cpus': cpus,
            'memories': memories,
            'replicas': replicas,
        }

        payload.update(kwargs)
        return self.request('app/%s/deploy' % appname, method='PUT', data=payload)

    def scale(self, appname, cpus, memories, replicas, **kwargs):
        """deploy app.
        cpu: 需要的cpu个数, 例如1, 或者1.5, 如果是public的部署, 传0.
        memory: 最小4MB.
        replicas: app的副本数量
        """
        payload = {
            'cluster': self.cluster,
            'cpus': cpus,
            'memories': memories,
            'replicas': replicas,
        }

        payload.update(kwargs)
        return self.request('app/%s/scale' % appname, method='PUT', data=payload)

    def create_job(self, specs_text=None, **kwargs):
        payload = kwargs
        if specs_text:
            payload = {
                'specs_text': specs_text,
            }
        return self.request('job', method='POST', json=payload)

    def list_job(self):
        return self.request('job', method='GET')

    def delete_job(self, jobname):
        return self.request('job/%s' % jobname, method='DELETE')

    def get_job_log(self, jobname, follow=False):
        if follow is False:
            return self.request('job/%s/log' % jobname)
        else:
            return self.request_sse('job/%s/log/events' % jobname)
