#!/usr/bin/env python
# -*- coding:utf-8 -*-
import requests
import json
import copy
class SaltApi():
    """
    定义salt api接口的类
    初始化获得token
    """
    def __init__(url,self):
        self.url = url
        self.username = "saltapi"
        self.password = "saltapi"
        self.headers = {"Content-type": "application/json"}
        self.params = {'client': 'local', 'fun': None, 'tgt': None, 'arg': None}
        self.login_url = self.url + "login"
        self.login_params = {'username': self.username, 'password':
        self.password, 'eauth': 'pam'}
        self.token = self.get_data(self.login_url, self.login_params)['token']
        self.headers['X-Auth-Token'] = self.token
    
    def get_data(self, url, params):
        '''
        请求url获取数据
        :param url: 请求的url地址
        :param params: 传递给url的参数
        :return: 请求的结果
        '''
        send_data = json.dumps(params)
        request = requests.post(url, data=send_data, headers=self.headers)
        response = request.json()
        result = dict(response)
        return result['return'][0]
    
    def get_auth_keys(self):
        '''
        获取所有已经认证的key
        :return:
        '''
        data = copy.deepcopy(self.params)
        data['client'] = 'wheel'
        data['fun'] = 'key.list_all'
        result = self.get_data(self.url, data)
        try:
            return result['data']['return']['minions']
        except Exception as e:
            return str(e)
    def get_grains(self, tgt, arg='id'):
        """
        获取系统基础信息
        :tgt: 目标主机
        :return:
        """
        data = copy.deepcopy(self.params)
        if tgt:
            data['tgt'] = tgt
        else:
            data['tgt'] = '*'
            data['fun'] = 'grains.item'
            data['arg'] = arg
        result = self.get_data(self.url, data)
        return result
    def execute_command(self, tgt, fun='cmd.run', arg=None, tgt_type='list',salt_async=False):
        """
        执行saltstack 模块命令，类似于salt '*' cmd.run 'command'
        :param tgt: 目标主机
        :param fun: 模块方法 可为空
        :param arg: 传递参数 可为空
        :return: 执行结果
        """
        data = copy.deepcopy(self.params)
        if not tgt: 
            return {'status': False, 'msg': 'target host not exist'}
        if not arg:
            data.pop('arg')
        else:
            data['arg'] = arg
        if tgt != '*':
            data['tgt_type'] = tgt_type
        if salt_async: 
            data['client'] = 'local_async'
            data['fun'] = fun
            data['tgt'] = tgt
        result = self.get_data(self.url, data)
        return result
    def jobs(self, fun='detail', jid=None):
        """
        任务
        :param fun: active, detail
        :param jod: Job ID
        :return: 任务执行结果
        """
        data = {'client': 'runner'}
        data['fun'] = fun
        if fun == 'detail':
            if not jid: 
                return {'success': False, 'msg': 'job id is none'}
            data['fun'] = 'jobs.lookup_jid'
            data['jid'] = jid
        else:
            return {'success': False, 'msg': 'fun is active or detail'}
        result = self.get_data(self.url, data)
        return result
