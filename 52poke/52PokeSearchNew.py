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

    def run(self):
        nameTuple = self.getName()
        print nameTuple[0], nameTuple[1], nameTuple[2]
        imageUrl = self.getImage()
        print urllib.unquote(imageUrl)


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
