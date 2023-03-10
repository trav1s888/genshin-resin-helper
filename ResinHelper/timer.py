# !usr/bin/env python
# -*- coding:utf-8 -*-

'''
 Description: Timer controller for all resin time count down thread. 
    Use muti-thread based long time sleep improve performance
 Author: Lightship
 Date: 2023-02-03 11:16:55
 LastEditTime: 2023-02-05 20:27:17
'''

import threading
import time
import math
import logging
from typing import Tuple, Dict, List, Any
from .config import gConfig, updateConfig
from .resin import getResinData
# from .utils import time_formatter, time_target, time_target_absolute, stop_thread, getInfoFromLabel
from .utils import *
from .SMTP import sendEmail

MAX_TIME_SECOND = 604800
        
def checkIfOnRemind(onRemindDict) -> bool:
    return (onRemindDict["resin_recovery_time"] |
        onRemindDict["max_remin_time"] |
        onRemindDict["home_coin_recovery_time"] |
        onRemindDict["transformer"])

'''
struct of timerDict
{
    globalLeastTargetDate   :int
    globalLeastTargetUid    :int
    globalLeastTargetName   :str
    [uid]:{
        leastTargetName     :int
        leastTargetTime     :int
        leastTargetDate     :int
        onRemind:{
            resin_recovery_time     :bool
            max_remin_time          :bool
            home_coin_recovery_time :bool
            transformer             :bool
            fetchDataFailed         :bool
        }
        'current_resin': 20,
        'resin_recovery_time': 67119
        'remain_resin_discount_num': 0
        'current_expedition_num': 5
        'max_expedition_num': 5
        'finished_expedition_num': 0
        'max_remin_time': 70363
        'current_home_coin': 0
        'max_home_coin': 2400
        'home_coin_recovery_time': 286323
        'transformer': {
            'obtained': True
            'recovery_time': {
                'Day': 0
                'Hour': 0
                'Minute': 0
                'Second': 0
                'reached': True
            }
            'wiki': 'https://bbs.mihoyo.com/ys/obc/content/1562/detail?bbs_presentation_style=no_header'
            'noticed': False
            'latest_job_id': '0'
        }
    }
    ...
}

'''

