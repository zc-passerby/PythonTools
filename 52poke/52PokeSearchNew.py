#! /usr/bin/env python
# -*- coding=utf-8 -*-

import sys
import requests
import urllib
import json
from bs4 import BeautifulSoup

websiteBase = "http://wiki.52poke.com"
websiteHome = "http://wiki.52poke.com/wiki/" \
              + "%E5%AE%9D%E5%8F%AF%E6%A2%A6%E5%88%97%E8%A1%A8%EF%BC%88%E6%8C" \
              + "%89%E5%85%A8%E5%9B%BD%E5%9B%BE%E9%89%B4%E7%BC%96%E5%8F%B7%EF%BC%89"


class SinglePokemonPage:
    def __init__(self, soup, pokemonCardTag, sightName='', sightPosition=0):
        self.soup = soup
        self.pokemonCardTag = pokemonCardTag
        self.sightName = sightName
        self.sightPosition = sightPosition - 1

    # 获取宝可梦的名字，包含中文名、日文名、英文名，其中有多形态的，中文名为宝可梦名称【形态名】，如：妙蛙花【超级妙蛙花】
    def getName(self):
        nameTagList = self.pokemonCardTag.select('.textblack.bgwhite > span > b')
        nameTagList += self.pokemonCardTag.select('.textblack.bgwhite > b')
        if len(nameTagList) < 3: return ('未命名', '未命名', '未命名')
        nameZh = nameTagList[0].text
        if self.sightName: nameZh = nameZh + u'【' + self.sightName + u'】'
        nameJp = nameTagList[1].text
        nameEn = nameTagList[2].text
        return (nameZh.encode('utf8'), nameJp.encode('utf8'), nameEn.encode('utf8'))

    # 获取宝可梦图片的Url，后续考虑将图片下载下来
    # 另外，有些宝可梦会有多张图片，后续再考虑处理
    def getImage(self):
        imageTagList = self.pokemonCardTag.select('.roundy.bgwhite.fulltable > tbody > tr > td > div > a.image > img')
        imageTagList += self.pokemonCardTag.select('.roundy.bgwhite.fulltable > tbody > tr > td > a.image > img')
        imageUrl = 'http:' + imageTagList[0]['data-url']
        imageUrl = imageUrl.replace('300px', '120px')  # 获取120像素的图片
        return imageUrl.encode('utf8')

    # 获取宝可梦图鉴编号，包含全国图鉴编号和各地区的图鉴编号
    # 全国图鉴编号是从pokemonCardTag里直接获取的，地区编号是从信息容器中获取
    def getSn(self, jarTag):
        snDict = {}
        # 全国图鉴编号
        NationalSn = self.pokemonCardTag.select('.textblack.bgwhite > a')[0].text.lstrip('#').encode('utf8')
        snDict['全国'] = NationalSn
        # 地区图鉴编号
        trTagList = jarTag.select('.roundy.bgwhite.fulltable.textblack > tbody > tr')
        for trTag in trTagList:
            # 若是trTag是hide属性，则无需处理
            if trTag.has_attr('class') and len(trTag['class']) > 0 and trTag['class'][0] == 'hide': continue
            tdTagList = trTag.select('td')
            # 若tdTag数量少于1，则无需处理
            if len(tdTagList) <= 1: continue
            # 获取地区名称
            region = tdTagList[0].text.strip().encode('utf8')
            for i, tdTag in enumerate(tdTagList):
                if i == 0: continue  # 地区名称已经处理过了
                if tdTag.has_attr('class') and 'hide' in tdTag['class']: continue
                targetSn = tdTag.text.strip().strip('#').encode('utf8')
                if snDict.get(region, None):
                    snDict[region] = snDict[region] + '/' + targetSn
                else:
                    snDict[region] = targetSn
        return snDict

    def run(self):
        nameTuple = self.getName()
        print nameTuple[0], nameTuple[1], nameTuple[2]
        imageUrl = self.getImage()
        # print urllib.unquote(imageUrl)
        # jarTagList 中包含各种宝可梦信息
        # 属性、分类、特性、100级时经验值、地区图鉴编号、地区浏览器编号
        # 身高、体重、体形、脚印、图鉴颜色、捕获率、性别比例、培育、取得基础点数、旁支系列
        jarTagList = self.pokemonCardTag.select('table.roundy.bw-1.fulltable > tbody > tr > td')
        for jarTag in jarTagList:
            if not jarTag.b: continue  # 若不存在b标签，则无需解析
            bTagText = jarTag.b.text  # 每个信息容器代表的宝可梦的信息的类型
            if bTagText == u'地区图鉴编号':
                dPokemonSn = self.getSn(jarTag)
                for k, v in dPokemonSn.iteritems():
                    print k, v


def handlePokemonPage(pokemonPage):
    # 获取目标宝可梦页
    soup = BeautifulSoup(pokemonPage.text, 'lxml')
    # 右上角宝可梦信息卡片，包含宝可梦名称，图片，属性，分类，特性，全国图鉴编号，地区图鉴编号
    # 身高，体重，体形，脚印，图鉴颜色，捕获率，性别比例，蛋群，孵化周期，对战获得的努力值和经验
    # 若为属性页或多形态宝可梦，则该卡片是属性列表或多形态列表
    pokemonCardTagList = soup.select('#bodyContent > #mw-content-text > .mw-parser-output > .roundy.a-r.at-c')
    if len(pokemonCardTagList) == 0: return
    pokemonCardTag = pokemonCardTagList[0]
    # 判断宝可梦是否为多形态（mega、不同颜色、原始的样子等）
    attrTagList = pokemonCardTag.select('tr > th')
    if len(attrTagList) == 0: return  # 非宝可梦页
    if attrTagList[0].a.text == u'属性列表':
        return
    elif attrTagList[0].a.text == u'形态':
        sightPosition = 0
        for sight in attrTagList:
            sightText = sight.text.strip('\n')
            if sightText and sightText != u'形态':
                sightPosition += 1
                targetPokemonCardTag = soup.select('tr._toggle.form' + str(sightPosition))[0]
                pokemon = SinglePokemonPage(soup, targetPokemonCardTag, sightText, sightPosition)
                pokemon.run()
    else:
        pokemon = SinglePokemonPage(soup, pokemonCardTag)
        pokemon.run()


def mainEntrance():
    homePage = requests.get(websiteHome)
    soup = BeautifulSoup(homePage.text, 'lxml')
    pokemonTagList = soup.select(
        '.mw-body-content > .mw-content-ltr > .mw-parser-output > .eplist > tbody > tr > td > a')

    for pokemonUrlTag in pokemonTagList:
        pokemonUrl = websiteBase + pokemonUrlTag['href']

        pokemonPage = None
        while True:
            try:
                pokemonPage = requests.get(pokemonUrl)
                break
            except:
                continue

        if not pokemonPage: continue
        handlePokemonPage(pokemonPage)
        sys.stdout.flush()
        # break


if __name__ == '__main__':
    mainEntrance()
