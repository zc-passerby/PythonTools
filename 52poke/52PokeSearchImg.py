#! /usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys
import time
import traceback
import urllib
import platform

from PIL import Image

from selenium import webdriver


def getPokemonImage(browser, linkElement, cropPosition, imageFileName, repair=False):
    try:
        # 获取目的元素以及大小
        targetId = linkElement.get_attribute('href').split('#')[-1]
        targetElement = browser.find_element_by_xpath(
            '//span[@id="{}"]/../following-sibling::table[1]/tbody'.format(targetId))
        width = targetElement.size['width']
        height = targetElement.size['height']
        # print width, height
        # 设置窗口大小
        browser.set_window_size(width + 320, height + 40)
        # 转到链接节点
        # linkElement.click()
        browser.get(linkElement.get_attribute('href'))
        time.sleep(2)  # 暂停2s等待图片加载完成
        # 重新设置窗口大小后，元素大小可能会出现偏差，根据repair参数来确定是否要修复偏差
        targetElement = browser.find_element_by_xpath(
            '//span[@id="{}"]/../following-sibling::table[1]/tbody'.format(targetId))
        # print targetElement.size['width'], targetElement.size['height']
        widthOffset = (targetElement.size['width'] - width) / 2
        # heightOffset = (targetElement.size['height'] - height) / 2
        heightOffset = targetElement.size['height'] - height
        if repair:
            cropPosition = (cropPosition[0] - widthOffset, cropPosition[1],
                            cropPosition[2] - widthOffset, cropPosition[3] - heightOffset)
        print '{}偏移: ({}, {})'.format(linkElement.text.encode('utf8').split(' ')[-1].strip(), widthOffset, heightOffset)
        # 进行截图和图片处理
        browser.get_screenshot_as_file(imageFileName)
        im = Image.open(imageFileName)
        im = im.crop(
            (cropPosition[0], cropPosition[1], im.size[0] - cropPosition[2], im.size[1] - cropPosition[3]))
        im.save(imageFileName)
        # 图片压缩，仅针对linux
        if platform.system() == 'Linux':
            os.popen(
                'optipng {}/{} >/dev/null 2>&1'.format(os.getcwd(), imageFileName))
    except:
        print '[ERROR]获取{}信息失败！'.format(linkElement.text.encode('utf8').split(' ')[-1].strip())
        with open('images/errorLog', 'ab') as fOut:
            fOut.write("{} {}\n".format(imageFileName, linkElement.text.encode('utf8').split(' ')[-1].strip()))


def getPokemonEvolve(browser, pokemonName, evolveLink, megaEvolveLink, transformEvolveLink):
    # 进化
    if evolveLink:
        cropPosition = (235, 21, 73, 8)
        imageFileName = 'images/evolveImg/{}.png'.format(pokemonName)
        getPokemonImage(browser, evolveLink, cropPosition, imageFileName, True)
    # 超级进化
    if megaEvolveLink:
        cropPosition = (235, 18, 73, 11)
        imageFileName = 'images/megaEvolveImg/{}.png'.format(pokemonName)
        getPokemonImage(browser, megaEvolveLink, cropPosition, imageFileName)
    # 形态变化
    if transformEvolveLink:
        cropPosition = (235, 21, 73, 8)
        imageFileName = 'images/transformImg/{}.png'.format(pokemonName)
        getPokemonImage(browser, transformEvolveLink, cropPosition, imageFileName)


