# !usr/bin/env python
# -*- coding:utf-8 -*-

'''
 Description: 
 Author: Lightship
 Date: 2023-02-02 21:43:26
 LastEditTime: 2023-02-05 13:43:49
'''

import hashlib
import random
import logging
from json import JSONDecodeError
from re import M
from typing import Union, Dict, List, Any
import requests
import time
import json
from urllib.parse import urlencode

from .config import gConfig

ReturnPackage = Dict[str, Any]
def resinRetrun(success:bool=False, retCode:int=-1, msg:str="", data:Dict={}) -> ReturnPackage:
    return {
        "success": success,
        "retCode": retCode,
        "msg": msg,
        "data": data
    }

def getResinData(uid) -> ReturnPackage:

    userData = gConfig["userData"]

    params = {
        'role_id': '【原神UID】',
        'server': 'cn_gf01',
    }
    cookies = {
        'account_id': '【米游社UID】',
        'cookie_token': '【抓包获取】',
    }
    
    try:
        cookies['account_id']   = userData[uid]["cookie"]["account_id"]
        cookies['cookie_token'] = userData[uid]["cookie"]["cookie_token"]
    except KeyError:
        logging.warn(uid+"尚未完成登录，未查询到cookie")
        return 

    params['role_id'] = uid
    
    return get_daily(cookies, params)


session = requests.Session()
session.trust_env = False
salt = 'xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs'

Json = Union[Dict, List, bool, str, int]
Return = Dict[str, Any]

def true_return(data: Json = None, msg: str = '成功') -> Return:
    return {
        'success': True,
        'data': data,
        'msg': msg,
    }

def false_return(msg: str = '出现错误') -> Return:
    return {
        'success': False,
        'msg': msg,
    }

def calc_ds(params) -> Return:
    t = int(time.time())
    r = random.randint(100000, 200000)
    q = urlencode(params)
    text = f'salt={salt}&t={t}&r={r}&b=&q={q}'
    md5 = hashlib.md5()
    md5.update(text.encode())
    c = md5.hexdigest()
    ds = f'{t},{r},{c}'
    return ds

def get_daily(cookies, params) -> ReturnPackage:
    ds = calc_ds(params)
    session.headers = {
        'x-rpc-client_type': '5',  # 未变
        'x-rpc-app_version': '2.28.1',
        'Host': 'api-takumi-record.mihoyo.com',
        'DS': ds,
    }
    url = 'https://api-takumi.mihoyo.com/game_record/app/genshin/api/dailyNote'
    response = session.get(url, params=params, cookies=cookies)
    try:
        response = response.json()
    except JSONDecodeError:
        return resinRetrun(False, 500, 'JSONDecodeError, response.text: ' + response.text)
    message = response['message']
    if message != 'OK':
        return resinRetrun(False, 400, 'message not OK: ' + message)

    '''
    {'current_resin': 127,
     'max_resin': 160, 
     'resin_recovery_time': '15516', 
     'finished_task_num': 0, 
     'total_task_num': 4,
     'is_extra_task_reward_received': False,
     'remain_resin_discount_num': 0, 
     'resin_discount_num_limit': 3, 
     'current_expedition_num': 5, 
     'max_expedition_num': 5, 
     'expeditions': [
        {'avatar_side_icon': 'https://upload-bbs.mihoyo.com/game_record/genshin/character_side_icon/UI_AvatarIcon_Side_Ambor.png', 'status': 'Finished', 'remained_time': '0'},
         {'avatar_side_icon': 'https://upload-bbs.mihoyo.com/game_record/genshin/character_side_icon/UI_AvatarIcon_Side_Noel.png', 'status': 'Finished', 'remained_time': '0'},
          {'avatar_side_icon': 'https://upload-bbs.mihoyo.com/game_record/genshin/character_side_icon/UI_AvatarIcon_Side_Bennett.png', 'status': 'Finished', 'remained_time': '0'},
           {'avatar_side_icon': 'https://upload-bbs.mihoyo.com/game_record/genshin/character_side_icon/UI_AvatarIcon_Side_Fischl.png', 'status': 'Finished', 'remained_time': '0'},
            {'avatar_side_icon': 'https://upload-bbs.mihoyo.com/game_record/genshin/character_side_icon/UI_AvatarIcon_Side_Keqing.png', 'status': 'Finished', 'remained_time': '0'}
            ],
    'current_home_coin': 1040, 
    'max_home_coin': 2000, 
    'home_coin_recovery_time': '130773', 
    'calendar_url': '', 
    'transformer': {
        'obtained': True, 
        'recovery_time': {
            Day': 4, 'Hour': 0, 'Minute': 0, 'Second': 0, 'reached': False
        }, 
    'wiki': 'https://bbs.mihoyo.com/ys/obc/content/1562/detail?bbs_presentation_style=no_header', 'noticed': False, 'latest_job_id': '0'}}
    '''

    # print("info:",response['data'])
    finishedCnt = 0
    maxReminTime = 0
    for v in response['data']['expeditions']:
        if v['status'] == 'Finished':
            finishedCnt += 1
        else:
            rt = int(v['remained_time'])
            if rt > maxReminTime:
                maxReminTime = rt

    return resinRetrun(True, 200, "成功", {
        'current_resin': int(response['data']['current_resin']),
        'resin_recovery_time': int(response['data']['resin_recovery_time']),
        'remain_resin_discount_num': int(response['data']['remain_resin_discount_num']),
        'current_expedition_num': int(response['data']['current_expedition_num']),
        'max_expedition_num': int(response['data']['max_expedition_num']),
        'finished_expedition_num' : finishedCnt, 
        'max_remin_time': maxReminTime,
        'current_home_coin': int(response['data']['current_home_coin']),
        'max_home_coin': int(response['data']['max_home_coin']),
        'home_coin_recovery_time': int(response['data']['home_coin_recovery_time']),
        'transformer':response['data']['transformer']
    })