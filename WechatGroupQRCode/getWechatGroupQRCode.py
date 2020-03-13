#! /usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import re
import sched
import sys
import time
import traceback
from datetime import datetime
from io import BytesIO

import requests
from PIL import Image
from bs4 import BeautifulSoup
from pyzbar.pyzbar import decode
from requests.packages import urllib3

import dbHandler

# image_path = './image/'
image_path = '/var/www/callcenter/frontend/web/static/wechatqrcode/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'
}

# 间隔执行时间
delay_seconds = 60 * 60
# 二维码有效期，暂时设为7天
qrcode_valid_time = 7 * 24 * 3600
# 过期二维码的数量，超过数量就
qrcode_max_expired_count = 120
# 屏蔽requests使用verify=False所给出的警告信息
urllib3.disable_warnings()
# 全局sqlite连接
# sqliteConn = dbHandler.ObjSqliteConnector("./wechatGroupQrcode.db3")
# 全局Mysql连接
mysqlConn = dbHandler.connectMysql()
# 时间格式匹配
str_time_pattern = re.compile('(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})')


def intTime2Str(unix_timestamp):
    if unix_timestamp < 0: unix_timestamp = 0
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(unix_timestamp))


def strTime2Int(str_time):
    str_time = str(str_time)
    if not str_time_pattern.match(str_time):
        return int(time.time())
    tmp_list = str_time_pattern.search(str_time).groups()
    return int(time.mktime(datetime(*map(int, tmp_list)).timetuple()))


def getResponseAndSoup(target_url, encoding, get_soup=True):
    response, soup = None, None
    try:
        if target_url:
            response = requests.get(target_url, headers=headers, timeout=30, verify=False)
            # 设置编码，在使用response.text时，自动联想编码，如果自动联想出错的话，会导致Unicode无法解码
            response.encoding = encoding
            if get_soup:
                soup = BeautifulSoup(response.text, 'lxml')
    except Exception:
        response, soup = None, None
        print "some errors occurred : %s" % traceback.format_exc()
    return (response, soup)


class ScheduleBase:
    schedule = sched.scheduler(time.time, time.sleep)
    secondsDelay = 60 * 60  # 默认60分钟执行一次

    def doTaskMain(self):
        pass

    def performTask(self, delay):
        # self.schedule.enter(delay, 0, self.performTask, (delay,));  # re-schedule
        self.doTaskMain()

    def run(self):
        delay = 0
        self.schedule.enter(delay, 0, self.performTask, (self.secondsDelay,))  # delay=0：立即执行
        self.schedule.run()


