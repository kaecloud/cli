#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import
import six
from six.moves.urllib.parse import urljoin
import re
import os
import pickle
import logging
import json as jsonlib
from requests import Session
import websocket
from .errors import ConsoleAPIError

logger = logging.getLogger(__name__)


OPCODE_DATA = (websocket.ABNF.OPCODE_TEXT, websocket.ABNF.OPCODE_BINARY)


def recv(ws):
    try:
        frame = ws.recv_frame()
    except websocket.WebSocketException:
        return websocket.ABNF.OPCODE_CLOSE, None
    if not frame:
        raise websocket.WebSocketException("Not a valid frame %s" % frame)
    elif frame.opcode in OPCODE_DATA:
        return frame.opcode, frame.data
    elif frame.opcode == websocket.ABNF.OPCODE_CLOSE:
        ws.send_close()
        return frame.opcode, None
    elif frame.opcode == websocket.ABNF.OPCODE_PING:
        ws.pong(frame.data)
        return frame.opcode, frame.data

    return frame.opcode, frame.data


def recv_ws(ws):
    while True:
        opcode, data = recv(ws)
        msg = None
        if six.PY3 and opcode == websocket.ABNF.OPCODE_TEXT and isinstance(data, bytes):
            data = str(data, "utf-8")
        if opcode in OPCODE_DATA:
            msg = data

        if msg is not None:
            yield msg

        if opcode == websocket.ABNF.OPCODE_CLOSE:
            print('closed')
            break


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
        self.session.headers.update({'X-Private-Token': auth_token})

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

    def request_ws(self, path, params=None, data=None, json=None):
        url = urljoin(self.base, path)
        url = re.sub(r'^http', 'ws', url)
        options = {
            'header': [
                "X-Private-Token: {}".format(self.auth_token),
            ],
        }
        ws = websocket.create_connection(url, **options)
        ws.send(jsonlib.dumps(json))
        for msg in recv_ws(ws):
            # print('-----------------')
            # print(msg)
            try:
                data = jsonlib.loads(msg)
                yield data
            except (ValueError, TypeError):
                raise ConsoleAPIError(500, msg)

    def get_app(self, appname):
        return self.request('app/%s' % appname)

    def delete_app(self, appname):
        return self.request('app/%s' % appname, method='DELETE')

    def get_app_pods(self, appname, canary=False, watch=False):
        params = {
            'cluster': self.cluster,
            'canary': canary,
        }
        if watch is False:
            return self.request('app/%s/pods' % appname, params=params)
        else:
            return self.request_ws('ws/app/%s/pods/events' % appname, json=params)

    def watch_app_pods(self, appname, canary=False):
        payload = {
            'cluster': self.cluster,
            'canary': canary,
        }
        return self.request_ws('ws/app/%s/pods/events' % appname, json=payload)

    def get_app_releases(self, appname):
        return self.request('app/%s/releases' % appname)

    def get_app_deployment(self, appname, canary=False):
        params = {
            'cluster': self.cluster,
            'canary': canary,
        }
        return self.request('app/%s/deployment' % appname, params=params)

    def get_release(self, appname, tag):
        return self.request('app/%s/version/%s' % (appname, tag))

    def get_secret(self, appname):
        params = {
            'cluster': self.cluster,
        }
        return self.request('app/%s/secret' % appname, params=params)

    def set_secret(self, appname, data, replace=False):
        payload = {
            'cluster': self.cluster,
            'data': data,
            'replace': replace,
        }
        return self.request('app/%s/secret' % appname, method="POST", json=payload)

    def get_config(self, appname):
        params = {
            'cluster': self.cluster,
        }
        return self.request('app/%s/configmap' % appname, params=params)

    def set_config(self, appname, data, replace=False):
        payload = {
            'cluster': self.cluster,
            'data': data,
            'replace': replace,
        }
        return self.request('app/%s/configmap' % appname, method="POST", json=payload)

    def register_release(self, appname, tag, git, specs_text, branch=None, force=False):
        payload = {
            'appname': appname,
            'tag': tag,
            'git': git,
            'specs_text': specs_text,
            'branch': branch,
            'force': force,
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
        return self.request_ws('ws/app/%s/build' % appname, json=payload)

    def deploy_app(self, appname, tag, cpus=None, memories=None, replicas=None, app_yaml_name=None):
        """deploy app.
        appname:
        tag: 要部署的版本号, git tag的值.
        cpus: 需要的cpu个数, 例如1, 或者1.5, 如果是public的部署, 传0.
        memories: 最小4MB.
        replicas: app的副本数量
        app_yaml_name: AppYaml template name
        """
        payload = {
            'cluster': self.cluster,
            'tag': tag,
            'cpus': cpus,
            'memories': memories,
            'replicas': replicas,
            'app_yaml_name': app_yaml_name,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.request('app/%s/deploy' % appname, method='PUT', data=payload)

    def deploy_app_canary(self, appname, tag, cpus=None, memories=None, replicas=None, app_yaml_name=None):
        """deploy canary version of specified app
        appname:
        tag: 要部署的版本号, git tag的值.
        cpus: 需要的cpu个数, 例如1, 或者1.5, 如果是public的部署, 传0.
        memories: 最小4MB.
        replicas: app的副本数量
        app_yaml_name: AppYaml template name
        """
        payload = {
            'cluster': self.cluster,
            'tag': tag,
            'cpus': cpus,
            'memories': memories,
            'replicas': replicas,
            'app_yaml_name': app_yaml_name,
        }

        payload = {k: v for k, v in payload.items() if v is not None}
        return self.request('app/%s/canary/deploy' % appname, method='PUT', data=payload)

    def delete_app_canary(self, appname):
        payload = {
            'cluster': self.cluster,
        }
        return self.request('app/%s/canary' % appname, method='DELETE', data=payload)

    def scale_app(self, appname, cpus, memories, replicas, **kwargs):
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

    def set_app_abtesting_rules(self, appname, rules):
        """deploy app.
        cpu: 需要的cpu个数, 例如1, 或者1.5, 如果是public的部署, 传0.
        memory: 最小4MB.
        replicas: app的副本数量
        """
        payload = {
            'cluster': self.cluster,
            'rules': rules,
        }
        return self.request('app/%s/abtesting' % appname, method='PUT', json=payload)

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
            return self.request_ws('ws/job/%s/log/events' % jobname)
