# -*- coding: utf8 -*-
import requests, time, datetime, re, sys, os, json, random, math, traceback
global skey,sckey,base_url,req_url,corpid,corpsecret,agentid,touser,toparty,totag,open_get_weather,area,qweather

class MiMotion():
    name = "小米运动"

    def __init__(self, check_item):
        self.check_item = check_item
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "MiFit/6.12.0 (MCE16; Android 16; Density/1.5)",
            "app_name": "com.xiaomi.hm.health",
        }
        
    def log(self, level, message, data=None):
        """通用日志记录函数"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_msg = f"[{timestamp}] [{level}] {message}"
        
        if data is not None:
            if isinstance(data, (dict, list)):
                try:
                    data_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
                except:
                    data_str = str(data)
            else:
                data_str = str(data)
            log_msg += f"\n{data_str}"
        
        print(log_msg)
        print("-" * 80)

   #发送酷推
    def push(self, title, content):
        try:
            url = "https://push.xuthus.cc/send/" + skey
            data = title + "\n" + content
            self.log("PUSH", f"准备发送酷推推送", {"url": url, "title": title, "content": content[:100] + "..."})
            
            # 发送请求
            res = requests.post(url=url, data=data.encode('utf-8')).text
            self.log("PUSH", f"酷推推送响应", {"response": res})
        except Exception as e:
            error_traceback = traceback.format_exc()
            self.log("ERROR", f"酷推推送异常", error_traceback)

    # 推送server
    def push_wx(self,desp=""):
        try:
            server_url = f"https://sc.ftqq.com/{sckey}.send"
            params = {
                "text": '【小米运动步数修改】',
                "desp": desp
            }
            
            self.log("PUSH", f"准备发送Server酱推送", {"url": server_url, "params": params})

            response = requests.get(server_url, params=params).text
            self.log("PUSH", f"Server酱推送响应", {"response": response})
        except Exception as e:
            error_traceback = traceback.format_exc()
            self.log("ERROR", f"Server酱推送异常", error_traceback)

    # 推送telegram
    def push_telegram(self,msg):
        try:
            self.log("PUSH", f"准备发送Telegram推送", {"msg": msg[:200] + "..."})
            # 修复：使用传入的msg，而不是未定义的title和content
            send_data = {"chat_id": tg_user_id, "text": msg, "disable_web_page_preview": "true"}
            
            response = requests.post(
                url=f'https://api.telegram.org/bot{tg_bot_token}/sendMessage', data=send_data)
            
            self.log("PUSH", f"Telegram推送响应", {"response": response.json()})
        except Exception as e:
            error_traceback = traceback.format_exc()
            self.log("ERROR", f"Telegram推送异常", error_traceback)

    # 企业微信
    def get_access_token(self):
        try:
            urls = base_url + 'corpid=' + corpid + '&corpsecret=' + corpsecret
            self.log("WECHAT", f"获取企业微信access_token", {"url": urls})
            
            resp = requests.get(urls).json()
            self.log("WECHAT", f"企业微信access_token响应", resp)
            
            access_token = resp['access_token']
            return access_token
        except Exception as e:
            error_traceback = traceback.format_exc()
            self.log("ERROR", f"企业微信获取token异常", error_traceback)

    def run(self,msg):
        try:
            data = {
                "touser": touser,
                "toparty": toparty,
                "totag": totag,
                "msgtype": "text",
                "agentid": agentid,
                "text": {
                    "content": "【小米运动步数修改】\n" + msg
                },
                "safe": 0,
                "enable_id_trans": 0,
                "enable_duplicate_check": 0,
                "duplicate_check_interval": 1800
            }
            data = json.dumps(data, ensure_ascii=False)
            req_urls = req_url + self.get_access_token()
            
            self.log("WECHAT", f"发送企业微信消息", {"url": req_urls, "data": data})
            
            resp = requests.post(url=req_urls, data=data.encode('utf-8')).text
            self.log("WECHAT", f"企业微信消息响应", {"response": resp})
            
            return resp
        except Exception as e:
            error_traceback = traceback.format_exc()
            self.log("ERROR", f"企业微信推送异常", error_traceback)


    def get_time(self):
        try:
            url = "http://mshopact.vivo.com.cn/tool/config"
            self.log("TIME", f"获取时间戳", {"url": url})
            
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).json()
            t = response["data"]["nowTime"]
            
            self.log("TIME", f"时间戳获取成功", {"原始响应": response, "提取的时间戳": t})
            return t
        except Exception as e:
            error_traceback = traceback.format_exc()
            self.log("ERROR", f"获取时间戳异常", error_traceback)
            fallback_time = int(time.time() * 1000)
            self.log("WARN", f"使用本地时间戳", {"fallback_time": fallback_time})
            return fallback_time


    def login(self, user, password):
        self.log("LOGIN", f"开始登录流程", {"user": user, "password": password})
        
        # 正则定义
        email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        phone_pattern = r"^1\d{10}$"
        phone_with_86_pattern = r"^\+861\d{10}$"

        # 第一步：邮箱 → third_name = "email"
        if re.fullmatch(email_pattern, user):
            user = user
            third_name = "email"
            self.log("LOGIN", f"账户类型识别", {"type": "邮箱账户", "user": user})

        # 第二步：已带+86的手机号 → third_name = "huami_phone"
        elif re.fullmatch(phone_with_86_pattern, user):
            user = user
            third_name = "huami_phone"
            self.log("LOGIN", f"账户类型识别", {"type": "国际手机号", "user": user})

        # 第三步：纯手机号（无+86）→ 补全+86，third_name = "huami_phone"
        elif re.fullmatch(phone_pattern, user):
            user = f"+86{user}"
            third_name = "huami_phone"
            self.log("LOGIN", f"账户类型识别", {"type": "国内手机号", "user": user})

        # 其他情况 → 保持原样，third_name = "huami_phone"
        else:
            user = user
            third_name = "huami_phone"
            self.log("LOGIN", f"账户类型识别", {"type": "其他类型", "user": user})
        
        """返回 (login_token, user_id, app_token) 任意一步失败返回 (0, 0, msg)"""
        # ---------- 阶段 1：拿 code ----------
        # 使用PHP版本的API
        url1 = "https://api-user.zepp.com/v2/registrations/tokens"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "MiFit6.14.0 (OPD2413; Android 15; Density/2.625)",
            "app_name": "com.xiaomi.hm.health",
            "appname": "com.xiaomi.hm.health",
            "appplatform": "android_phone",
            "Accept": "application/json",
            "Accept-Language": "zh-CN,zh;q=0.8",
            "Connection": "keep-alive",
            "x-hm-ekv": "1"
        }
        
        data1 = {
            "emailOrPhone": user,
            "password": password,
            "state": "REDIRECTION",
            "client_id": "HuaMi",
            "country_code": "CN",
            "token": "access",
            "redirect_uri": "https://s3-us-west-2.amazonaws.com/hm-registration/successsignin.html"
        }

        self.log("LOGIN_STAGE1", f"阶段1: 获取code", {
            "url": url1,
            "headers": headers,
            "data": data1
        })

        try:
            r1 = requests.post(url1, data=data1, headers=headers, timeout=10, allow_redirects=False)
            self.log("LOGIN_STAGE1", f"阶段1响应状态", {
                "status_code": r1.status_code,
                "headers": dict(r1.headers)
            })
            
            if r1.status_code != 200:
                self.log("ERROR", f"阶段1登录失败", {"response": r1.text})
                return 0, 0, 0
            
            # 从响应头中提取access token
            access = None
            response_text = r1.text
            
            # 尝试从响应头中获取access token
            if 'access=' in response_text:
                match = re.search(r'access=([^&]+)', response_text)
                if match:
                    access = match.group(1)
            elif 'refresh=' in response_text:
                match = re.search(r'refresh=([^&]+)', response_text)
                if match:
                    access = match.group(1)
            
            if not access:
                self.log("ERROR", f"未找到access token", {"response": response_text[:200]})
                return 0, 0, 0
            
            self.log("LOGIN_STAGE1", f"获取到access", {"access": access})
        except Exception as e:
            self.log("ERROR", f"阶段1登录异常", traceback.format_exc())
            return 0, 0, 0

        # ---------- 阶段 2：拿 token ----------
        url2 = "https://account.zepp.com/v2/client/login"
        headers2 = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "User-Agent": "MiFit6.14.0 (OPD2413; Android 15; Density/2.625)",
            "app_name": "com.xiaomi.hm.health"
        }
        
        data2 = {
            "app_name": "com.xiaomi.hm.health",
            "country_code": "CN",
            "code": access,
            "device_id": "efd38eeb-160d-44e4-9317-6df2145bcb0a",
            "device_model": "android_phone",
            "app_version": "6.14.0",
            "grant_type": "access_token",
            "allow_registration": "false",
            "dn": "account.zepp.com,api-user.zepp.com,api-mifit.zepp.com,api-watch.zepp.com,app-analytics.zepp.com,api-analytics.huami.com,auth.zepp.com",
            "source": "com.xiaomi.hm.health:6.14.0:50818",
            "third_name": third_name,
            "lang": "zh"
        }

        self.log("LOGIN_STAGE2", f"阶段2: 获取token", {
            "url": url2,
            "data": data2
        })

        try:
            r2 = requests.post(url2, data=data2, headers=headers2, timeout=10)
            self.log("LOGIN_STAGE2", f"阶段2响应状态", {
                "status_code": r2.status_code,
                "headers": dict(r2.headers)
            })
            
            if r2.status_code != 200:
                self.log("ERROR", f"阶段2登录失败", {"response": r2.text})
                return 0, 0, 0
            
            response_json = r2.json()
            self.log("LOGIN_STAGE2", f"阶段2成功响应", response_json)
            
            if response_json.get("result") != "ok":
                self.log("ERROR", f"登录失败", {"response": response_json})
                return 0, 0, 0
            
            info = response_json["token_info"]
            self.log("LOGIN_STAGE2", f"提取的token信息", {
                "login_token": info["login_token"],
                "user_id": info["user_id"],
                "app_token": info["app_token"],
                "ttl": info["ttl"],
                "app_ttl": info["app_ttl"]
            })
            
            return info["login_token"], info["user_id"], info["app_token"]
        except Exception as e:
            self.log("ERROR", f"阶段2登录异常", traceback.format_exc())
            return 0, 0, 0

    def main(self):
        self.log("MAIN", f"开始处理账号", {
            "user": self.check_item.get("user"),
            "min_step": self.check_item.get("min_step", 10000),
            "max_step": self.check_item.get("max_step", 19999)
        })
    
        # ---------- 1. 获取步数比例 ----------
        try:
            account_user = str(self.check_item.get("user"))
            account_password = str(self.check_item.get("password"))
            hea = {'User-Agent': 'Mozilla/5.0'}
            url = 'https://apps.game.qq.com/CommArticle/app/reg/gdate.php'
            
            self.log("STEP_RATIO", f"获取步数比例", {"url": url})
            r = requests.get(url, headers=hea, timeout=10)
            
            if r.status_code != 200:
                self.log("ERROR", f'获取步数比例失败', {"status_code": r.status_code, "response": r.text})
                hour = 12
            else:
                self.log("STEP_RATIO", f'步数比例响应', {"response": r.text[:200]})
                reg = re.search(r'\d{4}-\d{2}-\d{2} (\d{2}):\d{2}:\d{2}', r.text)
                hour = int(reg.group(1)) if reg else 12
            
            self.log("STEP_RATIO", f'获取到的小时数', {"hour": hour})
            min_ratio = int(hour) / 22
            max_ratio = int(hour) / 21
            step_ratio = random.uniform(min_ratio, max_ratio)
            self.log("STEP_RATIO", f'计算出的比例', {
                "hour": hour,
                "min_ratio": min_ratio,
                "max_ratio": max_ratio,
                "step_ratio": step_ratio
            })
        except Exception as e:
            self.log("ERROR", f'步数比例异常', traceback.format_exc())
            step_ratio = random.uniform(0.5, 0.9)
            self.log("WARN", f'使用默认比例', {"step_ratio": step_ratio})
    
        # ---------- 2. 计算步数范围 ----------
        try:
            min_step = math.ceil(int(self.check_item.get("min_step", 10000)) * step_ratio)
            max_step = math.ceil(int(self.check_item.get("max_step", 19999)) * step_ratio)
            if min_step > max_step:
                min_step, max_step = max_step, min_step
            self.log("STEP_CALC", f'计算步数范围', {
                "原始min_step": self.check_item.get("min_step", 10000),
                "原始max_step": self.check_item.get("max_step", 19999),
                "计算后min_step": min_step,
                "计算后max_step": max_step
            })
        except Exception as e:
            self.log("ERROR", f'步数范围计算异常', traceback.format_exc())
            min_step, max_step = 10000, 19999
            self.log("WARN", f'使用默认步数范围', {"min_step": min_step, "max_step": max_step})
    
        step = str(random.randint(min_step, max_step))
        self.log("STEP_CALC", f'最终步数', {
            "min_step": min_step,
            "max_step": max_step,
            "最终步数": step
        })
    
        # ---------- 3. 登录 ----------
        login_token, userid, app_token = self.login(account_user, account_password)
        if 0 in (login_token, userid, app_token):
            msg = f"帐号信息: {account_user[:4]}****{account_user[-4:]}\n修改信息: 登录失败\n"
            self.log("ERROR", f'登录失败', msg)
            return msg
        
        self.log("LOGIN_SUCCESS", f'登录成功', {
            "user_id": userid,
            "login_token": login_token,
            "app_token": app_token
        })
    
        # ---------- 4. 提交步数 ----------
        try:
            t = int(time.time())
            today = time.strftime("%Y-%m-%d")
            self.log("SUBMIT_PREPARE", f'提交准备', {
                "时间戳": t,
                "今日日期": today,
                "目标步数": step
            })
            
            # 这里用您的完整 data_json 模板
            data_json = "[{"data_hr":"\/\/\/\/\/\/9L\/\/\/\/\/\/\/\/\/\/\/\/Vv\/\/\/\/\/\/\/\/\/\/\/0v\/\/\/\/\/\/\/\/\/\/\/9e\/\/\/\/\/0n\/a\/\/\/S\/\/\/\/\/\/\/\/\/\/\/\/0b\/\/\/\/\/\/\/\/\/\/1FK\/\/\/\/\/\/\/\/\/\/\/\/R\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/9PTFFpaf9L\/\/\/\/\/\/\/\/\/\/\/\/R\/\/\/\/\/\/\/\/\/\/\/\/0j\/\/\/\/\/\/\/\/\/\/\/9K\/\/\/\/\/\/\/\/\/\/\/\/Ov\/\/\/\/\/\/\/\/\/\/\/zf\/\/\/86\/zr\/Ov88\/zf\/Pf\/\/\/0v\/S\/8\/\/\/\/\/\/\/\/\/\/\/\/\/Sf\/\/\/\/\/\/\/\/\/\/\/z3\/\/\/\/\/\/0r\/Ov\/\/\/\/\/\/S\/9L\/zb\/Sf9K\/0v\/Rf9H\/zj\/Sf9K\/0\/\/N\/\/\/\/0D\/Sf83\/zr\/Pf9M\/0v\/Ov9e\/\/\/\/\/\/\/\/\/\/\/\/S\/\/\/\/\/\/\/\/\/\/\/\/zv\/\/z7\/O\/83\/zv\/N\/83\/zr\/N\/86\/z\/\/Nv83\/zn\/Xv84\/zr\/PP84\/zj\/N\/9e\/zr\/N\/89\/03\/P\/89\/z3\/Q\/9N\/0v\/Tv9C\/0H\/Of9D\/zz\/Of88\/z\/\/PP9A\/zr\/N\/86\/zz\/Nv87\/0D\/Ov84\/0v\/O\/84\/zf\/MP83\/zH\/Nv83\/zf\/N\/84\/zf\/Of82\/zf\/OP83\/zb\/Mv81\/zX\/R\/9L\/0v\/O\/9I\/0T\/S\/9A\/zn\/Pf89\/zn\/Nf9K\/07\/N\/83\/zn\/Nv83\/zv\/O\/9A\/0H\/Of8\/\/zj\/PP83\/zj\/S\/87\/zj\/Nv84\/zf\/Of83\/zf\/Of83\/zb\/Nv9L\/zj\/Nv82\/zb\/N\/85\/zf\/N\/9J\/zf\/Nv83\/zj\/Nv84\/0r\/Sv83\/zf\/MP\/\/\/zb\/Mv82\/zb\/Of85\/z7\/Nv8\/\/0r\/S\/85\/0H\/QP9B\/0D\/Nf89\/zj\/Ov83\/zv\/Nv8\/\/0f\/Sv9O\/0ZeXv\/\/\/\/\/\/\/\/\/\/\/1X\/\/\/\/\/\/\/\/\/\/\/9B\/\/\/\/\/\/\/\/\/\/\/\/TP\/\/\/1b\/\/\/\/\/\/0\/\/\/\/\/\/\/\/\/\/\/\/9N\/\/\/\/\/\/\/\/\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+\/v7+","date":"2025-08-17","data":[{"start":0,"stop":1439,"value":"UA8AUBQAUAwAUBoAUAEAYCcAUBkAUB4AUBgAUCAAUAEAUBkAUAwAYAsAYB8AYB0AYBgAYCoAYBgAYB4AUCcAUBsAUB8AUBwAUBIAYBkAYB8AUBoAUBMAUCEAUCIAYBYAUBwAUCAAUBgAUCAAUBcAYBsAYCUAATIPYD0KECQAYDMAYB0AYAsAYCAAYDwAYCIAYB0AYBcAYCQAYB0AYBAAYCMAYAoAYCIAYCEAYCYAYBsAYBUAYAYAYCIAYCMAUB0AUCAAUBYAUCoAUBEAUC8AUB0AUBYAUDMAUDoAUBkAUC0AUBQAUBwAUA0AUBsAUAoAUCEAUBYAUAwAUB4AUAwAUCcAUCYAUCwKYDUAAUUlEC8IYEMAYEgAYDoAYBAAUAMAUBkAWgAAWgAAWgAAWgAAWgAAUAgAWgAAUBAAUAQAUA4AUA8AUAkAUAIAUAYAUAcAUAIAWgAAUAQAUAkAUAEAUBkAUCUAWgAAUAYAUBEAWgAAUBYAWgAAUAYAWgAAWgAAWgAAWgAAUBcAUAcAWgAAUBUAUAoAUAIAWgAAUAQAUAYAUCgAWgAAUAgAWgAAWgAAUAwAWwAAXCMAUBQAWwAAUAIAWgAAWgAAWgAAWgAAWgAAWgAAWgAAWgAAWREAWQIAUAMAWSEAUDoAUDIAUB8AUCEAUC4AXB4AUA4AWgAAUBIAUA8AUBAAUCUAUCIAUAMAUAEAUAsAUAMAUCwAUBYAWgAAWgAAWgAAWgAAWgAAWgAAUAYAWgAAWgAAWgAAUAYAWwAAWgAAUAYAXAQAUAMAUBsAUBcAUCAAWwAAWgAAWgAAWgAAWgAAUBgAUB4AWgAAUAcAUAwAWQIAWQkAUAEAUAIAWgAAUAoAWgAAUAYAUB0AWgAAWgAAUAkAWgAAWSwAUBIAWgAAUC4AWSYAWgAAUAYAUAoAUAkAUAIAUAcAWgAAUAEAUBEAUBgAUBcAWRYAUA0AWSgAUB4AUDQAUBoAXA4AUA8AUBwAUA8AUA4AUA4AWgAAUAIAUCMAWgAAUCwAUBgAUAYAUAAAUAAAUAAAUAAAUAAAUAAAUAAAUAAAUAAAWwAAUAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAeSEAeQ8AcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcBcAcAAAcAAAcCYOcBUAUAAAUAAAUAAAUAAAUAUAUAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcCgAeQAAcAAAcAAAcAAAcAAAcAAAcAYAcAAAcBgAeQAAcAAAcAAAegAAegAAcAAAcAcAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcCkAeQAAcAcAcAAAcAAAcAwAcAAAcAAAcAIAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcCIAeQAAcAAAcAAAcAAAcAAAcAAAeRwAeQAAWgAAUAAAUAAAUAAAUAAAUAAAcAAAcAAAcBoAeScAeQAAegAAcBkAeQAAUAAAUAAAUAAAUAAAUAAAUAAAcAAAcAAAcAAAcAAAcAAAcAAAegAAegAAcAAAcAAAcBgAeQAAcAAAcAAAcAAAcAAAcAAAcAkAegAAegAAcAcAcAAAcAcAcAAAcAAAcAAAcAAAcA8AeQAAcAAAcAAAeRQAcAwAUAAAUAAAUAAAUAAAUAAAUAAAcAAAcBEAcA0AcAAAWQsAUAAAUAAAUAAAUAAAUAAAcAAAcAoAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAYAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcBYAegAAcAAAcAAAegAAcAcAcAAAcAAAcAAAcAAAcAAAeRkAegAAegAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAEAcAAAcAAAcAAAcAUAcAQAcAAAcBIAeQAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcBsAcAAAcAAAcBcAeQAAUAAAUAAAUAAAUAAAUAAAUBQAcBYAUAAAUAAAUAoAWRYAWTQAWQAAUAAAUAAAUAAAcAAAcAAAcAAAcAAAcAAAcAMAcAAAcAQAcAAAcAAAcAAAcDMAeSIAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcAAAcBQAeQwAcAAAcAAAcAAAcAMAcAAAeSoAcA8AcDMAcAYAeQoAcAwAcFQAcEMAeVIAaTYAbBcNYAsAYBIAYAIAYAIAYBUAYCwAYBMAYDYAYCkAYDcAUCoAUCcAUAUAUBAAWgAAYBoAYBcAYCgAUAMAUAYAUBYAUA4AUBgAUAgAUAgAUAsAUAsAUA4AUAMAUAYAUAQAUBIAASsSUDAAUDAAUBAAYAYAUBAAUAUAUCAAUBoAUCAAUBAAUAoAYAIAUAQAUAgAUCcAUAsAUCIAUCUAUAoAUA4AUB8AUBkAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAAfgAA","tz":32,"did":"DA932FFFFE8816E7","src":24}],"summary":"{\"v\":6,\"slp\":{\"st\":1628296479,\"ed\":1628296479,\"dp\":0,\"lt\":0,\"wk\":0,\"usrSt\":-1440,\"usrEd\":-1440,\"wc\":0,\"is\":0,\"lb\":0,\"to\":0,\"dt\":0,\"rhr\":0,\"ss\":0},\"stp\":{\"ttl\":17760,\"dis\":10627,\"cal\":510,\"wk\":41,\"rn\":50,\"runDist\":7654,\"runCal\":397,\"stage\":[{\"start\":327,\"stop\":341,\"mode\":1,\"dis\":481,\"cal\":13,\"step\":680},{\"start\":342,\"stop\":367,\"mode\":3,\"dis\":2295,\"cal\":95,\"step\":2874},{\"start\":368,\"stop\":377,\"mode\":4,\"dis\":1592,\"cal\":88,\"step\":1664},{\"start\":378,\"stop\":386,\"mode\":3,\"dis\":1072,\"cal\":51,\"step\":1245},{\"start\":387,\"stop\":393,\"mode\":4,\"dis\":1036,\"cal\":57,\"step\":1124},{\"start\":394,\"stop\":398,\"mode\":3,\"dis\":488,\"cal\":19,\"step\":607},{\"start\":399,\"stop\":414,\"mode\":4,\"dis\":2220,\"cal\":120,\"step\":2371},{\"start\":415,\"stop\":427,\"mode\":3,\"dis\":1268,\"cal\":59,\"step\":1489},{\"start\":428,\"stop\":433,\"mode\":1,\"dis\":152,\"cal\":4,\"step\":238},{\"start\":434,\"stop\":444,\"mode\":3,\"dis\":2295,\"cal\":95,\"step\":2874},{\"start\":445,\"stop\":455,\"mode\":4,\"dis\":1592,\"cal\":88,\"step\":1664},{\"start\":456,\"stop\":466,\"mode\":3,\"dis\":1072,\"cal\":51,\"step\":1245},{\"start\":467,\"stop\":477,\"mode\":4,\"dis\":1036,\"cal\":57,\"step\":1124},{\"start\":478,\"stop\":488,\"mode\":3,\"dis\":488,\"cal\":19,\"step\":607},{\"start\":489,\"stop\":499,\"mode\":4,\"dis\":2220,\"cal\":120,\"step\":2371},{\"start\":500,\"stop\":511,\"mode\":3,\"dis\":1268,\"cal\":59,\"step\":1489},{\"start\":512,\"stop\":522,\"mode\":1,\"dis\":152,\"cal\":4,\"step\":238}]},\"goal\":8000,\"tz\":\"28800\"}","source":24,"type":0}]"
            
            # 记录替换前的 data_json 状态
            self.log("DATA_REPLACE", f"data_json替换前状态", {
                "data_json长度": len(data_json),
                "是否包含2025-08-17": "2025-08-17" in data_json,
                "是否包含17760": "17760" in data_json
            })
            
            data_json = data_json.replace('2025-08-17', today).replace('17760', step)
            
            # 记录替换后的 data_json 状态
            self.log("DATA_REPLACE", f"data_json替换后状态", {
                "data_json长度": len(data_json),
                "是否包含今天日期": today in data_json,
                "是否包含目标步数": step in data_json
            })
    
            # 使用与PHP版本相同的API端点
            url = f'https://api-mifit-cn.zepp.com/v1/data/band_data.json?&t={t}'
            
            # 设置与PHP版本相同的headers
            headers = {
                "apptoken": app_token, 
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "Accept-Language": "zh-CN,zh;q=0.8",
                "Connection": "keep-alive",
                "app_name": "com.xiaomi.hm.health",
                "appname": "com.xiaomi.hm.health",
                "appplatform": "android_phone",
                "User-Agent": "MiFit6.14.0 (OPD2413; Android 15; Density/2.625)"
            }
            
            # 使用与PHP版本相同的设备ID
            data = f'data_json={data_json}&userid={userid}&device_type=0&last_sync_data_time={t}&last_deviceid=C4D2D4FFFE8C5068'
            
            self.log("SUBMIT", f"提交步数请求", {
                "url": url,
                "headers": headers,
                "data_length": len(data),
                "data_preview": data[:200] + "..." if len(data) > 200 else data
            })
            
            resp = requests.post(url, data=data, headers=headers, timeout=10)
            self.log("SUBMIT", f"提交步数响应", {
                "status_code": resp.status_code,
                "headers": dict(resp.headers)
            })
            
            if resp.status_code != 200:
                self.log("ERROR", f'提交步数失败', {"status_code": resp.status_code, "response": resp.text})
                raise RuntimeError('接口返回非 200')
    
            res_json = resp.json()
            self.log("SUBMIT", f"提交步数响应JSON", res_json)
            
            if res_json.get('code') == 1 or res_json.get('message') == 'success':
                msg = (f"帐号信息: {account_user[:4]}****{account_user[-4:]}\n"
                       f"修改信息: success\n"
                       f"修改步数: {step}\n")
                self.log("SUCCESS", f"步数修改成功", {"message": res_json.get('message'), "code": res_json.get('code'), "step": step})
            else:
                msg = (f"帐号信息: {account_user[:4]}****{account_user[-4:]}\n"
                       f"修改信息: 失败-{res_json}\n")
                self.log("ERROR", f"步数修改失败", {"response": res_json})
        except Exception as e:
            error_traceback = traceback.format_exc()
            self.log("ERROR", f"提交步数异常", error_traceback)
            msg = f"【异常】账号 {account_user[:4]}****{account_user[-4:]} 提交失败：{e}\n"
    
        self.log("RESULT", f"处理结果", {"msg": msg})
        return msg

if __name__ == "__main__":
    # 添加一个简单的日志函数，用于主程序的日志记录
    def log_main(level, message, data=None):
        """主程序使用的简单日志函数"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        log_msg = f"[{timestamp}] [{level}] {message}"
        
        if data is not None:
            if isinstance(data, (dict, list)):
                try:
                    data_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
                except:
                    data_str = str(data)
            else:
                data_str = str(data)
            log_msg += f"\n{data_str}"
        
        print(log_msg)
        print("-" * 80)
    
    try:
        log_main("SYSTEM", f"程序启动", {"时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        
        #with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "/root/config.json"), "r", encoding="utf-8") as f:
            #datas = json.loads(f.read())
        datas = json.loads(os.environ["CONFIG"])
        log_main("CONFIG", f"加载配置", {"config_keys": list(datas.keys())})
        
        # 开启根据地区天气情况降低步数（默认关闭）
        if datas.get("OPEN_GET_WEATHER"):
            open_get_weather = datas.get("OPEN_GET_WEATHER")
        else:
            open_get_weather = "False"
        # 设置获取天气的地区（上面开启后必填）如：area = "宁波"
        if datas.get("AREA"):
            area = datas.get("AREA")
        else:
            area = "NO"
        # 和风天气 Private KEY
        if datas.get("OPEN_GET_WEATHER"):
            qweather = datas.get("OPEN_GET_WEATHER")
        else:
            qweather = "False"
            
        log_main("CONFIG_DETAIL", f"配置详情", {
            "OPEN_GET_WEATHER": open_get_weather,
            "AREA": area,
            "qweather": qweather
        })
            
        msg = ""
        mimotion_items = datas.get("MIMOTION", [])
        log_main("ACCOUNTS", f"账号列表", {"账号数量": len(mimotion_items)})
        
        for i in range(len(mimotion_items)):
            log_main("ACCOUNT_PROCESS", f"开始处理第{i+1}个账号", {"index": i, "item": mimotion_items[i]})
            _check_item = mimotion_items[i]
            msg += MiMotion(check_item=_check_item).main()
            time.sleep(10)
            
        log_main("SUMMARY", f"所有账号处理完成", {"总消息长度": len(msg)})
        
        # 酷推skey和server酱sckey和企业微信设置，只用填一个其它留空即可
        if datas.get("SKEY"):
            skey = datas.get("SKEY")
            log_main("PUSH_CONFIG", f"配置酷推推送", {"skey": skey})
            MiMotion(check_item=_check_item).push('【小米运动步数修改】', msg)
        # 推送server酱
        if datas.get("SCKEY"):
            sckey = datas.get("SCKEY")
            log_main("PUSH_CONFIG", f"配置Server酱推送", {"sckey": sckey})
            MiMotion(check_item=_check_item).push_wx(msg)
        # 推送telegram
        if datas.get("TG_BOT_TOKEN") or datas.get("TG_USER_ID"):
            tg_bot_token = datas.get("TG_BOT_TOKEN")
            tg_user_id = datas.get("TG_USER_ID")
            log_main("PUSH_CONFIG", f"配置Telegram推送", {
                "tg_bot_token": tg_bot_token,
                "tg_user_id": tg_user_id
            })
            MiMotion(check_item=_check_item).push_telegram(msg)

        # 企业微信推送
        # 是否开启企业微信推送false关闭true开启，默认关闭，开启后请填写设置并将上面两个都留空
        if datas.get("POSITION"):
            base_url = 'https://qyapi.weixin.qq.com/cgi-bin/gettoken?'
            req_url = 'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token='
            corpid = datas.get("CORPID")  # 企业ID， 登陆企业微信，在我的企业-->企业信息里查看
            corpsecret = datas.get("CORPSECRET")  # 自建应用，每个自建应用里都有单独的secret
            agentid = datas.get("AGENTID")  # 填写你的应用ID，不加引号，是个整型常数,就是AgentId
            touser = datas.get("TOUSER")  # 指定接收消息的成员，成员ID列表（多个接收者用'|'分隔，最多支持1000个）。特殊情况：指定为"@all"，则向该企业应用的全部成员发送
            toparty = datas.get("TOPARTY")  # 指定接收消息的部门，部门ID列表，多个接收者用'|'分隔，最多支持100个。当touser为"@all"时忽略本参数
            totag = datas.get("TOTAG")  # 指定接收消息的标签，标签ID列表，多个接收者用'|'分隔，最多支持100个。当touser为"@all"时忽略本参数
            
            log_main("PUSH_CONFIG", f"配置企业微信推送", {
                "corpid": corpid,
                "corpsecret": corpsecret,
                "agentid": agentid,
                "touser": touser,
                "toparty": toparty,
                "totag": totag
            })
            
            MiMotion(check_item=_check_item).run(msg)
        # 推送CONFIG配置
        # MiMotion(check_item=_check_item).run(os.environ["CONFIG"])
        
        log_main("SYSTEM", f"程序结束", {"时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        
    except Exception as e:
        # 获取报错位置的详细信息
        error_traceback = traceback.format_exc()
        log_main("ERROR", f"主程序异常", error_traceback)
