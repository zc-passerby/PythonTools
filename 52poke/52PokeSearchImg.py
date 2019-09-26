#! /usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import time
import urllib

from PIL import Image

from selenium import webdriver

# 设置Chrome启动参数
option = webdriver.ChromeOptions()
# 把chrome设置成无界面模式，不论windows还是linux都可以，自动适配对应参数
option.headless = True
option.add_argument('--no-sandbox')
# option.add_argument('--window-size=1980,1080')  # 指定浏览器窗口大小
option.add_argument('-start-maximized') # 浏览器窗口最大化
option.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
option.add_argument('--hide-scrollbars')  # 隐藏滚动条, 应对一些特殊页面
# 此步骤很重要，设置为开发者模式，防止被各大网站识别出来使用了Selenium
option.add_experimental_option("excludeSwitches", ["ignore-certificate-errors", "enable-automation"])
# 启动Chrome
browser = webdriver.Chrome('./chromedriver', options=option)
HomeUrl = 'https://wiki.52poke.com/wiki/'
# 打开第一个宝可梦位置
quoteName = urllib.quote('妙蛙种子')
firstPokemonUrl = HomeUrl + quoteName
browser.get(firstPokemonUrl)
while True:
    # 获取宝可梦名称
    pokemonName = browser.find_element_by_tag_name('h1').text.strip().encode('utf8')
    print pokemonName
    # 获取下一个宝可梦的超链接
    # nextPokemonButton = browser.find_element_by_class_name('roundybr-25').find_element_by_tag_name('a')
    nextPokemonButton = browser.find_elements_by_css_selector('.prenxt-nav > tbody > tr > td > table > tbody > tr > td > a')[-1]
    # print nextPokemonButton.text.encode('utf8')
    evolveImgFileName = 'evolveImg/{}.png'.format(pokemonName)
    megaEvolveImgFileName = 'megaEvolveImg/{}.png'.format(pokemonName)
    # 获取当前页面地址
    currentUrl = browser.current_url.encode('utf8')
    # 获取进化节点
    try:
        browser.find_element_by_id('.E8.BF.9B.E5.8C.96')
        # 获取进化元素的大小
        evolveElement = browser.find_element_by_xpath(
            '//span[@id=".E8.BF.9B.E5.8C.96"]/../following-sibling::table[1]/tbody')
        width = evolveElement.size['width']
        height = evolveElement.size['height']
        # print width, height
        # 设置窗口大小
        browser.set_window_size(width + 320, height + 40)
        # 转到进化节点
        evolvePageUrl = currentUrl + '#.E8.BF.9B.E5.8C.96'
        browser.get(evolvePageUrl)
        time.sleep(2)  # 暂停2s等待图片加载完成
        # 重新设置窗口大小后，元素大小会出现偏差
        evolveElement = browser.find_element_by_xpath(
            '//span[@id=".E8.BF.9B.E5.8C.96"]/../following-sibling::table[1]/tbody')
        widthOffset = (evolveElement.size['width'] - width) / 2
        heightOffset = (evolveElement.size['height'] -height) / 2
        print '进化偏移', widthOffset, heightOffset
        # 进行截图和图片处理
        browser.save_screenshot(evolveImgFileName)
        im = Image.open(evolveImgFileName)
        im = im.crop((235 - widthOffset, 21 - heightOffset, im.size[0] - 73 + widthOffset, im.size[1] - 8 + heightOffset))
        im.save(evolveImgFileName)
        # 图片压缩
        os.popen('cd /home/zhangchao/PythonTools/52poke/evolveImg;optipng {}.png >/dev/null 2>&1'.format(pokemonName))
    except:
        print '无进化路径'
    # 获取超级进化节点
    try:
        browser.find_element_by_id('.E8.B6.85.E7.B4.9A.E9.80.B2.E5.8C.96')
        megaEvolveElement = browser.find_element_by_xpath(
            '//span[@id=".E8.B6.85.E7.B4.9A.E9.80.B2.E5.8C.96"]/../following-sibling::table[1]/tbody')
        width = megaEvolveElement.size['width']
        height = megaEvolveElement.size['height']
        # print width, height
        # 设置窗口大小
        browser.set_window_size(width + 320, height + 40)
        # 转到超级进化节点
        megaEvolvePageUrl = currentUrl + '#.E8.B6.85.E7.B4.9A.E9.80.B2.E5.8C.96'
        browser.get(megaEvolvePageUrl)
        time.sleep(2)  # 暂停2s等待图片加载完成
        # 重新设置窗口大小后，元素大小会出现偏差
        megaEvolveElement = browser.find_element_by_xpath(
            '//span[@id=".E8.B6.85.E7.B4.9A.E9.80.B2.E5.8C.96"]/../following-sibling::table[1]/tbody')
        widthOffset = (evolveElement.size['width'] - width) / 2
        heightOffset = (evolveElement.size['height'] - height) / 2
        # print evolveElement.size['width'], evolveElement.size['height']
        print '超级进化偏移', widthOffset, heightOffset
        # 进行截图和图片处理
        browser.save_screenshot(megaEvolveImgFileName)
        im = Image.open(megaEvolveImgFileName)
        im = im.crop((235, 17, im.size[0] - 73, im.size[1] - 12))
        im.save(megaEvolveImgFileName)
        # 图片压缩
        os.popen('cd /home/zhangchao/PythonTools/52poke/megaEvolveImg;optipng {}.png >/dev/null 2>&1'.format(pokemonName))
    except:
        print '无超级进化路径'
    # 点击解析下一个宝可梦
    nextPokemonButton.click()

    # browser.get_screenshot_as_file('./abc2.png')
browser.quit()
