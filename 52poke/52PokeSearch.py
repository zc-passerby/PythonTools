#! /usr/bin/env python
#-*- coding=utf-8 -*-

import sys, requests, time
import urllib, urllib2, re
from bs4 import BeautifulSoup

websiteBase = "http://wiki.52poke.com"
websiteHome = "http://wiki.52poke.com/wiki/%E5%AE%9D%E5%8F%AF%E6%A2%A6%E5%88%97%E8%A1%A8%EF%BC%88%E6%8C%89%E5%85%A8%E5%9B%BD%E5%9B%BE%E9%89%B4%E7%BC%96%E5%8F%B7%EF%BC%89"

def getPokemonSn(soup, pokemonInfoTag):# 获取宝可梦图鉴编号，包含全国图鉴和各地区图鉴
    snDict = {}
    NationalSn = soup.select('.textblack.bgwhite > a')[0].text.lstrip('#').encode('utf8')
    snDict['全国'] = NationalSn
    trList = pokemonInfoTag.select('.roundy.bgwhite.fulltable.textblack > tr')
    for tr in trList:
        if tr.has_attr('class') and tr['class'][0] == 'hide':
            continue
        tdList = tr.select('td')
        tdLen = len(tdList)
        if tdLen <= 1: continue
        region = tdList[0].text.strip().encode('utf8')
        for i, td in enumerate(tdList):
            if i == 0: continue
            if 'hide' in td['class']: continue
            if snDict.get(region, None):
                snDict[region] = snDict[region] + '/' + td.text.strip().encode('utf8')
            else:
                snDict[region] = td.text.strip().encode('utf8')
    return snDict

def getPokemonName(pokemonInfoTag, sightName):# 获取宝可梦名字，包含中文名、日文名、英文名，其中有多形态的，中文名以：宝可梦原名-宝可梦形态名展示
    if sightName: sightName = u'-' + sightName
    pokemonNameList = pokemonInfoTag.select('.textblack.bgwhite > span > b')
    pokemonNameList += pokemonInfoTag.select('.textblack.bgwhite > b')
    if len(pokemonNameList) < 3: return ('unknown', 'unknown', 'unknown')
    name_zh = pokemonNameList[0].text + sightName
    name_jp = pokemonNameList[1].text
    name_en = pokemonNameList[2].text
    return (name_zh.encode('utf8'), name_jp.encode('utf8'), name_en.encode('utf8'))

def getPokemonAttr(pokemonInfoTag):# 获取宝可梦属性，多个属性以丨间隔， 属性：一般、火、虫、水、毒、电、飞行、草、地面、冰、格斗、超能力、岩石、幽灵、龙、恶、钢、妖精
    pokemonAttrL = pokemonInfoTag.select('.bgwhite.fulltable > tr > .roundy > span > a')
    attributes = ""
    for atag in pokemonAttrL:
        if attributes != "":
            attributes += "|"
        attributes += atag.text.strip()
    return attributes.encode('utf8')

def getPokemonClass(pokemonInfoTag):# 获取宝可梦分类
    pokemonClassL = pokemonInfoTag.select('table.roundy.bgwhite.fulltable > tr > td.roundy.bgwhite.bw-1')
    pokemonClass = pokemonClassL[0].text.strip()
    return pokemonClass.encode('utf8')

def getPokemonFeatures(pokemonInfoTag):# 获取宝可梦特性，普通特性和隐藏特性
    pokemonFeatureL = pokemonInfoTag.select('.roundy.bgwhite.fulltable > td')
    for featureTag in pokemonFeatureL:
        print featureTag.text.encode('utf8')

# 注：jarTagL为获取宝可梦信息的容器，包括：
# 属性、分类、特性、100级时经验值、地区图鉴编号、[地区浏览器编号]
# 身高、体重、体形、脚印、图鉴颜色、捕获率、性别比例、培育、取得基础点数、旁支系列
def parsePokemonPage(soup, pokemonInfoTag, sightName = ''):# 解析宝可梦详情页
    print '*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-'
    tPokemonName = getPokemonName(pokemonInfoTag, sightName)
    #print tPokemonName[0], tPokemonName[1], tPokemonName[2]
    dPokeSn, sPokeAttr, sPokeClass = '', '', ''
    jarTagL = pokemonInfoTag.select('table.roundy.bw-1.fulltable > tr > td')
    for jarTag in jarTagL:
        if not jarTag.b: continue
        bTagText = jarTag.b.text
        if bTagText == u'地区图鉴编号':
            dPokeSn = getPokemonSn(pokemonInfoTag, jarTag)
            #for k, v in dPokeSn.iteritems():
            #    print k, v
        if bTagText == u'属性':
            sPokeAttr = getPokemonAttr(jarTag)
            #print sPokeAttr
        if bTagText == u'分类':
            sPokeClass = getPokemonClass(jarTag)
            #print sPokeClass
        if bTagText == u'特性':
            print "~~~~~"
            getPokemonFeatures(jarTag)

def checkPokemonPageMulti(pokemonInfoTag, soup):# 去除属性页，解析多形态宝可梦页面
    bRet = False
    #attrTag = pokemonInfoTag.select('tr > th > a > span.textblack') #区分是宝可梦页面还是属性页面
    attrTag = pokemonInfoTag.select('tr > th')
    if attrTag[0].a.text == u'属性列表':
        #print '这是属性。。。。'
        bRet = True
    elif attrTag[0].a.text == u'形态':
        sightPosition = 0
        for sight in attrTag:
            sightText = sight.text.strip('\n')
            if sightText and sightText != u'形态':
                sightPosition += 1
                targetPokemon = soup.select('tr._toggle.form' + str(sightPosition))[0]
                parsePokemonPage(soup, targetPokemon, sightText)
                bRet = True
    return bRet

def checkPokemonPage(pokemonPage):
    soup = BeautifulSoup(pokemonPage.text, 'lxml')
    pokemonInfoTagList = soup.select('#bodyContent > #mw-content-text > .mw-parser-output > .roundy.a-r.at-c')
    pokemonInfoTag = pokemonInfoTagList[0]
    if checkPokemonPageMulti(pokemonInfoTag, soup) == True: return # 去除属性页，解析多形态宝可梦页面
    parsePokemonPage(soup, pokemonInfoTag) # 解析宝可梦详情页

def getPokemonInfo(indexPage):
    soup = BeautifulSoup(indexPage.text, 'lxml')
    #print indexPage.text
    pokemonList = soup.select('.mw-body-content > .mw-content-ltr > .mw-parser-output > .eplist > tr > td > a')
    i = 0
    for pokemon in pokemonList:
        i += 1
        #print pokemon
        pokemonUrl = websiteBase + pokemon['href']
        #print pokemonUrl
        pokemonPage = requests.get(pokemonUrl)
        #if i == 7: checkPokemonPage(pokemonPage)
        checkPokemonPage(pokemonPage)
        sys.stdout.flush()
        #if i >= 4 : break

indexPage = requests.get(websiteHome)
getPokemonInfo(indexPage)
