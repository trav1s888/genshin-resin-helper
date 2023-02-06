# !usr/bin/env python
# -*- coding:utf-8 -*-

'''
 Description: utils
 Author: Lightship
 Date: 2023-02-03 15:10:42
 LastEditTime: 2023-02-05 21:48:26
'''
import time
import inspect
import ctypes
import tenacity
import uuid
from typing import Tuple

MAX_RETRY_TIMES = 5

# Time format
def time_formatter(t:int)->str:
    return f"{t//3600}小时{(t%3600)//60}分钟{t%60}秒"

# Calculate the target end time
def time_target(t:int)->str:
    tartime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()+t))
    return tartime

# Format absolute time
def time_target_absolute(t:int)->str:
    tartime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))
    return tartime


def _async_raise(tid, exctype):
  """raises the exception, performs cleanup if needed"""
  tid = ctypes.c_long(tid)
  if not inspect.isclass(exctype):
    exctype = type(exctype)
  res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
  if res == 0:
    raise ValueError("invalid thread id")
  elif res != 1:
    # """if it returns a number greater than one, you're in trouble,
    # and you should call it again with exc=NULL to revert the effect"""
    ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
    raise SystemError("PyThreadState_SetAsyncExc failed")
    
def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)

LabelDict = {
  "resin_recovery_time": (0, "树脂已达阈值"),
  "max_remin_time": (1, "探索派遣全部完成"),
  "home_coin_recovery_time": (2, "洞天宝钱已达阈值"),
  "transformer": (3, "质变仪已就绪"),
  "onRemind": (4,"轮询中")
}
def getInfoFromLabel(label:str) -> Tuple[int, str]:
  return LabelDict.get(label)

def generateDeviceID() -> str:
  """random x-rpc-device_id"""
  return str(uuid.uuid4()).upper()

def custom_attempt_times(retry: bool):
    """
    自定义的重试机制停止条件\n
    根据是否要重试的bool值，给出相应的`tenacity.stop_after_attempt`对象
    >>> retry == True #重试次数达到配置中 MAX_RETRY_TIMES 时停止
    >>> retry == False #执行次数达到1时停止，即不进行重试
    """
    if retry:
        return tenacity.stop_after_attempt(MAX_RETRY_TIMES + 1)
    else:
        return tenacity.stop_after_attempt(1)