class TimerController():
    def __init__(self):
        self.timerDict = {}
        self.timerDictLock = threading.Lock()
        self.__resinDataInit() #init resin data dict
        self.counterThread = threading.Thread(target = TimerController.__counter, args=(self,))
        self.counterThread.setDaemon(True)
        self.counterThread.start()

    def __resinDataInit(self):
        '''Counter first start-up, update all account's resin data
            time delay of first is second level, Receivabiltiy!'''
        # least time slice of all account
        leastTimeAccount = [math.ceil(time.time())+MAX_TIME_SECOND, -1, "---"]
        for uid in gConfig["userData"].keys():
            #??????????????????????????????????????????
            # resinData = {'success': True, 'data': {'current_resin': 20, 'resin_recovery_time': 67119, 'remain_resin_discount_num': 0, 'current_expedition_num': 5, 'max_expedition_num': 5, 'finished_expedition_num': 0, 'max_remin_time': 70363, 'current_home_coin': 0, 'max_home_coin': 2400, 'home_coin_recovery_time': 286323, 'transformer': {
            #     'obtained': True, 'recovery_time': {'Day': 0, 'Hour': 0, 'Minute': 0, 'Second': 0, 'reached': True}, 'wiki': 'https://bbs.mihoyo.com/ys/obc/content/1562/detail?bbs_presentation_style=no_header', 'noticed': False, 'latest_job_id': '0'}}, 'msg': '??????'} 
            resinData = getResinData(uid)
            resinData["data"].update({
                    "onRemind": {
                    "resin_recovery_time"       :False,
                    "max_remin_time"            :False,
                    "home_coin_recovery_time"   :False,
                    "transformer"               :False,
                    "fetchDataFailed"           :False
                }
            })

            self.TimerDictAccountResinDataUpdate(resinData, uid, True)
            
            #global least time count
            if (self.timerDict[uid]["leastTargetDate"] < leastTimeAccount[0]):
                leastTimeAccount = [self.timerDict[uid]["leastTargetDate"], uid, self.timerDict[uid]["leastTargetName"]]
        #acquire lock
        self.timerDictLock.acquire()
        self.timerDict["globalLeastTargetDate"] = leastTimeAccount[0]
        self.timerDict["globalLeastTargetUid"] = leastTimeAccount[1]
        self.timerDict["globalLeastTargetName"] = leastTimeAccount[2]
        #release lock
        self.timerDictLock.release()
    
    def __timeDictGlobalUpdate(self):
        leastTimeAccount = [math.ceil(time.time())+MAX_TIME_SECOND, -1, "---"]
        for uid in gConfig["userData"].keys():
            if (self.timerDict[uid]["leastTargetDate"] < leastTimeAccount[0]):
                leastTimeAccount = [self.timerDict[uid]["leastTargetDate"], uid, self.timerDict[uid]["leastTargetName"]]
        #acquire lock
        self.timerDictLock.acquire()
        self.timerDict["globalLeastTargetDate"] = leastTimeAccount[0]
        self.timerDict["globalLeastTargetUid"] = leastTimeAccount[1]
        self.timerDict["globalLeastTargetName"] = leastTimeAccount[2]
        #release lock
        self.timerDictLock.release()

    def TimerDictAccountResinDataUpdate(self, resinData, uid, isInit):
        if(not resinData["success"]):
            if (isInit or not self.timerDict[uid]["onRemind"]["fetchDataFailed"]):
                logging.warn("?????? "+uid+" ????????????????????????????????????????????????????????????????????????????????????????????????")
                #email remind
                sendEmail("??????????????????", "\t?????? "+uid+" ?????????????????????????????????????????????????????????????????????????????????????????????\
                            ???????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????\n\
                        \t?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????API??????????????????\
                        ", gConfig["userData"][uid]["email"])
            elif not isInit:
                self.timerDict[uid]["onRemind"]["fetchDataFailed"] = True
                logging.warn("?????? "+uid+" ????????????????????????????????????????????????????????????????????????????????????????????????")
        else:
            logging.info("?????? "+uid+" ?????????????????????")
        #acquire lock
        self.timerDictLock.acquire()
        if not isInit:
            self.timerDict[uid]["onRemind"]["fetchDataFailed"] = False
            resinData["data"].update({
                "onRemind": self.timerDict[uid]["onRemind"]
            })
        self.timerDict.update({
            uid: resinData["data"]
            })
        leastTarget = self.__getAccountLeast(uid, resinData["data"])
        self.timerDict[uid].update({
            "leastTargetName": leastTarget[0],
            "leastTargetTime": leastTarget[1],
            "leastTargetDate": math.ceil(time.time())+leastTarget[1]
        })
        #release lock
        self.timerDictLock.release()
        logging.debug("--> ??????????????????: "+leastTarget[0]+", ????????????: "+time_target_absolute(self.timerDict[uid]["leastTargetDate"]))        
        return resinData["success"]

    def __counter(self):
        targetDate = self.timerDict["globalLeastTargetDate"]
        targetUid = self.timerDict["globalLeastTargetUid"]
        targetName = self.timerDict["globalLeastTargetName"]
        while True:
            nowTime = time.time() #avoid negative sleep caused by innner while
            while(targetDate <= nowTime):
                logging.info("?????? "+targetUid+" ????????????, ??????: "+targetName+", ???????????????...")
                #update timerDict account resin data and CHECK IF CAN SEND EMAIL!
                resinData = getResinData(targetUid)
                # if fetch data failed, func inner will control to sendEmail and set MAX_SECOND, just update and continue
                if (not self.TimerDictAccountResinDataUpdate(resinData, targetUid, False)):
                    #update global target
                    self.__timeDictGlobalUpdate()
                    nowTime = time.time()
                    targetDate = self.timerDict["globalLeastTargetDate"]
                    targetUid = self.timerDict["globalLeastTargetUid"]
                    targetName = self.timerDict["globalLeastTargetName"]
                    continue
                #update global target
                self.__timeDictGlobalUpdate()
                if (targetName == "onRemind"):
                    logging.info("?????? "+targetUid+" ????????????")
                else:
                    if (self.timerDict["globalLeastTargetUid"] == targetUid and
                        self.timerDict["globalLeastTargetName"] == targetName and
                        abs(self.timerDict["globalLeastTargetDate"] - nowTime) < 10):
                        '''Send Email'''
                        logging.info("?????? "+targetUid+" ???????????????...")
                        emailPackage = self.generateEmailInfo(targetName, targetUid)
                        sendEmail(emailPackage[0], emailPackage[1], gConfig["userData"][targetUid]["email"])
                        logging.info("?????? "+targetUid+" ????????????????????????")
                        self.timerDict[targetUid]["onRemind"][targetName] = True
                        #update now data after onRemind is True
                        self.TimerDictAccountResinDataUpdate(resinData, targetUid, False)
                        self.__timeDictGlobalUpdate()
                    else:
                        logging.info("?????? "+targetUid+" ????????????????????????????????????")
                nowTime = time.time()
                targetDate = self.timerDict["globalLeastTargetDate"]
                targetUid = self.timerDict["globalLeastTargetUid"]
                targetName = self.timerDict["globalLeastTargetName"]
            #no instant target, into sleep
            logging.info("??????????????????: "+str(targetUid)+", ????????????: "\
                +getInfoFromLabel(targetName)[1]+", ????????????: "+time_target_absolute(targetDate))
            print(">")
            time.sleep(targetDate-nowTime)

    def __restartTimer(self):
        stop_thread(self.counterThread)
        self.__timeDictGlobalUpdate()
        self.counterThread = threading.Thread(target = TimerController.__counter, args=(self,))
        self.counterThread.setDaemon(True)
        self.counterThread.start()

    def RestartTimerAndUserConfig(self,uid)->bool:
        stop_thread(self.counterThread)
        if uid not in self.timerDict:
            return False
        updateConfig()
        self.TimerDictAccountResinDataUpdate(getResinData(uid), uid, False)
        self.__restartTimer()
        return True

    # generate email info by targetName and uid, return subject and message
    def generateEmailInfo(self, targetName, uid) -> Tuple[str, str]:
        labelInfo = getInfoFromLabel(targetName)
        subject = labelInfo[1]
        if (labelInfo[0] == 0):
            subject += "??????????????? "+str(self.timerDict[uid]["current_resin"])
        elif (labelInfo[0] == 2):
            subject += "??????????????? "+str(self.timerDict[uid]["current_home_coin"])

        userSettings = gConfig["userData"][uid]["setting"]
        message = f'''\
        ???????????????????  {self.timerDict[uid]["current_resin"]}/160\
        \n???????????????????  {time_formatter(self.timerDict[uid]['resin_recovery_time'])}\
        \n???????????????????  {time_target(self.timerDict[uid]['resin_recovery_time'])}\
        \n?????????{"????????????"+str(userSettings["resinRemindThreshold"]) if userSettings["resinRemindOn"] else "???"}\
        \n-------------------------------------\
        \n???????????????????  ????????? {self.timerDict[uid]['finished_expedition_num']}/{self.timerDict[uid]['current_expedition_num']}\
        \n????????????{'???' if self.timerDict[uid]['max_remin_time'] == 0 else '???'}:   {time_formatter(self.timerDict[uid]['max_remin_time'])}\
        \n???????????????????  {time_target(self.timerDict[uid]['max_remin_time'])}\
        \n?????????{"???" if userSettings["expeditionRemindOn"] else "???"}\
        \n-------------------------------------\
        \n???????????????????  {self.timerDict[uid]['current_home_coin']}/{self.timerDict[uid]['max_home_coin']}\
        \n???????????????????  {time_formatter(self.timerDict[uid]['home_coin_recovery_time'])}\
        \n???????????????????  {time_target(self.timerDict[uid]['home_coin_recovery_time'])}\
        \n?????????{"????????????"+str(userSettings["homeRemindThreshold"]) if userSettings["coinRemindOn"] else "???"}\
        \n-------------------------------------\
        \n?????????????????????????    {self.timerDict[uid]['remain_resin_discount_num']}???\
        \n-------------------------------------
        '''.strip()

        if (self.timerDict[uid]['transformer']["obtained"]):
            recvTimeDict = self.timerDict[uid]["transformer"]["recovery_time"]
            D,H,M,S,R = recvTimeDict["Day"], recvTimeDict["Hour"], recvTimeDict["Minute"],recvTimeDict["Second"],recvTimeDict["reached"]
            targetTimeCount = 0 if R else ((D*24+H)*60+M)*60+S
            message += "\n"+f'''\
            ?????????{'???' if recvTimeDict["reached"] else '???'}??????\
            \n????????????{'???' if recvTimeDict["reached"] else '???'}:   {time_formatter(targetTimeCount)}\
            \n???????????????????  {time_target(targetTimeCount)}\
            \n?????????{"???" if userSettings["transformerRemindOn"] else "???"}\
            '''.strip()
        else:
            message += "\n??????????????????"

        return (subject, message)

    # gain least seconds from Account Data Dict
    def __getAccountLeast(self, uid ,innerAccountTimes) -> Tuple[str,int]:
        least = MAX_TIME_SECOND
        key = "onRemind"
        # ?????????????????????????????????????????????????????????????????????????????????????????????
        cmpList = ("resin_recovery_time", "max_remin_time","home_coin_recovery_time", "transformer")
        setList = ("resinRemindOn", "expeditionRemindOn","coinRemindOn", "transformerRemindOn")
        userSettings = gConfig["userData"][uid]["setting"]
        for i in range(len(cmpList)):
            try:
                # switch off
                if (not userSettings[setList[i]]):
                    self.timerDict[uid]["onRemind"][cmpList[i]] = False
                    continue
                # switch on
                targetTimeCount = innerAccountTimes[cmpList[i]]
                if (i == 0): #resin
                    targetTimeCount -= 480 * (160 - userSettings["resinRemindThreshold"])
                    if (self.timerDict[uid]["onRemind"][cmpList[i]]):
                        if (targetTimeCount > 0): # user already update resin data, can email now
                            self.timerDict[uid]["onRemind"][cmpList[i]] = False
                            logging.debug("--> ???????????????????????????????????????: "+time_formatter(targetTimeCount))
                        else: # cannot email
                            targetTimeCount = MAX_TIME_SECOND
                            logging.debug("--> ??????????????????????????????????????????30min")
                    else:
                        # can email
                        targetTimeCount = 0 if targetTimeCount < 0 else targetTimeCount
                        logging.debug("--> ????????????????????????: "+time_formatter(targetTimeCount))
                elif (i == 1): #expedition
                    if (innerAccountTimes["current_expedition_num"] == 0): continue
                    if (self.timerDict[uid]["onRemind"][cmpList[i]]):
                        if (targetTimeCount > 0): # user already update data, can email now
                            self.timerDict[uid]["onRemind"][cmpList[i]] = False
                            logging.debug("--> ?????????????????????????????????????????????: "+time_formatter(targetTimeCount))
                        else:
                            targetTimeCount = MAX_TIME_SECOND
                            logging.debug("--> ????????????????????????????????????????????????30min")
                    else:
                        logging.debug("--> ??????????????????????????????: "+time_formatter(targetTimeCount))
                elif (i == 2): #homecoin
                    M,C,Tp =  innerAccountTimes["max_home_coin"], innerAccountTimes["current_home_coin"], userSettings["homeRemindThreshold"]
                    if (C >= Tp*M):
                        targetTimeCount = 0
                    else:
                        targetTimeCount *= math.ceil(M*(1-Tp)/(M-C))
                    if (self.timerDict[uid]["onRemind"][cmpList[i]]):
                        if (targetTimeCount > 0): # user already update data, can email now
                            self.timerDict[uid]["onRemind"][cmpList[i]] = False
                            logging.debug("--> ???????????????????????????????????????: "+time_formatter(targetTimeCount))
                        else:
                            targetTimeCount = MAX_TIME_SECOND
                            logging.debug("--> ??????????????????????????????????????????30min")
                    else:
                        logging.debug("--> ????????????????????????: "+time_formatter(targetTimeCount))
                elif (i==3): #?????????
                    if (not innerAccountTimes[cmpList[i]]["obtained"]): continue
                    recvTimeDict = innerAccountTimes[cmpList[i]]["recovery_time"]
                    D,H,M,S,R = recvTimeDict["Day"], recvTimeDict["Hour"], recvTimeDict["Minute"],recvTimeDict["Second"],recvTimeDict["reached"]
                    targetTimeCount = 0 if R else ((D*24+H)*60+M)*60+S
                    if (self.timerDict[uid]["onRemind"][cmpList[i]]):
                        if (targetTimeCount > 0): # user already update data, can email now
                            self.timerDict[uid]["onRemind"][cmpList[i]] = False
                            logging.debug("--> ??????????????????????????????????????????: "+time_formatter(targetTimeCount))
                        else:
                            targetTimeCount = MAX_TIME_SECOND
                            logging.debug("--> ?????????????????????????????????????????????30min")
                    else:
                        logging.debug("--> ?????????????????????: "+time_formatter(targetTimeCount))
                if (targetTimeCount < least):
                    key = cmpList[i]
                    least = targetTimeCount
            except KeyError:
                continue
        if (least > 1799 and checkIfOnRemind(self.timerDict[uid]["onRemind"])):
            key = "onRemind"
            least = 1799
        return (key, least + 1) # Add 1 to avoid double timeout in two seconds