class ParseWebsite(ScheduleBase):
    '''
    获取网站中的微信群二维码数据
    目前只能识别二维码是否为微信二维码
    暂时不能识别群二维码是否有效

    格式：
        群：      weixin.qq.com/g/
        个人：    u.wechat.com/
        公众号：  weixin.qq.com/r/
                 weixin.qq.com/q/
    '''

    def __init__(self):
        self.encoding = 'utf8'
        self.website_name = ''
        self.home_url = ''
        self.home_page_url = ''
        self.group_page_url = ''
        self.table_name = 'wechat_qrcode_info'
        # --------------------------------------------------------------------------------
        self.d_tag_finder = {}
        # --------------------------------------------------------------------------------
        self.qrcode_detail_page_selector = ''
        self.qrcode_image_selector = ''
        self.qrcode_image_create_time_selector = ''
        self.next_page_selector = ''

    def initDataBase(self):
        pass

    def getQrcodeCreateTime(self, page_soup):
        is_valid = True
        current_time_int = int(time.time())
        create_time = intTime2Str(current_time_int)
        tag_list = page_soup.select(self.qrcode_image_create_time_selector)
        for tag in tag_list:
            tag_text = self.d_tag_finder['image_create_time_tag_text']
            if tag_text in tag.text:
                create_time = tag.text.replace(tag_text, '').strip()
        create_time_int = strTime2Int(create_time)
        if current_time_int - create_time_int > qrcode_valid_time:
            is_valid = False
        return is_valid, create_time

    def qrCodeSave(self, image_content, image_filename, qrcode_url_list, create_time):
        try:
            if image_content == '' or len(qrcode_url_list) == 0: return False
            print qrcode_url_list, image_filename
            # 保存图片，并设置所有权为nginx:nginx
            with open(image_filename, 'wb') as f_img:
                f_img.write(image_content)
            # 设置权限
            try:
                print os.popen('chown nginx:nginx ' + image_filename).read()
            except:
                print traceback.format_exc()
            # 将数据写入数据库
            for qrcode_url in qrcode_url_list:
                # dbHandler.InsertWechatQrcodeInfo(sqliteConn, qrcode_url, image_filename, self.website_name, create_time)
                dbHandler.InsertToMysqlDb(mysqlConn, (str(qrcode_url), str(image_filename), str(create_time)))
        except Exception:
            print 'some error occurs: %s' % traceback.format_exc()
            return False
        return True

    def qrCodeRecognize(self, image_resp):
        qrcode_url_list = []
        # 打开二维码
        img = Image.open(BytesIO(image_resp.content))
        # 灰度化
        img = img.convert("L")
        # 对二维码进行解码
        qrcode_info = decode(img)
        # print qrcode_info
        for qrcode in qrcode_info:
            qrcode_url = qrcode.data.decode('utf-8')
            if 'weixin.qq.com/g/' in qrcode_url:
                qrcode_url_list.append(qrcode_url)
        return qrcode_url_list

    def getWeixinQRCode(self, page_url):
        qrcode_saved = False
        target_page, page_soup = getResponseAndSoup(page_url, self.encoding)
        if not page_soup: return
        qunImageTagList = page_soup.select(self.qrcode_image_selector)
        for imageTag in qunImageTagList:
            if imageTag.has_attr('src'):
                image_url = imageTag['src']
                if not self.home_url in image_url: image_url = self.home_page_url + image_url.lstrip('/')
                is_valid, create_time = self.getQrcodeCreateTime(page_soup)
                # print "二维码创建时间：" + str(create_time)
                if is_valid:
                    image_resp, image_soup = getResponseAndSoup(image_url, self.encoding, False)
                    qrcode_url_list = []
                    if image_resp.status_code == 200:
                        qrcode_url_list = self.qrCodeRecognize(image_resp)
                    if len(qrcode_url_list):
                        image_filename = image_path + image_url.split('/')[-1]
                        is_saved = self.qrCodeSave(image_resp.content, image_filename, qrcode_url_list, create_time)
                        if not qrcode_saved: qrcode_saved = is_saved
                    # else:
                    #     print '二维码已过有效期'
        return qrcode_saved

    def getNextPageSoup(self, page_soup):
        next_page_soup = None
        linkTagList = page_soup.select(self.next_page_selector)
        for linkTag in linkTagList:
            if linkTag.text == self.d_tag_finder['next_page_tag_text'] and linkTag['href']:
                next_page_href = linkTag['href']
                if not self.home_url in next_page_href: next_page_href = self.home_page_url + next_page_href.lstrip('/')
                print next_page_href
                next_page, next_page_soup = getResponseAndSoup(next_page_href, self.encoding)
        return next_page_soup

    def doTaskMain(self):
        # group_page = requests.get(self.group_page_url, headers=headers, timeout=30, verify=False)
        # group_page_soup = BeautifulSoup(group_page.text, 'lxml')
        expired_count = 0
        group_page, group_page_soup = getResponseAndSoup(self.group_page_url, self.encoding)
        while True:
            if not group_page_soup: break
            print "失效二维码数：" + str(expired_count)
            if expired_count >= qrcode_max_expired_count: break
            detailPageTagList = group_page_soup.select(self.qrcode_detail_page_selector)
            print len(detailPageTagList)
            for detailPageTag in detailPageTagList:
                if detailPageTag.has_attr('title') and detailPageTag.has_attr('href'):
                    title = detailPageTag.get('title')
                    href = detailPageTag.get('href')
                    if self.home_page_url not in href: href = self.home_page_url + href
                    print title, '===>', href
                    if not self.getWeixinQRCode(href): expired_count += 1
            group_page_soup = self.getNextPageSoup(group_page_soup)


class ParseWxqun(ParseWebsite):
    def __init__(self):
        ParseWebsite.__init__(self)
        self.encoding = 'utf8'
        self.website_name = "wxqun"
        self.home_url = "www.wxqun.com"
        self.home_page_url = "https://www.wxqun.com/"
        self.group_page_url = "https://www.wxqun.com/wxq/p1.html"
        # --------------------------------------------------------------------------------
        self.d_tag_finder['next_page_tag_text'] = u'下一页'
        self.d_tag_finder['image_create_time_tag_text'] = u'时间：'
        # --------------------------------------------------------------------------------
        self.qrcode_detail_page_selector = '.list.clearfix > .show > ul > li > div > a'
        self.qrcode_image_selector = '.w1200.clearfix > .conL > .cl1 > .con_img > p.showcode > span > img'
        self.qrcode_image_create_time_selector = '.w1200.clearfix > .conL > .cl1 > .con_info > ul > li'
        self.next_page_selector = '.pageNo.vm > ul.pagination > li > a'


