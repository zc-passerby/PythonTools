#! /usr/bin/env python
# -*- coding=utf-8 -*-

import sys
import requests
import json
from dbHandler import ObjSqliteConnector
from bs4 import BeautifulSoup

websiteBase = "http://wiki.52poke.com"
websiteHome = "http://wiki.52poke.com/wiki/" \
              + "%E5%AE%9D%E5%8F%AF%E6%A2%A6%E5%88%97%E8%A1%A8%EF%BC%88%E6%8C" \
              + "%89%E5%85%A8%E5%9B%BD%E5%9B%BE%E9%89%B4%E7%BC%96%E5%8F%B7%EF%BC%89"


def getPokemonSn(soup, pokemonInfoTag):  # 获取宝可梦图鉴编号，包含全国图鉴和各地区图鉴
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


def getPokemonName(pokemonInfoTag, sightName):  # 获取宝可梦名字，包含中文名、日文名、英文名，其中有多形态的，中文名以：宝可梦原名-宝可梦形态名展示
    if sightName: sightName = u'-' + sightName
    pokemonNameList = pokemonInfoTag.select('.textblack.bgwhite > span > b')
    pokemonNameList += pokemonInfoTag.select('.textblack.bgwhite > b')
    if len(pokemonNameList) < 3: return ('unknown', 'unknown', 'unknown')
    name_zh = pokemonNameList[0].text + sightName
    name_jp = pokemonNameList[1].text
    name_en = pokemonNameList[2].text
    return (name_zh.encode('utf8'), name_jp.encode('utf8'), name_en.encode('utf8'))


def getPokemonImg(pokemonInfoTag):  # 获取宝可梦图片
    pokemonImgTagL = pokemonInfoTag.select('.roundy.bgwhite.fulltable > tr > td > div > a.image > img')
    pokemonImgTagL += pokemonInfoTag.select('.roundy.bgwhite.fulltable > tr > td > a.image > img')
    pokeImgUrl = 'http:' + pokemonImgTagL[0]['data-url']
    pokeImgUrl = pokeImgUrl.replace('300px', '120px')  # 获取120像素的图片
    return pokeImgUrl.encode('utf8')


def getPokemonAttr(pokemonInfoTag):  # 获取宝可梦属性，多个属性以丨间隔， 属性：一般、火、虫、水、毒、电、飞行、草、地面、冰、格斗、超能力、岩石、幽灵、龙、恶、钢、妖精
    pokemonAttrL = pokemonInfoTag.select('.bgwhite.fulltable > tr > .roundy > span > a')
    attributes = ""
    for atag in pokemonAttrL:
        if attributes != "":
            attributes += "|"
        attributes += atag.text.strip()
    return attributes.encode('utf8')


def getPokemonClass(pokemonInfoTag):  # 获取宝可梦分类
    pokemonClassL = pokemonInfoTag.select('table.roundy.bgwhite.fulltable > tr > td.roundy.bgwhite.bw-1')
    pokemonClass = pokemonClassL[0].text.strip()
    return pokemonClass.encode('utf8')


def getPokemonFeatures(pokemonInfoTag):  # 获取宝可梦特性，普通特性和隐藏特性
    normalFeat, hideFeat = '', ''
    try:
        pokemonFeatureL = pokemonInfoTag.select('.roundy.bgwhite.fulltable > tr > td')
        for featureTag in pokemonFeatureL:
            curFeat = featureTag.a.text.strip()
            smallTag = featureTag.find('small')
            if smallTag and smallTag.text.strip() == u'隱藏特性':
                hideFeat = curFeat
                continue
            if normalFeat != "": normalFeat += "|"
            normalFeat += curFeat
        return (normalFeat.encode('utf8'), hideFeat.encode('utf8'))
    except:
        return (normalFeat, hideFeat)


def getPokemonRacialValue(soup, position):
    dPokeRace = {}
    try:
        hitPointTag = soup.select('tr.bgl-HP')[position]
        attackTag = hitPointTag.find_next_sibling()
        defenseTag = attackTag.find_next_sibling()
        specialAttacTag = defenseTag.find_next_sibling()
        specialDefenseTag = specialAttacTag.find_next_sibling()
        speedTag = specialDefenseTag.find_next_sibling()
        dPokeRace['HP'] = hitPointTag.select('td > table > tr > th')[1].text.strip().encode('utf8')
        dPokeRace['攻击'] = attackTag.select('td > table > tr > th')[1].text.strip().encode('utf8')
        dPokeRace['防御'] = defenseTag.select('td > table > tr > th')[1].text.strip().encode('utf8')
        dPokeRace['特攻'] = specialAttacTag.select('td > table > tr > th')[1].text.strip().encode('utf8')
        dPokeRace['特防'] = specialDefenseTag.select('td > table > tr > th')[1].text.strip().encode('utf8')
        dPokeRace['速度'] = speedTag.select('td > table > tr > th')[1].text.strip().encode('utf8')
        return dPokeRace
    except:
        dPokeRace['HP'] = '同原始形态'
        dPokeRace['攻击'] = '同原始形态'
        dPokeRace['防御'] = '同原始形态'
        dPokeRace['特攻'] = '同原始形态'
        dPokeRace['特防'] = '同原始形态'
        dPokeRace['速度'] = '同原始形态'
        return dPokeRace


def getEvolvePath(evolveDetailTag):
    print filter(lambda x: x != '\n', evolveDetailTag.contents)[0]


