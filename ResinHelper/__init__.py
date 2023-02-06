# !usr/bin/env python
# -*- coding:utf-8 -*-

'''
 Description: RH package
 Author: Lightship
 Date: 2023-02-02 20:46:54
 LastEditTime: 2023-02-05 14:39:43
'''
import logging

#logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.INFO,
format = '[%(levelname)s]\t%(asctime)s: %(message)s')


from .config import gConfig
from .resin import getResinData
from .timer import TimerController
from .SMTP import sendEmail