def getCropImage(**kwargs):
    browser = kwargs['browser']
    cropElement = kwargs['cropElement']
    cropLink = kwargs['cropLink']
    cropPosition = kwargs['cropPosition']
    imageFileName = kwargs['imageFileName']
    cssSelector = kwargs['cssSelector']
    position = kwargs.get('position', 0)
    tryRepair = kwargs.get('tryRepair', 0)
    # repair = kwargs.get('repair', False)
    try:
        targetElement = cropElement.find_elements_by_css_selector(cssSelector)[position]
        width = targetElement.size['width']
        height = targetElement.size['height']
        print width, height
        # 设置窗口大小
        # browser.set_window_size(width + 320, height + 300)
        # 转到链接节点
        # linkElement.click()
        browser.get(cropLink.get_attribute('href'))
        time.sleep(2)  # 暂停2s等待图片加载完成
        # 重新设置窗口大小后，元素大小可能会出现偏差，根据repair参数来确定是否要修复偏差
        # targetElement = cropElement.find_elements_by_css_selector(cssSelector)[position]
        # print targetElement.size['width'], targetElement.size['height']
        # widthOffset = (targetElement.size['width'] - width) / 2
        # # heightOffset = (targetElement.size['height'] - height) / 2
        # heightOffset = targetElement.size['height'] - height
        # if repair:
        #     cropPosition = (cropPosition[0] - widthOffset, cropPosition[1],
        #                     cropPosition[2] - widthOffset, cropPosition[3] - heightOffset)
        # print '{}偏移: ({}, {})'.format(cropLink.text.encode('utf8').split(' ')[-1].strip(), widthOffset,
        #                               heightOffset)
        if tryRepair:
            tryRepair = (width - 750) / 2
        # 进行截图和图片处理
        browser.get_screenshot_as_file(imageFileName)
        im = Image.open(imageFileName)
        im = im.crop((cropPosition[0] - tryRepair, cropPosition[1], cropPosition[2] + width -tryRepair, cropPosition[3] + height))
        im.save(imageFileName)
        # 图片压缩，仅针对linux
        if platform.system() == 'Linux':
            os.popen(
                'optipng "{}/{}" >/dev/null 2>&1'.format(os.getcwd(), imageFileName))
    except:
        print '[ERROR]获取信息失败！{}'.format(traceback.format_exc())
        with open('images/errorLog', 'ab') as fOut:
            fOut.write("{} {}\n".format(imageFileName, cropLink.text.encode('utf8').split(' ')[-1].strip()))


def getPokemonSpeciesStrength(browser, pokemonName, speciesStrengthLink):
    if not speciesStrengthLink: return
    try:
        browser.set_window_size(1366, 768)
        # 获取目的元素以及大小
        targetId = speciesStrengthLink.get_attribute('href').split('#')[-1]
        speciesElement = browser.find_element_by_xpath(
            '//span[@id="{}"]/../following-sibling::*'.format(targetId))
        tabElementList = speciesElement.find_elements_by_css_selector("div > ul > li")
        dParams = {
            'browser': browser,
            'cropElement': speciesElement,
            'cropLink': speciesStrengthLink,
            'cssSelector': 'table.roundy.alignt-center > tbody'
        }
        if len(tabElementList) == 0:
            dParams['cropPosition'] = (199, 16, 210, 28)
            dParams['imageFileName'] = 'images/speciesStrength/{}.png'.format(pokemonName)
            getCropImage(**dParams)
        else:
            for pos, tabElement in enumerate(tabElementList):
                tabElement.click()
                dParams['position'] = pos
                dParams['cropPosition'] = (205, 60, 216, 72)
                dParams['imageFileName'] = 'images/speciesStrength/{}_{}.png'.format(pokemonName,
                                                                                      tabElement.text.encode('utf8'))
                getCropImage(**dParams)
    except:
        print '[ERROR]获取信息失败！{}'.format(traceback.format_exc())


def getPokemonTypeOpposite(browser, pokemonName, TypeOppositeLink):
    if not TypeOppositeLink: return
    try:
        browser.set_window_size(1366, 768)
        # 获取目的元素以及大小
        targetId = TypeOppositeLink.get_attribute('href').split('#')[-1]
        typeElement = browser.find_element_by_xpath(
            '//span[@id="{}"]/../following-sibling::*'.format(targetId))
        tabElementList = typeElement.find_elements_by_css_selector("div > ul > li")
        dParams = {
            'browser': browser,
            'cropElement': typeElement,
            'cropLink': TypeOppositeLink,
            'cssSelector': 'table.roundy > tbody'
        }
        for pos, tabElement in enumerate(tabElementList):
            tabElement.click()
            dParams['position'] = pos
            dParams['tryRepair'] = 1
            # dParams['cropPosition'] = (245, 63, 66, 125)
            dParams['cropPosition'] = (392, 64, 401, 73) # 剑盾
            dParams['imageFileName'] = 'images/typeOpposite/{}_{}.png'.format(pokemonName,
                                                                              tabElement.text.encode('utf8'))
            getCropImage(**dParams)
    except:
        print "error:{}".format(traceback.format_exc())