def parseBodyLink(soup):
    # evolveTagL = soup(id='.E8.BF.9B.E5.8C.96') # 获取进化节点链接
    # superEvolveTagL = soup(id='.E8.B6.85.E7.B4.9A.E9.80.B2.E5.8C.96') # 获取超级进化节点链接
    # if len(evolveTagL):
    #     evolveTag = evolveTagL[0]
    #     evolveDetailTag = evolveTag.find_parent().find_next_sibling() # 获取进化节点详细信息（进化链接的父节点的下一个兄弟节点）
    #     #getEvolvePath(evolveDetailTag)
    # if len(superEvolveTagL):
    #     superEvolveTag = superEvolveTagL[0]
    #     superEvolveDetailTag = superEvolveTag.find_parent().find_next_sibling() # 获取超级进化节点详细信息（超级进化链接的父节点的下一个兄弟节点）
    #     #print superEvolveDetailTag
    #     getEvolvePath(superEvolveDetailTag)
    pass


# 注：jarTagL为获取宝可梦信息的容器，包括：
# 属性、分类、特性、100级时经验值、地区图鉴编号、地区浏览器编号
# 身高、体重、体形、脚印、图鉴颜色、捕获率、性别比例、培育、取得基础点数、旁支系列
def parsePokemonPage(soup, pokemonInfoTag, sightName='', sightPosition=1):  # 解析宝可梦详情页
    sightPosition = sightPosition - 1  # 宝可梦第几种形态，但作为下标要-1
    tPokeName = getPokemonName(pokemonInfoTag, sightName)
    print tPokeName[0], tPokeName[1], tPokeName[2]
    sPokeImg = getPokemonImg(pokemonInfoTag)
    print sPokeImg
    dPokeSn, sPokeAttr, sPokeClass, tPokeFeat, dPokeRace = '', '', '', '', ''
    jarTagL = pokemonInfoTag.select('table.roundy.bw-1.fulltable > tr > td')
    for jarTag in jarTagL:
        if not jarTag.b: continue
        bTagText = jarTag.b.text
        if bTagText == u'地区图鉴编号':
            dPokeSn = getPokemonSn(pokemonInfoTag, jarTag)
            # for k, v in dPokeSn.iteritems():
            #    print k, v
        if bTagText == u'属性':
            sPokeAttr = getPokemonAttr(jarTag)
            # print sPokeAttr
        if bTagText == u'分类':
            sPokeClass = getPokemonClass(jarTag)
            # print sPokeClass
        if bTagText == u'特性':
            tPokeFeat = getPokemonFeatures(jarTag)
            # print tPokeFeat[0], tPokeFeat[1]
    dPokeRace = getPokemonRacialValue(soup, sightPosition)
    # parseBodyLink(soup) #暂时先不做这个了。。。
    # 开始插入sqlite数据库啦
    sqliteConn = ObjSqliteConnector("./52Poke.db3")
    pokeInfoTuple = (
        dPokeSn['全国'], json.dumps(dPokeSn, ensure_ascii=False), tPokeName[0], tPokeName[1], tPokeName[2], sPokeImg,
        sPokeAttr, sPokeClass, tPokeFeat[0], tPokeFeat[1], dPokeRace['HP'], dPokeRace['攻击'], dPokeRace['防御'],
        dPokeRace['特攻'], dPokeRace['特防'], dPokeRace['速度'])
    # print pokeInfoTuple
    print sqliteConn.insert('pokemonInfo', [pokeInfoTuple, ])


def checkPokemonPageMulti(pokemonInfoTag, soup):  # 去除属性页，解析多形态宝可梦页面
    bRet = False
    # attrTag = pokemonInfoTag.select('tr > th > a > span.textblack') #区分是宝可梦页面还是属性页面
    attrTag = pokemonInfoTag.select('tr > th')
    if attrTag[0].a.text == u'属性列表':
        # print '这是属性。。。。'
        bRet = True
    elif attrTag[0].a.text == u'形态':
        sightPosition = 0
        for sight in attrTag:
            sightText = sight.text.strip('\n')
            if sightText and sightText != u'形态':
                sightPosition += 1
                targetPokemon = soup.select('tr._toggle.form' + str(sightPosition))[0]
                parsePokemonPage(soup, targetPokemon, sightText, sightPosition)
                bRet = True
    return bRet


def checkPokemonPage(pokemonPage):
    soup = BeautifulSoup(pokemonPage.text, 'lxml')
    pokemonInfoTagList = soup.select('#bodyContent > #mw-content-text > .mw-parser-output > .roundy.a-r.at-c')
    pokemonInfoTag = pokemonInfoTagList[0]
    if checkPokemonPageMulti(pokemonInfoTag, soup): return  # 去除属性页，解析多形态宝可梦页面
    parsePokemonPage(soup, pokemonInfoTag)  # 解析宝可梦详情页


def getPokemonInfo(indexPageObj):
    soup = BeautifulSoup(indexPageObj.text, 'lxml')
    # print indexPageObj.text
    pokemonList = soup.select('.mw-body-content > .mw-content-ltr > .mw-parser-output > .eplist > tr > td > a')
    i = 0
    for pokemon in pokemonList:
        i += 1
        # print pokemon
        # if i < 1781: continue
        pokemonUrl = websiteBase + pokemon['href']
        # print pokemonUrl
        pokemonPage = ''
        while True:
            try:
                pokemonPage = requests.get(pokemonUrl)
                break
            except:
                continue
        # if i == 7: checkPokemonPage(pokemonPage)
        print '*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-'
        print i
        checkPokemonPage(pokemonPage)
        sys.stdout.flush()
        # if i >= 4 : break


indexPage = requests.get(websiteHome)
getPokemonInfo(indexPage)
