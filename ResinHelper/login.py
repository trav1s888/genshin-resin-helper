"""
### 米游社登录获取Cookie相关
"""
import traceback
from typing import List, Union

import httpx
import requests.utils
import tenacity
import logging
from utils import *

from .config import gConfig

SLEEP_TIME_RETRY: float = 3
TIME_OUT: Union[float, None] = None

URL_1 = "https://webapi.account.mihoyo.com/Api/login_by_mobilecaptcha"
URL_2 = "https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket?login_ticket={0}&token_types=3&uid={1}"
URL_3 = "https://api-takumi.mihoyo.com/account/auth/api/webLoginByMobile"
HEADERS_1 = {
    "Host": "webapi.account.mihoyo.com",
    "Connection": "keep-alive",
    "sec-ch-ua": gConfig["device"]["UA"],
    "DNT": "1",
    "x-rpc-device_model": gConfig["device"]["X_RPC_DEVICE_MODEL_PC"],
    "sec-ch-ua-mobile": "?0",
    "User-Agent": gConfig["device"]["USER_AGENT_PC"],
    "x-rpc-device_id": None,
    "Accept": "application/json, text/plain, */*",
    "x-rpc-device_name": gConfig["device"]["X_RPC_DEVICE_NAME_PC"],
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "x-rpc-client_type": "4",
    "sec-ch-ua-platform": gConfig["device"]["UA_PLATFORM"],
    "Origin": "https://user.mihoyo.com",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://user.mihoyo.com/",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"
}
HEADERS_2 = {
    "Host": "api-takumi.mihoyo.com",
    "Content-Type": "application/json;charset=utf-8",
    "Origin": "https://bbs.mihoyo.com",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": gConfig["device"]["USER_AGENT_PC"],
    "Referer": "https://bbs.mihoyo.com/",
    "Accept-Language": "zh-CN,zh-Hans;q=0.9"
}