def parsePokemon(browser, quoteName, bSingle):
    HomeUrl = 'https://wiki.52poke.com/wiki/'
    # 打开第一个宝可梦位置
    firstPokemonUrl = HomeUrl + quoteName
    browser.get(firstPokemonUrl)
    while True:
        # 获取宝可梦名称
        pokemonName = browser.find_element_by_tag_name('h1').text.strip()
        print '===================={}===================='.format(pokemonName.encode('utf8'))
        # 获取下一个宝可梦的超链接
        nextPokemonButton = \
            browser.find_elements_by_css_selector('.prenxt-nav > tbody > tr > td > table > tbody > tr > td > a')[-1]
        # print nextPokemonButton.text.encode('utf8')
        pokemonName = pokemonName.encode('utf8')
        # windows中用utf8中文为文件名的话无法保存文件
        if platform.system() == 'Windows': pokemonName = pokemonName.decode('utf8').encode('gb2312')
        # 获取目录中的链接，目前使用进化、超级进化、形态变化、种族值
        evolveLink, megaEvolveLink, transformEvolveLink = None, None, None
        speciesStrengthLink, TypeOppositeLink = None, None
        aTagList = browser.find_elements_by_xpath('//div[@id="toc"]//a')
        for aTag in aTagList:
            aTagText = aTag.text.encode('utf8').split(' ')[-1].strip()
            if aTagText == '进化' or aTagText == '進化':
                evolveLink = aTag
            elif aTagText == '超级进化' or aTagText == '超級進化':
                megaEvolveLink = aTag
            elif aTagText == '形态变化' or aTagText == '形態變化':
                transformEvolveLink = aTag
            elif aTagText == '种族值' or aTagText == '種族值':
                speciesStrengthLink = aTag
            elif aTagText == '属性相性' or aTagText == '屬性相性':
                TypeOppositeLink = aTag

        if evolveLink: print evolveLink.get_attribute('href').split('#')[-1]
        if megaEvolveLink: print megaEvolveLink.get_attribute('href').split('#')[-1]
        if transformEvolveLink: print transformEvolveLink.get_attribute('href').split('#')[-1]
        getPokemonEvolve(browser, pokemonName, evolveLink, megaEvolveLink, transformEvolveLink)
        getPokemonSpeciesStrength(browser, pokemonName, speciesStrengthLink)
        getPokemonTypeOpposite(browser, pokemonName, TypeOppositeLink)
        # 若仅解析单个宝可梦，则不需要进入下个宝可梦页面
        if bSingle: break
        # 点击解析下一个宝可梦
        nextPokemonButton.click()


def mainEntrance(pokemonName='', bSingle=True):
    # 若未设定宝可梦，则默认为妙蛙种子，并继续解析
    # 若设置了宝可梦，则默认解析单个宝可梦
    if pokemonName == '':
        pokemonName = '妙蛙种子'
        bSingle = False
    # 设置Chrome启动参数
    option = webdriver.ChromeOptions()
    # 把chrome设置成无界面模式，不论windows还是linux都可以，自动适配对应参数
    option.headless = True
    option.add_argument('--no-sandbox')
    # option.add_argument('--window-size=1366,768')  # 指定浏览器窗口大小
    option.add_argument('-start-maximized')  # 浏览器窗口最大化
    option.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
    option.add_argument('--hide-scrollbars')  # 隐藏滚动条, 应对一些特殊页面
    # 此步骤很重要，设置为开发者模式，防止被各大网站识别出来使用了Selenium
    option.add_experimental_option("excludeSwitches", ["ignore-certificate-errors", "enable-automation"])
    # 启动Chrome
    browser = webdriver.Chrome('./chromedriver', options=option)
    try:
        quoteName = urllib.quote(pokemonName)
        parsePokemon(browser, quoteName, bSingle)
    except:
        print "some error occurs:\n", traceback.format_exc()
    finally:
        browser.close()
        browser.quit()


if __name__ == '__main__':
    args = len(sys.argv)
    # 若无输入参数，则执行默认解析
    # 若有一个输入参数，则执行解析单个宝可梦
    # 若有两个参数，第一个参数必须为FILE(file)/START(start)
    #   FILE: 第二个参数为文件名，文件中列出所有要解析的宝可梦，一行一个，UTF8格式
    #   START: 第二个参数为宝可梦名，表示从该宝可梦开始解析
    if args <= 1:
        mainEntrance()
    elif args == 2:
        mainEntrance(sys.argv[1])
    elif args >= 3:
        mode = sys.argv[1].upper()
        content = sys.argv[2]
        if mode not in ['FILE', 'START']:
            print "Usage: python {} [pokemonName] | [file fileName] | [start pokemonName]".format(sys.argv[0])
            exit(0)
        if mode == "FILE":
            with open(content, 'rb') as fIn:
                pokemonList = fIn.readlines()
                for pokemonName in pokemonList:
                    mainEntrance(pokemonName.strip())
        elif mode == "START":
            mainEntrance(content, False)
