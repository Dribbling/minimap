import time

from controller.BaseController import BaseController

class UIController(BaseController):
    def __init__(self, debug_enable=None):
        super().__init__(debug_enable)
        from controller.OCRController import OCRController
        self.ocr = OCRController(debug_enable)

    # def open_map_page(self): pass


    def open_paimon_menu_page(self):
        """
        打开派蒙菜单
        :return:
        """
        pass

    def navigation_to_world_page(self, timeout=5):
        """
        回到游戏大世界界面
        :return:
        """
        start_wait = time.time()
        while not self.gc.has_paimon(delay=False) and time.time() - start_wait < timeout:
            self.click_ui_close_button()
            time.sleep(1)

        if self.gc.has_paimon(delay=False):
            self.logger.debug('回到了大世界界面')
        else:
            self.logger.error('无法回到大世界界面')

    def navigate_to_adventure_handbook_page(self):
        """
        前往冒险之证页面
        :return:
        """
        if not self.gc.has_template_icon_in_screen(self.gc.img_advanture_handbook_left_top_corner):
            self.navigation_to_world_page()

        while not self.gc.has_template_icon_in_screen(self.gc.img_advanture_handbook_left_top_corner):
            self.kb_press_and_release(self.Key.f1)
            time.sleep(2)
        self.logger.debug('已经打开冒险之证页面')




class TeamNotFoundException(Exception): pass

class TeamUIController(UIController):
    last_selected_team = None

    def __init__(self):
        super().__init__(True)

    def open_team_config_page(self, timeout=10):
        """
        打开队伍配置界面
        :return:
        """
        result = self.ocr.find_text_and_click('队伍配置')
        start_time = time.time()
        while not result:
            if time.time() - start_time > timeout:
                self.logger.error("打开队伍配置页面超时")
                return False
            self.kb_press_and_release(self.Key.esc)
            time.sleep(1.5)
            result = self.ocr.find_text_and_click('队伍配置')

        self.log('等待加载中...')
        start_wait = time.time()
        success = False
        while time.time() - start_wait < 5:
            pos = self.gc.get_icon_position(self.gc.icon_team_selector)
            if len(pos) > 0:
                success = True
                break
        self.log('成功打开队伍配置界面')
        return success

    def open_team_selector(self):
        """
        打开队伍选择器
        :return:
        """
        success = False
        for _ in range(2): # 尝试两次打开队伍配置界面
            success = self.open_team_config_page()
            if success: break
        if not success:
            self.logger.error('无法打开队伍配置页面')
            return False

        try: success = self.click_if_appear(self.gc.icon_team_selector, timeout=0.5)
        except TimeoutError: success = False

        return success

    def team_selector_scroll_to_top(self):
        """
        移动到顶部
        :return:
        """
        # 需要先将鼠标移动到选择列表内，否则无法滚动
        time.sleep(0.2)
        pos = (150, self.gc.h / 2)
        sc_pos = self.gc.get_screen_position(pos)
        self.set_ms_position(sc_pos)
        time.sleep(1)
        self.zoom_in(100)

    def team_selector_next_group(self):
        """
        经过测试，60帧数下，10滚轮量大约一个队伍, 40则4个队伍
        只能在选择器打开的时候操作
        :return:
        """
        # 将4个队伍滚到上面
        self.zoom_out(40)


    def click_target_team(self, team_alias):
        """
        点击目标队伍
        :param team_alias:
        :return:
        """
        success = False
        ocr_results = self.ocr.find_match_text(team_alias)
        for ocr_result in ocr_results:
            center = ocr_result.center
            ocr_result.center = (center[0], center[1] + 50)
            self.ocr.click_ocr_result(ocr_result)
            success = True
        return success

    def switch_team(self, fight_team):
        from controller.FightController import FightController


        # 解析队伍名称
        try: team_alias = FightController.get_teamname_from_string(fight_team)
        except Exception as e:
            raise TeamNotFoundException(f"{fight_team}无法解析队伍简称!")

        if len(team_alias.strip()) == 0:
            raise TeamNotFoundException(f"{fight_team}队伍未设置简称，无法切换,请在括号内写入队伍简称!")
        target_team = team_alias

        if TeamUIController.last_selected_team == fight_team:
            return

        # 如果发现仍然在战斗状态，则回七天神像后再切换队伍
        from controller.MapController2 import MapController
        mpc = MapController()
        if FightController(None).has_enemy(): mpc.go_to_seven_anemo_for_revive()

        # 如果发现无法打开页面，则去七天神像后再尝试
        if not self.open_team_selector():
            self.logger.error("无法打开配置页面，尝试前往七天神像后再尝试")
            mpc.go_to_seven_anemo_for_revive()
            if not self.open_team_selector():
                raise TimeoutError("仍然无法打开队伍配置页面, 抛出超时异常")
        self.team_selector_scroll_to_top()
        time.sleep(0.5)
        success = self.click_target_team(target_team)
        start_wait = time.time()
        while not success and time.time() - start_wait < 10:
            self.team_selector_next_group()
            time.sleep(0.5)
            success = self.click_target_team(target_team)
        if success:
            self.log(f'成功选择{target_team}')
            self.ocr.find_text_and_click('确认')
            time.sleep(0.8)
            self.ocr.find_text_and_click('出战')
            self.last_selected_team = fight_team
        else:
            msg =f'超时失败:{target_team}'
            self.logger.error(msg)
            raise TeamNotFoundException(msg)



if __name__ == '__main__':
    # tui = TeamUIController()
    # tui.navigation_to_world_page()
    # target_team = '钟离_芙宁娜_枫原万叶_流浪者_(钟芙万流).txt'
    # target_team = '纳西妲_钟离_芙宁娜_枫原万叶_(采集队).txt'
    # tui.switch_team(target_team)
    # tui.navigation_to_world_page()
    uic = UIController()
    # uic.navigate_to_adventure_handbook_page()
    uic.navigation_to_world_page()