class GetCookie:
    """
    获取Cookie(需先初始化对象)
    """

    def __init__(self, phone) -> None:
        self.phone = phone
        self.bbsUID: str = None
        self.cookie: dict = None
        '''获取到的Cookie数据'''
        self.client = httpx.AsyncClient()
        for uid in gConfig["userData"].keys():
            if gConfig["userData"][uid]["phone"] == phone:
                self.deviceId = gConfig["userData"][uid]
                return
        self.deviceId = generateDeviceID()
        
            

    async def get_1(self, captcha: str, retry: bool = True) -> List[1, -1, -2, -3, -4]:
        """
        第一次获取Cookie(目标是login_ticket)

        参数:
            `captcha`: 短信验证码
            `retry`: 是否允许重试

        - 若返回 `1` 说明已成功
        - 若返回 `-1` 说明Cookie缺少`login_ticket`
        - 若返回 `-2` 说明Cookie缺少米游社UID(bbsUID)，如`stuid`
        - 若返回 `-3` 说明请求失败
        - 若返回 `-4` 说明验证码错误
        """
        headers = HEADERS_1.copy()
        headers["x-rpc-device_id"] = self.deviceID
        res = None
        try:
            async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), wait=tenacity.wait_fixed(SLEEP_TIME_RETRY)):
                with attempt:
                    res = await self.client.post(URL_1, headers=headers, data="mobile={0}&mobile_captcha={1}&source=user.mihoyo.com".format(self.phone, captcha), timeout=TIME_OUT)
                    try:
                        res_json = res.json()
                        if res_json["data"]["msg"] == "验证码错误" or res_json["data"]["info"] == "Captcha not match Err":
                            logging.info("登录米哈游账号 - 验证码错误")
                            return -4
                    except:
                        pass
                    if "login_ticket" not in res.cookies:
                        return -1
                    for item in ("login_uid", "stuid", "ltuid", "account_id"):
                        if item in res.cookies:
                            self.bbsUID = res.cookies[item]
                            break
                    if not self.bbsUID:
                        return -2
                    self.cookie = requests.utils.dict_from_cookiejar(
                        res.cookies.jar)
                    return 1
        except tenacity.RetryError:
            logging.error("登录米哈游账号 - 获取Cookie: 网络请求失败")
            logging.debug(traceback.format_exc())
            return -3

    # async def get_2(self, retry: bool = True):
    #     """
    #     获取stoken

    #     参数:
    #         `retry`: 是否允许重试

    #     - 若返回 `True` 说明Cookie缺少`cookie_token`
    #     - 若返回 `False` 说明网络请求失败或服务器没有正确返回
    #     """
    #     try:
    #         async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), reraise=True, wait=tenacity.wait_fixed(conf.SLEEP_TIME_RETRY)):
    #             with attempt:
    #                 res = await self.client.get(URL_2.format(self.cookie["login_ticket"], self.bbsUID), timeout=conf.TIME_OUT)
    #                 stoken = list(filter(
    #                     lambda data: data["name"] == "stoken", res.json()["data"]["list"]))[0]["token"]
    #                 self.cookie["stoken"] = stoken
    #                 return True
    #     except KeyError:
    #         logger.error(
    #             conf.LOG_HEAD + "登录米哈游账号 - 获取stoken: 服务器没有正确返回")
    #         logger.debug(conf.LOG_HEAD + "网络请求返回: {}".format(res.text))
    #         logger.debug(conf.LOG_HEAD + traceback.format_exc())
    #     except:
    #         logger.error(
    #             conf.LOG_HEAD + "登录米哈游账号 - 获取stoken: 网络请求失败")
    #         logger.debug(conf.LOG_HEAD + traceback.format_exc())
    #     return False

    # async def get_3(self, captcha: str, retry: bool = True) -> Literal[1, -1, -2, -3]:
    #     """
    #     第二次获取Cookie(目标是cookie_token)

    #     参数:
    #         `captcha`: 短信验证码
    #         `retry`: 是否允许重试

    #     - 若返回 `1` 说明已成功
    #     - 若返回 `-1` 说明Cookie缺少`cookie_token`
    #     - 若返回 `-2` 说明请求失败
    #     - 若返回 `-3` 说明验证码错误
    #     """
    #     try:
    #         async for attempt in tenacity.AsyncRetrying(stop=custom_attempt_times(retry), wait=tenacity.wait_fixed(conf.SLEEP_TIME_RETRY)):
    #             with attempt:
    #                 res = await self.client.post(URL_3, headers=HEADERS_2, json={
    #                     "is_bh2": False,
    #                     "mobile": str(self.phone),
    #                     "captcha": captcha,
    #                     "action_type": "login",
    #                     "token_type": 6
    #                 }, timeout=conf.TIME_OUT)
    #                 try:
    #                     res_json = res.json()
    #                     if res_json["data"]["msg"] == "验证码错误" or res_json["data"]["info"] == "Captcha not match Err":
    #                         logger.info(f"{conf.LOG_HEAD}登录米哈游账号 - 验证码错误")
    #                         return -3
    #                 except:
    #                     pass
    #                 if "cookie_token" not in res.cookies:
    #                     return -1
    #                 self.cookie.update(requests.utils.dict_from_cookiejar(res.cookies.jar))
    #                 await self.client.aclose()
    #                 return 1
    #     except tenacity.RetryError:
    #         logger.error(
    #             conf.LOG_HEAD + "登录米哈游账号 - 获取第三次Cookie: 网络请求失败")
    #         logger.debug(conf.LOG_HEAD + traceback.format_exc())
    #         return -2



