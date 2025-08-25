# -*- coding: utf-8 -*-
"""
安卓手机操控
"""
import logging
import uiautomator2 as u2
import time
import os
import random
import cv2
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import configs
from Infra import util
class AndroidController:
    """
    安卓手机控制
    """
    def __init__(self, port):
        self.device = u2.connect_usb(port)
        self.upperbar = 0
        self.subbar = 0
        self.sleep_time = 0.1
        if not self.device:
            logging.error('init Android opr failed!')
        else:
            logging.info('init Android opr success!')
        # self.device.set_fastinput_ime(True)
        self.screen_width = 0
        self.screen_height = 0
        self.event_index = 0

    def set_screen_size(self):
        # 获取设备信息
        info = self.device.info

        # 获取屏幕尺寸
        self.screen_width = info['displayWidth']
        self.screen_height = info['displayHeight']


    def start_app(self, app_pkg_name,wait=2):
        """
        启动app
        :param app_pkg_name:
        :return:
        """
        # 每次打开前先关闭，同时保证处在消息界面
        try:
            self.stop_app(app_pkg_name)
        except:
            pass
        self.device.app_start(app_pkg_name)
        logging.debug('start app begin...')
        time.sleep(wait)
        # self.device.set_fastinput_ime(True)
        logging.debug('start app end...')


    def stop_app(self, app_pkg_name):
        """
        app杀进程
        :param app_pkg_name:
        :return:
        """
        self.device.app_stop(app_pkg_name)

    def click(self, x, y,wait_time = 0.1):
        self.screenshot_with_simple_annotation(configs.run_output_path+ str(self.event_index) + ".png", "tap_hold", x , y)
        self.event_index += 1

        """
        点击坐标（x,y）
        :param x:
        :param y:
        :return:
        """
        if(x<0 and y < 0):
            self.back()
            return
        self.device.click(int(x), int(y)+self.upperbar)
        time.sleep(wait_time)






    def home(self):
        self.screenshot_with_simple_annotation(configs.run_output_path + str(self.event_index) + ".png", "home")
        self.event_index += 1

        """
        home键
        :return:
        """
        self.device.press("home")

    def back(self):
        self.screenshot_with_simple_annotation(configs.run_output_path + str(self.event_index) + ".png", "back")
        self.event_index += 1

        """
        返回键
        :return:
        """
        self.device.press("back")
        time.sleep(self.sleep_time)

    def tap_hold(self, x, y, t):
        self.screenshot_with_simple_annotation(configs.run_output_path + str(self.event_index) + ".png", "tap_hold",x , y)
        self.event_index += 1

        """
        长按,持续t秒
        :param x:
        :param y:
        :param t:
        :return:
        """
        self.device.long_click(int(x), int(y)+self.upperbar, t)
        time.sleep(self.sleep_time)

    def vertical_scroll(self,start=250,end=1000,direction = 0):
        self.screenshot_with_simple_annotation(configs.run_output_path + str(self.event_index) + ".png", "vertical_scroll")
        self.event_index += 1

        if direction==1:
            self.swipe(600,start,600,end)
        else:
            self.swipe(600,end,600,start)

    def horizontal_scroll(self,start = 20,end = 1000,pos=500,direction = 2):
        self.screenshot_with_simple_annotation(configs.run_output_path + str(self.event_index) + ".png", "horizontal_scroll")
        self.event_index += 1

        if direction==1:
            self.swipe(start,pos,end,pos)
        else:
            self.swipe(end,pos,start,pos)

    def swipe(self,fx,fy,tx,ty,steps=40):
        self.device.swipe(int(fx),int(fy),int(tx),int(ty),steps=steps)
        time.sleep(self.sleep_time)

    def input(self, text = "PKU", clear=True):
        self.screenshot_with_simple_annotation(configs.run_output_path + str(self.event_index) + ".png", "input: " + text)
        self.event_index += 1

        try:
            # TODO: deal with clear here
            text = text.replace(" ","\ ")
            # os.system("adb shell input text \"{}\"".format(text))
            util.adb_text("\"{}\"".format(text))
            time.sleep(0.2)
            # self.device.send_keys(text,clear=clear)
        except:
            return False
        return True

    def capture_screen(self):
        """
        截屏
        :return:
        """
        image = self.device.screenshot(format='opencv')
        image = image[self.upperbar:] # shiver the task bar
        return image
        
    def screenshot_with_simple_annotation(self, save_path, text, x=0, y=0):
        """
        使用 uiautomator2 截图并在指定位置添加标注文本
        
        :param device_port: 设备的 USB 端口或设备 ID（字符串）
        :param save_path: 保存截图的本地路径（字符串）
        :param x: 标注文本的 x 坐标
        :param y: 标注文本的 y 坐标
        :param text: 要标注的文本（字符串）
        """
        try:
            # 获取文件路径中的目录部分
            directory = os.path.dirname(save_path)
            
            # 如果目录不存在，则创建目录
            if not os.path.exists(directory):
                os.makedirs(directory)

            # 获取截图字节流
            screenshot_bytes = self.device.screenshot()
            
            # 如果 screenshot_bytes 是一个字节流，而不是图像对象，则通过 Image.open 转换
            if isinstance(screenshot_bytes, bytes):
                image = Image.open(io.BytesIO(screenshot_bytes))  # 将字节流转为 Image 对象
            else:
                image = screenshot_bytes  # 如果已经是 Image 对象，直接使用
            
            # 创建 ImageDraw 对象，用于在图像上绘制
            draw = ImageDraw.Draw(image)
            
            # 设置字体（如果没有字体文件，使用默认字体）
            try:
                font = ImageFont.truetype("arial.ttf", size=48)
            except IOError:
                font = ImageFont.load_default()
            
            # 在指定位置添加标注文本
            draw.text((x, y), text, font=font, fill="red")  # 颜色为红色，你可以根据需要修改
            
            # 保存标注后的截图
            image.save(save_path)
            
            print(f"截图已保存并标注到: {save_path}")
        except Exception as e :
            print(e)

    def dump(self):
        return self.device.dump_hierarchy()
    def app_info(self):
        CurApp = self.device.app_current()
        return CurApp['package'],CurApp['activity']

if __name__ == "__main__":
    print(AndroidController("emulator-5554").dump())
