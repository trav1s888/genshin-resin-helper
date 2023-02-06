# !usr/bin/env python
# -*- coding:utf-8 -*-

'''
 Description: MainPy
 Author: Lightship
 Date: 2023-02-02 20:16:58
 LastEditTime: 2023-02-05 14:04:14
'''

import logging
import threading

from ResinHelper import *

exitFlag = False
def resetExitFlag():
    global exitFlag
    exitFlag = False

if __name__ == '__main__':
    # logging.debug(gConfig)
    # print(getResinData("119066247"))
    
    # Init and start Timer, fetch all account's resin data save to gConfig
    TC = TimerController()

    import time
    logging.info("初始化完毕，自动提醒已开启!")
    exitTimer = threading.Timer(1, resetExitFlag)
    while True:
        try:
            cmd = input(">")
            if (cmd == "help"):
                print("""\
                    这里是帮助
                """.strip())
            elif (cmd == "reset"):
                logging.info("重载配置")
                TC.RestartTimerAndUserConfig("119066247")
            # TC.RestartTimer()
        except KeyboardInterrupt:
                try:
                    logging.info("2s内再次ctrl+c退出程序")
                    time.sleep(2)
                except KeyboardInterrupt:
                    exit(0)