class ParseChinaRot(ParseWebsite):
    def __init__(self):
        ParseWebsite.__init__(self)
        self.encoding = 'utf8'
        self.website_name = "chinarot"
        self.home_url = "www.chinarot.com"
        self.home_page_url = "https://www.chinarot.com/"
        self.group_page_url = "https://www.chinarot.com/group/"
        # --------------------------------------------------------------------------------
        self.d_tag_finder['next_page_tag_text'] = u'>'
        self.d_tag_finder['image_create_time_tag_text'] = u'来源：微信群'
        # --------------------------------------------------------------------------------
        self.qrcode_detail_page_selector = '.w1200 > .clearfix.bgfff.mt20.bigimg_list > ul#tab_head > li > div.border5 > a'
        self.qrcode_image_selector = '.art_show_right > .subj.cateNav_ny.clearfix > .clearfix > .iframe > .shiftcode > img'
        self.qrcode_image_create_time_selector = '.art_show_right > .subj.cateNav_ny.clearfix > .clearfix > .des_info > .clearfix > ul > .des_info > .clearfix > ul > ul.other-info > li'
        self.next_page_selector = '.w1200 > .pages.pageNo.vm.center > a'


class ParseQunFenXiang(ParseWebsite):
    def __init__(self):
        ParseWebsite.__init__(self)
        self.encoding = 'utf8'
        self.website_name = "qunfenxiang"
        self.home_url = "www.qunfenxiang.net"
        self.home_page_url = "https://www.qunfenxiang.net/"
        self.group_page_url = "https://www.qunfenxiang.net/group/"
        # --------------------------------------------------------------------------------
        self.d_tag_finder['next_page_tag_text'] = u'>'
        self.d_tag_finder['image_create_time_tag_text'] = u'时间：'
        # --------------------------------------------------------------------------------
        self.qrcode_detail_page_selector = '.w1200 > .column.comBorder > .wechat-lg.picShow > ul > li > div.boldBorder a'
        self.qrcode_image_selector = '.code_pic > span.shiftcode > .p1 > p > img'
        self.qrcode_image_create_time_selector = '.code_info > .other-info > ul > li'
        self.next_page_selector = '.w1200 > .column.comBorder div.center a'


class ParseWeixinqun(ParseWebsite):
    def __init__(self):
        ParseWebsite.__init__(self)
        self.encoding = 'utf8'
        self.website_name = "weixinqun"
        self.home_url = "weixinqun.com"
        self.home_page_url = "https://weixinqun.com/"
        self.group_page_url = "https://weixinqun.com/group"
        # --------------------------------------------------------------------------------
        self.d_tag_finder['next_page_tag_text'] = u'>'
        self.d_tag_finder['image_create_time_tag_text'] = u'时间：'
        # --------------------------------------------------------------------------------
        self.qrcode_detail_page_selector = '.w1200 > .clearfix.bgfff.mt20.bigimg_list > ul#tab_head > li > .border5 > a'
        self.qrcode_image_selector = '.code_pic > span.shiftcode > .p1 > p > img'
        self.qrcode_image_create_time_selector = '.code_info > .other-info > ul > li'
        self.next_page_selector = '.pageNo.vm.center > a'


def mainEntrance():
    # 先创建数据表
    # dbHandler.WechatQrcodeInfoBuild(sqliteConn)
    wxqun_parser = ParseWxqun()
    wxqun_parser.run()
    # dbHandler.SyncSqliteToMysql(sqliteConn)
    chinarot_parser = ParseChinaRot()
    chinarot_parser.run()
    qunfenxiang_parser = ParseQunFenXiang()
    qunfenxiang_parser.run()
    # weixinqun_parser = ParseWeixinqun()
    # weixinqun_parser.run()
    dbHandler.closeMysql(mysqlConn)


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    try:
        # 创建存放文件的路径
        print os.makedirs(image_path)
        print os.popen('chown -R nginx:nginx ' + image_path).read()
    except Exception:
        pass
    while True:
        mainEntrance()
        time.sleep(delay_seconds)
