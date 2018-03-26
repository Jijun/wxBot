#!/usr/bin/env python
# coding: utf-8

import os
import sys
import traceback
import webbrowser
import pyqrcode
import requests
import mimetypes
import json
import xml.dom.minidom
import urllib
import time
import re
import random
from traceback import format_exc
from requests.exceptions import ConnectionError, ReadTimeout
import HTMLParser

qr_url = "http://qr.dingtalk.com/action/login?code=%s"
qr_generate_code_uuid = "https://login.dingtalk.com/user/qrcode/generate.json"


def show_image(file_path):
    """
    跨平台显示图片文件
    :param file_path: 图片文件路径
    """
    if sys.version_info >= (3, 3):
        from shlex import quote
    else:
        from pipes import quote

    if sys.platform == "darwin":
        command = "open -a /Applications/Preview.app %s&" % quote(file_path)
        os.system(command)
    else:
        webbrowser.open(os.path.join(os.getcwd(),'temp',file_path))


class SafeSession(requests.Session):
    def request(self, method, url, params=None, data=None, headers=None, cookies=None, files=None, auth=None,
                timeout=None, allow_redirects=True, proxies=None, hooks=None, stream=None, verify=None, cert=None,
                json=None):
        for i in range(3):
            try:
                return super(SafeSession, self).request(method, url, params, data, headers, cookies, files, auth,
                                                        timeout,
                                                        allow_redirects, proxies, hooks, stream, verify, cert, json)
            except Exception as e:
                print e.message, traceback.format_exc()
                continue

        #重试3次以后再加一次，抛出异常
        try:
            return super(SafeSession, self).request(method, url, params, data, headers, cookies, files, auth,
                                                    timeout,
                                                    allow_redirects, proxies, hooks, stream, verify, cert, json)
        except Exception as e:
            raise e

class DingBot(object):

    def __init__(self):
        self.DEBUG = False
        self.conf = {'qr': 'png'}
        self.code_uuid = ''

    def get_code_uuid(self):
        r = self.session.get(qr_generate_code_uuid)
        r.encoding = 'utf-8'
        data = r.text
        dic = json.load(r.text)
        if dic['success']:
            return dic['result']

    def gen_qr_code(self, qr_file_path):
        string = qr_url % self.code_uuid
        qr = pyqrcode.create(string)
        if self.conf['qr'] == 'png':
            qr.png(qr_file_path, scale=8)
            show_image(qr_file_path)
            # img = Image.open(qr_file_path)
            # img.show()
        elif self.conf['qr'] == 'tty':
            print(qr.terminal(quiet_zone=1))

    def run(self):
        try:
            self.get_code_uuid()
            self.gen_qr_code(os.path.join(self.temp_pwd,'wxqr.png'))
            print '[INFO] Please use DingTalk to scan the QR code .'
        except Exception,e:
            pass

    def handle_msg_all(self, msg):
        pass