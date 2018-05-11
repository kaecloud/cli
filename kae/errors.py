#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""

"""
from __future__ import print_function, division, absolute_import


class ConsoleAPIError(Exception):
    def __init__(self, http_code, msg):
        self.http_code = http_code
        self.msg = msg

    def __str__(self):
        return self.msg
