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
import websocket
from threading import Timer
import math

qr_url = "http://qr.dingtalk.com/action/login?code=%s"
qr_generate_code_uuid = "https://login.dingtalk.com/user/qrcode/generate.jsonp?callback=angular.callbacks._0"
app_key = '85A09F60A599F5E1867EAB915A8BB07F'
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36'
# "wss://webalfa.dingtalk.com",
# "wss://webalfa-cm3.dingtalk.com",
# "wss://webalfa-cm10.dingtalk.com"

SUCCESS = ''
WAIT_LOGIN = '11021'
SUCCESS = ''
TIMEOUT = ''
SCANED = ''


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
        webbrowser.open(os.path.join(os.getcwd(), 'temp', file_path))


def loads_jsonp(_jsonp):
    try:
        return json.loads(re.match(".*?({.*}).*", _jsonp, re.S).group(1))
    except:
        raise ValueError('Invalid Input')


def task(func, interval, delay):
    start = time.time()
    if delay != 0:
        time.sleep(delay)
    func()
    end = time.time()
    if start + interval > end:
        Timer(start + interval - end, task, (func, interval, 0)).start()
    else:
        times = round((end - start) / interval)  # times >= 1
        Timer(start + (times + 1) * interval - end, task, (func, interval, 0)).start()


def schedule(func, interval, delay=0):
    Timer(interval, task, (func, interval, delay)).start()


id = 0
DIGITS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "a", "b", "c", "d", "e", "f"]


def genMid():
    global id
    I = int(math.floor(random.random() * math.pow(2, 16)))
    D = id
    id += 1
    G = ""
    G += DIGITS[I >> 12 & 15]
    G += DIGITS[I >> 8 & 15]
    G += DIGITS[I >> 4 & 15]
    G += DIGITS[15 & I]
    G += DIGITS[D >> 12 & 15]
    G += DIGITS[D >> 8 & 15]
    G += DIGITS[D >> 4 & 15]
    G += DIGITS[15 & D]
    return G


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

        # 重试3次以后再加一次，抛出异常
        try:
            return super(SafeSession, self).request(method, url, params, data, headers, cookies, files, auth,
                                                    timeout,
                                                    allow_redirects, proxies, hooks, stream, verify, cert, json)
        except Exception as e:
            raise e


