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
qr_generate_code_uuid = "https://login.dingtalk.com/user/qrcode/generate.jsonp?callback=angular.callbacks._0"
app_key ='85A09F60A599F5E1867EAB915A8BB07F'

#"wss://webalfa.dingtalk.com",
#"wss://webalfa-cm3.dingtalk.com",
#"wss://webalfa-cm10.dingtalk.com"

SUCCESS = ''
WAIT_LOGIN = '11021'
SUCCESS = ''
TIMEOUT = ''
SCANED=''

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

def loads_jsonp(_jsonp):
    try:
        return json.loads(re.match(".*?({.*}).*",_jsonp,re.S).group(1))
    except:
	    raise ValueError('Invalid Input')

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

class DingBot:

    def __init__(self):
        self.num = 0 # callback 计数器,plus +1
        self.DEBUG = False
        self.conf = {'qr': 'png'}
        self.code_uuid = ''
        self.app_key = app_key
        self.session = SafeSession()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36'})
        self.my_account = {}  # 当前账户
        self.temp_pwd = os.path.join(os.getcwd(), 'temp')
        if os.path.exists(self.temp_pwd) == False:
            os.mkdir(self.temp_pwd)

        self.my_account = {}


    def get_code_uuid(self):
        r = self.session.get(qr_generate_code_uuid)
        r.encoding = 'utf-8'
        data = r.text
        dic = loads_jsonp(r.text)
        if dic['success']:
            self.code_uuid= dic['result']
            return dic['success']
        return False

    def gen_qr_code(self, qr_file_path):
        string = qr_url % self.code_uuid
        print(string)
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
            self.gen_qr_code(os.path.join(self.temp_pwd,'dingtalkqr.png'))
            print '[INFO] Please use DingTalk to scan the QR code .'
            self.wait4login()
        except Exception as e:
            print e

    def do_request(self,url):
        r = self.session.get(url)
        r.encoding='utf-8'
        data = r.text
        result = loads_jsonp(data);
        if result.get('success'):
            return result.get('success'), 200, result['result']

        return result['success'], result['errorCode'], result['errorMsg']

    def wait4login(self):
        login_check_url = 'https://login.dingtalk.com/user/qrcode/is_logged.jsonp?appKey=%s&callback=angular.callbacks._43' \
              '&pdmModel=Unknown+&pdmTitle=Unknown++Web&pdmToken=%s&qrcode=%s'

        try_later_secs = 5
        MAX_RETRY_TIMES = 34

        retry_time = MAX_RETRY_TIMES

        #5秒一次，1,2,3,4...a,b,c,d... x,y

        while retry_time > 0:
            url = login_check_url % (app_key, '', self.code_uuid)

            success, code, result = self.do_request(url)
            if success:
                print '[INFO] %s' % result
                self.my_account = result;
                break;
            elif code == WAIT_LOGIN :
                print '[ERROR] %s' % result
                retry_time -= 1
                time.sleep(try_later_secs)
            else:
                print '[ERROR] %s' % result
                retry_time -= 1
                time.sleep(try_later_secs)




    def handle_msg_all(self, msg):
        pass

if __name__ == '__main__':

    DingBot().run();