# !usr/bin/env python
# -*- coding:utf-8 -*-

'''
 Description: email module
 Author: Lightship
 Date: 2023-02-02 20:08:10
 LastEditTime: 2023-02-05 13:27:49
'''
# -*- coding: utf-8 -*-
from smtplib import SMTP
from email.header import Header
from email.mime.text import MIMEText
from .config import gConfig


class notificationList():
    def __init__(self):
        self.targetList = []
    def add(self, app):
        self.targetList.append(app)

headers={
   'Connection': 'keep-alive',
   'Accept-Encoding': 'gzip, deflate',
   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.72 Safari/537.36',
   'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6'
}

def sendEmail(subject, mess, receiver):
    message = MIMEText(mess, 'plain', 'utf-8')
    message['From'] = Header('树脂助手', 'utf-8')
    message['To'] = Header('客户端', 'utf-8')
    message['Subject'] = Header('树脂助手: '+subject, 'utf-8')
    
    smtper = SMTP('smtp.qq.com', 587) #阿里云465端口无响应，使用587端口
    smtper.login(gConfig["sender"], gConfig["passwd"])
    smtper.sendmail(gConfig["sender"], receiver, message.as_string())
    smtper.quit()
    return True