class DingBot:

    def __init__(self):
        self.num = 0  # callback 计数器,plus +1
        self.DEBUG = False
        self.conf = {'qr': 'png'}
        self.code_uuid = ''
        self.app_key = app_key
        self.session = SafeSession()
        self.session.headers.update({'User-Agent': user_agent})
        self.my_account = {}  # 当前账户
        self.temp_pwd = os.path.join(os.getcwd(), 'temp')
        if os.path.exists(self.temp_pwd) is False:
            os.mkdir(self.temp_pwd)

        self.my_account = {}
        self.ws_url = 'wss://webalfa-cm3.dingtalk.com/long'
        self.tmp_code = ''
        self.access_token = ''
        self.cookie = '';
        self.header = []
        # header.append('Accept-Encoding:gzip, deflate, sdch')
        # header.append('Host:webalfa.dingtalk.com')
        self.header.append('Origin:https://im.dingtalk.com')
        # header.append('Sec-WebSocket-Extensions:permessage-deflate; client_max_window_bits')
        self.header.append('Sec-WebSocket-Key:xpuOh/qlI/zsyeARsnZvfQ==')
        self.header.append('Sec-WebSocket-Version:13')
        self.header.append('User-Agent:' + user_agent)

        # self.write_to_json('OrgRelations', '')

    def on_message(self, ws, message):
        data = json.loads(message)
        print "get ws message %s" % data

    def on_error(self, ws, error):
        print error

    def on_close(self, ws):
        print "### closed ###"

    def on_open(self, ws):
        self.send(
            '{"lwp":"/reg","headers":{"cache-header":"token app-key did ua vhost wv","vhost":"WK","ua":"' + user_agent + '","app-key":"' + self.app_key + '","mid":"' + genMid() + ' 0","wv"："im:3,au:3,sy:4"},"body":null}')
        # self.send('{"lwp":"/r/Adaptor/LoginI/umidToken","headers":{"mid":"50230000 0"},"body":[]}')
        self.send(
            '{"lwp":"/subscribe","headers":{"set-ver:116725541521","token":"' + self.access_token + '","sync":"0,0;0;0;","mid":"1ea00001 0"}}')
        # self.getOrgRelations()

    def ping(self):
        def func():
            self.ws.send('{"lwp":"/!","headers":{"mid":"' + genMid() + ' 0"},"body":null}')

        schedule(func, 15, delay=0)

    def send(self, str):
        print 'send message : %s' % str
        self.ws.send(str)

    def get_code_uuid(self):
        r = self.session.get(qr_generate_code_uuid)
        r.encoding = 'utf-8'
        data = r.text
        dic = loads_jsonp(r.text)
        print "[INFO]获取code:%s" % str(dic)
        if dic['success']:
            self.code_uuid = dic['result']
            return dic['success']
        print "[ERROR] 获取code失败"
        return False

    def gen_qr_code(self, qr_file_path):
        string = qr_url % self.code_uuid
        # print "[INFO]生成二维码 %s" % string
        qr = pyqrcode.create(string)
        if self.conf['qr'] == 'png':
            qr.png(qr_file_path, scale=8)
            show_image(qr_file_path)
        elif self.conf['qr'] == 'tty':
            print(qr.terminal(quiet_zone=1))

    def run(self):
        try:
            self.get_code_uuid()
            self.gen_qr_code(os.path.join(self.temp_pwd, 'dingtalkqr.png'))
            print '[INFO] Please use DingTalk to scan the QR code .'
            self.wait4login()
            self.setCookie()
            self.setStaticCookie()
            self.header.append("cookie:" + self.cookie)
            print self.header
            self.ws = websocket.WebSocketApp(self.ws_url, on_message=self.on_message, on_error=self.on_error,
                                             on_close=self.on_close, header=self.header)
            self.ws.on_open = self.on_open
            self.ws.run_forever()
            self.ping()

        except Exception as e:
            print e

    def do_request(self, url):
        r = self.session.get(url)
        r.encoding = 'utf-8'
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

        # 5秒一次，1,2,3,4...a,b,c,d... x,y

        while retry_time > 0:
            url = login_check_url % (app_key, '', self.code_uuid)

            success, code, result = self.do_request(url)
            if success:
                print '[INFO] 返回结果 %s' % result
                self.my_account = result;
                self.tmp_code = self.my_account['tmpCode']
                # 获取accessToken，用于websocket订阅
                self.access_token = self.my_account['accessToken']
                for c in self.session.cookies:
                    self.cookie += c.name + ":" + c.value + ";"

                #self.cookie += "token:" + self.access_token + ";"
                break;
            elif code == WAIT_LOGIN:
                print '[ERROR] %s' % result
                retry_time -= 1
                time.sleep(try_later_secs)
            else:
                print '[ERROR] %s' % result
                retry_time -= 1
                time.sleep(try_later_secs)

    def setCookie(self):

        url = 'https://webalfa-cm3.dingtalk.com/setCookie?code=%s&appkey=%s&isSession=true&callback=__jp0' % (
            self.tmp_code, self.app_key)
        r = self.session.get(url)
        data = r.text
        print "[INFO] set cookie %s" % data

        result = loads_jsonp(data);
        if result['code'] != 200:
            print "error %s " % result

        self.deviceid = self.session.cookies['deviceid']
        self.deviceid_exist = self.session.cookies['deviceid_exist']
        for c in self.session.cookies:
            self.cookie += c.name + ":" + c.value + ";"
        print(self.cookie)
    def setStaticCookie(self):
        url = "https://static.dingtalk.com/media/setCookie?code=ggHaACQ3YTcxYzkzZS05NGFmLTQ5NTYtYjcxMy02ZTMyODA3MzI4MjACsTY3MzMzNTI2QGRpbmdkaW5n&callback=__jp0"
        r = self.session.get(url)
        data = r.text
        print "[INFO] set static cookie %s" % data

        result = loads_jsonp(data);
        if result['code'] != 200:
            print "set static cookie error %s " % result

        for c in self.session.cookies:
            self.cookie += c.name + ":" + c.value + ";"



    def handle_msg_all(self, msg):
        pass


if __name__ == '__main__':
    DingBot().run();
