# 打开游戏
import sys

import cv2
import time, os
from capture.capture_factory import capture
from controller.BaseController import BaseController
from myutils.configutils import resource_path
from myutils.os_utils import switch_input_language, LANG_ENGLISH
import subprocess
template_path = os.path.join(resource_path, 'template')
icon_button_logout = cv2.imread(os.path.join(template_path, 'login','icon_button_logout.png'), cv2.IMREAD_GRAYSCALE)
icon_button_agreement = cv2.imread(os.path.join(template_path, 'login','icon_button_login_agreement.png'), cv2.IMREAD_GRAYSCALE)
from controller.OCRController import OCRController

class LoginController(BaseController):
    
    def __init__(self):
        super(LoginController, self).__init__()
        self.ocr = OCRController()
        
    def open_game(self):
        from myutils.configutils import WindowsConfig
        game_path = WindowsConfig.get(WindowsConfig.KEY_GAME_PATH)
        subprocess.Popen([game_path], shell=True)
        # os.startfile(game_path)
        self.logger.debug("已经执行启动游戏命令，先等待10秒")
        time.sleep(10)
        start_wait = time.time()
        while not capture.is_active() and time.time() - start_wait < 120 and not self.stop_listen:
            try:
                capture.activate_window()
            except Exception as e:
                self.logger.debug(e.args)
                self.logger.debug(f'正在打开游戏中, 剩余等待时间{120-(time.time() - start_wait)}')
            time.sleep(2)

        start_wait = time.time()
        while not self.ocr.is_text_in_screen("进入游戏", "点击进入", match_all=True) and time.time()-start_wait < 120:
            if self.stop_listen: return
            self.logger.debug(f'正在载入登录界面, 剩余等待时间:{120-(time.time()-start_wait)}秒')
            time.sleep(2)

        if self.ocr.is_text_in_screen("进入游戏", "点击进入"):
            self.logger.debug('成功加载登录界面')
        else:
            self.logger.debug('无法加载登录界面')
            return False
        
         # 更新登录流程
        if self.ocr.is_text_in_screen("点击进入"):
            self.logger.debug('开始切换账号流程')
            
            # 1. 点击退出按钮 (重试3次)
            retry_count = 3
            while retry_count > 0:
                if self.ocr.click_if_appear(icon_button_logout, timeout=5):
                    break
                retry_count -= 1
                self.logger.debug(f'重试点击退出按钮，剩余重试次数: {retry_count}')
                time.sleep(1)
            if retry_count == 0:
                self.logger.error('无法点击退出按钮')
                return False
            time.sleep(2)
            
            # 2. 点击确认退出 (重试3次)
            retry_count = 3
            while retry_count > 0:
                if self.ocr.find_text_and_click('退出', match_all=True):
                    break
                retry_count -= 1
                self.logger.debug(f'重试点击确认退出，剩余重试次数: {retry_count}')
                time.sleep(1)
            if retry_count == 0:
                self.logger.error('无法点击确认退出')
                return False
            time.sleep(2)
            
            # 3. 点击登录其他账号 (重试3次)
            retry_count = 3
            while retry_count > 0:
                if self.ocr.find_text_and_click('登录其他账号', match_all=True):
                    break
                retry_count -= 1
                self.logger.debug(f'重试点击登录其他账号，剩余重试次数: {retry_count}')
                time.sleep(1)
            if retry_count == 0:
                self.logger.error('无法点击登录其他账号')
                return False
            time.sleep(2)
            
            return True
        else:
            self.logger.debug('已在登录界面，可直接输入账号密码')
            return True

        # self.logger.debug('点击切换账号')
        # self.ocr.click_if_appear(icon_button_logout,timeout=2)
        # time.sleep(1)
        # self.ocr.find_text_and_click('确定', match_all=True)

    def user_input_focus(self):
        self.ocr.find_text_and_click('输入手机号/邮箱')
        self.logger.debug('点击输入手机号/邮箱成功')
        
    def password_input_focus(self):
        self.ocr.find_text_and_click('输入密码')

    def type_string(self, text):
        for c in text:
            self.kb_press_and_release(c)
            time.sleep(0.02)

            # 每输入一个字符按下shift避免中文输入法干扰
            # self.kb_press_and_release(self.Key.shift)
            # time.sleep(0.02)

    def user_pwd_input(self,user_name, password):
        self.logger.debug("强制切换英文输入法")
        try:
            switch_input_language(LANG_ENGLISH)
        except RuntimeError as e:
            self.logger.error("切换失败！")


        # 输入框获取焦点
        self.logger.debug('强制置游戏窗口于前台')
        capture.activate_window()
        time.sleep(0.5)
        self.logger.debug('输入框获取焦点')
        self.user_input_focus()
        self.logger.debug('输入账号')
        time.sleep(0.5)
        self.logger.debug(f'输入账号: {user_name}')
        self.type_string(user_name)
        self.logger.debug('输入账号完毕')
        time.sleep(0.5)
        self.logger.debug('密码框获取焦点')
        self.password_input_focus()
        self.logger.debug('输入密码')
        time.sleep(0.5)
        self.logger.debug(f'输入密码: {password}')
        self.type_string(password)
        self.logger.debug('输入密码完毕')
        time.sleep(0.5)
        self.logger.debug('点击进入游戏')

        # 点击同意协议
        self.logger.debug('点击同意协议')
        ocr_results = self.ocr.find_match_text('立即注册')
        if len(ocr_results) < 1: self.logger.debug('未找到立即注册按钮')
        time.sleep(0.5)
        self.click_if_appear(icon_button_agreement, timeout=0.5)
        time.sleep(0.5)

        if self.ocr.find_text_and_click("进入游戏", match_all=True):
            self.logger.debug("已经点击进入游戏")
        else:self.logger.debug('未找到"进入游戏"的文本')
        self.logger.debug("先等待5秒")
        time.sleep(5)
        start_wait = time.time()
        while not self.gc.has_paimon(delay=True) and time.time()-start_wait < 80 and not BaseController.stop_listen:
            self.logger.debug(f'等待进入游戏界面中, 剩余{80-(time.time()-start_wait)}秒')
            self.click_screen((10,10))
            time.sleep(3)

        if self.gc.has_paimon(delay=True):
            self.logger.debug('成功进入游戏')
        else:
            self.logger.error("无法进入游戏")

        # 无法解决卡住问题
        # self.logger.debug("登陆后再激活一次窗口")
        # capture.activate_window()
        #


    def click_login_button(self):
        login_count = 5
        while not self.ocr.find_text_and_click("登录") and login_count > 0:
            login_count -= 1
            time.sleep(5)

    # # 指定账户密码登录
    # open_game()
    # user_pwd_input(user_name, password)

    # cv2.imwrite('login2.jpg', capture.get_screenshot())

if __name__ == '__main__':
    from myutils.os_utils import kill_game
    kill_game()
    login = LoginController()
    login.open_game()
    # from myutils.configutils import AccountConfig
    # ci = AccountConfig.get_current_instance()
    # account = ci.get("account")
    # password = ci.get("password")
    # login.user_pwd_input(user_name=account, password=password)