def CmdLoginProcess():
    try:
        print("""\
            登录流程：
            \n1.输入手机号\
            \n2.前往 https://user.mihoyo.com/#/login/captcha，输入手机号并获取验证码（网页上不要登录）\
            \n3.回到项目命令行输入验证码1\
            \n4.继续前往 https://user.mihoyo.com/#/login/captcha，再次获取验证码（不要登录）\
            \n5.回到项目命令行输入验证码2\
            \n6.登录完成后，跟随指引完善配置\
            \n🚪过程中使用ctrl+c即可退出该流程\
            """.strip())
        state = {}
        while True:
            try:
                phone = input("输入手机号：")
                phone_num = int(phone)
            except ValueError:
                print("手机号应为11位数字，请重新输入")
                continue
            if len(phone) != 11:
                print("手机号应为11位数字，请重新输入")
            else:
                state['phone'] = phone_num
                state['getCookie'] = GetCookie(phone_num)
                break
        while True:
            try:
                print('前往 https://user.mihoyo.com/#/login/captcha，获取验证码（不要登录！）')
                captcha1 = input("输入验证码1：")
                int(captcha1)
            except ValueError:
                print("验证码应为6位数字，请重新输入")
                continue
            if len(captcha1) != 6:
                print("验证码应为6位数字，请重新输入")
                continue
            else:
                status: int = state['getCookie'].get_1(captcha1)
                if status == -1:
                    print("⚠️由于Cookie缺少login_ticket，无法继续，请稍后再试")
                    return
                elif status == -2:
                    print("⚠️由于Cookie缺少uid，无法继续，请稍后再试")
                    return
                elif status == -3:
                    print("⚠️网络请求失败，无法继续，请稍后再试")
                    return
                elif status == -4:
                    print("⚠️验证码错误，注意不要在网页上使用掉验证码，请重新发送")
                    continue
                else:
                    break
        status: bool = state["getCookie"].get_2()
        if not status:
            print("⚠️获取stoken失败，一种可能是登录失效，请稍后再试")
            return
        
    except KeyboardInterrupt:
            return
    


# @get_cookie.handle()
# async def _(event: PrivateMessageEvent, state: T_State):
#     await get_cookie.send('2.前往 https://user.mihoyo.com/#/login/captcha，获取验证码（不要登录！）')


# @get_cookie.got("验证码1", prompt='3.请发送验证码：')
# async def _(event: PrivateMessageEvent, state: T_State, captcha1: str = ArgPlainText('验证码1')):
#     if captcha1 == '退出':
#         print("🚪已成功退出")
#     try:
#         int(captcha1)
#     except:
#         await get_cookie.reject("⚠️验证码应为6位数字，请重新输入")
#     if len(captcha1) != 6:
#         await get_cookie.reject("⚠️验证码应为6位数字，请重新输入")
#     else:
#         status: int = await state['getCookie'].get_1(captcha1)
#         if status == -1:
#             print("⚠️由于Cookie缺少login_ticket，无法继续，请稍后再试")
#         elif status == -2:
#             print("⚠️由于Cookie缺少uid，无法继续，请稍后再试")
#         elif status == -3:
#             print("⚠️网络请求失败，无法继续，请稍后再试")
#         elif status == -4:
#             await get_cookie.reject("⚠️验证码错误，注意不要在网页上使用掉验证码，请重新发送")

#     status: bool = await state["getCookie"].get_2()
#     if not status:
#         print("⚠️获取stoken失败，一种可能是登录失效，请稍后再试")


# @get_cookie.handle()
# async def _(event: PrivateMessageEvent, state: T_State):
#     await get_cookie.send('4.请刷新网页，再次获取验证码（不要登录！）')


# @get_cookie.got('验证码2', prompt='4.请发送验证码：')
# async def _(event: PrivateMessageEvent, state: T_State, captcha2: str = ArgPlainText('验证码2')):
#     if captcha2 == '退出':
#         print("🚪已成功退出")
#     try:
#         int(captcha2)
#     except:
#         await get_cookie.reject("⚠️验证码应为6位数字，请重新输入")
#     if len(captcha2) != 6:
#         await get_cookie.reject("⚠️验证码应为6位数字，请重新输入")
#     else:
#         status: bool = await state["getCookie"].get_3(captcha2)
#         if status < 0:
#             if status == -3:
#                 await get_cookie.reject("⚠️验证码错误，注意不要在网页上使用掉验证码，请重新发送")
#             print("⚠️获取cookie_token失败，一种可能是登录失效，请稍后再试")

#     UserData.set_cookie(state['getCookie'].cookie,
#                         int(event.user_id), state['phone'])
#     print("🎉米游社账户 {} 绑定成功".format(state['phone']))
