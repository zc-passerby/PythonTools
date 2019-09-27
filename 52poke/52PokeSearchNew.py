#! /usr/bin/env python
# -*- coding=utf-8 -*-

import sys
import requests
import random
import string
import urllib
import json
from dbHandler import ObjSqliteConnector
from bs4 import BeautifulSoup

websiteBase = "http://wiki.52poke.com"
# 全局sqlite连接
sqliteConn = ObjSqliteConnector("./52Poke.db3")


# 右上角宝可梦信息卡片，包含宝可梦名称，图片，属性，分类，特性，全国图鉴编号，地区图鉴编号
# 身高，体重，体形，脚印，图鉴颜色，捕获率，性别比例，蛋群，孵化周期，对战获得的努力值和经验
class SinglePokemonCard:
    def __init__(self, pokemonCardTag, sightName=''):
        self.pokemonCardTag = pokemonCardTag
        self.sightName = sightName

    # 获取宝可梦的名字，包含中文名、日文名、英文名，其中有多形态的，中文名为宝可梦名称【形态名】，如：妙蛙花【超级妙蛙花】
    def getName(self):
        nameTagList = self.pokemonCardTag.select('.textblack.bgwhite > span > b')
        nameTagList += self.pokemonCardTag.select('.textblack.bgwhite > b')
        if len(nameTagList) < 3: return ('未命名', '未命名', '未命名')
        nameZh = nameTagList[0].text
        if self.sightName: nameZh = nameZh + u'【' + self.sightName + u'】'
        nameJp = nameTagList[1].text
        nameEn = nameTagList[2].text
        self.tPokemonName = (nameZh.encode('utf8'), nameJp.encode('utf8'), nameEn.encode('utf8'))

    # 获取宝可梦图片的Url，后续考虑将图片下载下来
    # 另外，有些宝可梦会有多张图片，后续再考虑处理
    def getImage(self):
        imageTagList = self.pokemonCardTag.select('.roundy.bgwhite.fulltable > tbody > tr > td > div > a.image > img')
        imageTagList += self.pokemonCardTag.select('.roundy.bgwhite.fulltable > tbody > tr > td > a.image > img')
        imageUrl = 'http:' + imageTagList[0]['data-url']
        imageUrl = imageUrl.replace('300px', '120px')  # 获取120像素的图片
        self.sPokemonImageUrl = imageUrl.encode('utf8')

    # 获取宝可梦图鉴编号，包含全国图鉴编号和各地区的图鉴编号
    # 全国图鉴编号是从pokemonCardTag里直接获取的，地区编号是从信息容器中获取
    def getSn(self, jarTag):
        snDict = {}
        # 全国图鉴编号
        NationalSn = self.pokemonCardTag.select('.textblack.bgwhite > a')[0].text.lstrip('#').encode('utf8')
        snDict['全国'] = NationalSn
        # 地区图鉴编号
        trTagList = jarTag.select('table > tbody > tr')
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
                regionalSn = tdTag.text.strip().strip('#').encode('utf8')
                if snDict.get(region, None):
                    snDict[region] = snDict[region] + '/' + regionalSn
                else:
                    snDict[region] = regionalSn
        self.dPokemonSn = snDict

    # 获取宝可梦属性，多个属性以|分隔
    # 属性：一般、火、虫、水、毒、电、飞行、草、地面、冰、格斗、超能力、岩石、幽灵、龙、恶、钢、妖精
    def getType(self, jarTag):
        aTagList = jarTag.select('table > tbody > tr > td > span > a')
        sType = u""
        for aTag in aTagList:
            if sType != "": sType += "|"
            sType += aTag.text.strip()
        self.sPokemonType = sType.encode('utf8')

    # 获取宝可梦的特性，分为普通特性和隐藏特性，多个特性以|分隔
    # 目前普通特性可能是一个或两个，隐藏特性可能是零个或一个
    def getAbilities(self, jarTag):
        sNormalAbility, sHiddenAbility = u'', u''
        tdTagList = jarTag.select('table > tbody > tr > td')
        for tdTag in tdTagList:
            smallTag = tdTag.find('small')
            if smallTag and (smallTag.text.strip() == u'隐藏特性' or smallTag.text.strip() == u'隱藏特性'):
                if sHiddenAbility != '': sHiddenAbility += '|'
                sHiddenAbility += tdTag.a.text.strip()
            else:
                aTagList = tdTag.find_all('a')
                for aTag in aTagList:
                    if sNormalAbility != '': sNormalAbility += '|'
                    sNormalAbility += aTag.text.strip()
        self.tPokemonAbilities = (sNormalAbility.encode('utf8'), sHiddenAbility.encode('utf8'))

    # 获取捕获概率和普通精灵球在满体力下的捕获概率
    def getCatchRate(self, jarTag):
        sRate, sFullRate = u'', u''
        tdTagList = jarTag.select('table > tbody > tr > td')
        if len(tdTagList) >= 1:
            tdTag = tdTagList[0]
            sRate = tdTag.text.strip()
            smallTag = tdTag.find('small')
            if smallTag and smallTag.text.strip():
                sFullRate = smallTag.text.strip()
                sRate = sRate.replace(sFullRate, '')
        self.tPokemonCatchRate = (sRate, sFullRate)

    # 获取宝可梦性别比例，如雄性100%，雄性50%|雌性50%，无性别
    def getGenderRatio(self, jarTag):
        sGenderRatio = u''
        tdTagList = jarTag.select('table > tbody > tr > td > table > tbody > tr > td')
        for tdTag in tdTagList:
            if tdTag.has_attr('class') and 'hide' in tdTag['class']: continue
            if len(tdTag.find_all('div')) > 0: continue  # 该处是显示百分比的框子的
            sGenderRatio = tdTag.text.strip()
        self.sPokemonGenderRatio = sGenderRatio.encode('utf8')

    # 获取宝可梦的培育信息，包括蛋群和孵化周期
    def getBreedingInfo(self, jarTag):
        sEggGroup, sEggCycle = u'', u''
        tdTagList = jarTag.select('table > tbody > tr > td')
        if len(tdTagList) >= 2:
            sEggGroup = tdTagList[0].text.strip()
            sEggCycle = tdTagList[1].text.strip()
        self.tPokemonBreedingInfo = (sEggGroup.encode('utf8').replace(' ', ''), sEggCycle.encode('utf8'))

    # 获取与该宝可梦对战可获得的战斗点数和经验
    def getBattleInfo(self, jarTag):
        dBattleInfo = {}
        tdTagList = jarTag.select('table > tbody > tr > td')
        for tdTag in tdTagList:
            smallTag = tdTag.find('small')
            if smallTag and smallTag.text.strip():
                smallText = smallTag.text.strip()
                tdText = tdTag.text.strip()
                content = tdText.replace(smallText, '').encode('utf8').strip().strip('*')
                dBattleInfo[smallText.encode('utf8')] = content
        self.dPokemonBattleInfo = dBattleInfo

    # 获取宝可梦信息
    # 宝可梦分类、100级时的经验值、身高、体重、图鉴颜色
    def getSingleText(self, jarTag):
        sResult = u''
        tdTagList = jarTag.select('table > tbody > tr > td')
        if len(tdTagList) >= 1:
            sResult = tdTagList[0].text.strip()
        return sResult.encode('utf8')

    # 将宝可梦数据插入到数据库中
    def doDatabaseInsert(self):
        pokemonBaseInfoTuple = (
            self.dPokemonSn['全国'], json.dumps(self.dPokemonSn, ensure_ascii=False), self.tPokemonName[0],
            self.tPokemonName[1], self.tPokemonName[2], self.sPokemonImageUrl, self.sPokemonType,
            self.sPokemonCategory, self.tPokemonAbilities[0], self.tPokemonAbilities[1],
            self.sPokemon100Experience, self.sPokemonHeight, self.sPokemonWeight, self.sPokemonBookColor,
            self.tPokemonCatchRate[0], self.tPokemonCatchRate[1], self.sPokemonGenderRatio,
            self.tPokemonBreedingInfo[0], self.tPokemonBreedingInfo[1],
            json.dumps(self.dPokemonBattleInfo, ensure_ascii=False))
        print sqliteConn.insert('PokemonBaseInfo', [pokemonBaseInfoTuple, ])

    def run(self):
        # 宝可梦名称，中文、日文、英文
        self.getName()
        # print self.tPokemonName[0], self.tPokemonName[1], self.tPokemonName[2]
        # 宝可梦图片
        self.getImage()
        # print urllib.unquote(self.sPokemonImageUrl)

        # jarTagList 中包含各种宝可梦信息
        # 属性、分类、特性、100级时经验值、地区图鉴编号、地区浏览器编号
        # 身高、体重、体形、脚印、图鉴颜色、捕获率、性别比例、培育、取得基础点数、旁支系列
        jarTagList = self.pokemonCardTag.select('table.roundy.bw-1.fulltable > tbody > tr > td')
        for jarTag in jarTagList:
            if not jarTag.b: continue  # 若不存在b标签，则无需解析
            bTagText = jarTag.b.text  # 每个信息容器代表的宝可梦的信息的类型
            if bTagText == u'地区图鉴编号':
                self.getSn(jarTag)
                # for k, v in self.dPokemonSn.iteritems():
                #     print k, v
            elif bTagText == u'属性':
                self.getType(jarTag)
                # print self.sPokemonType
            elif bTagText == u'分类':
                self.sPokemonCategory = self.getSingleText(jarTag)
                # print self.sPokemonCategory
            elif bTagText == u'特性':
                self.getAbilities(jarTag)
                # print '普通特性:{}, 隐藏特性:{}'.format(self.tPokemonAbilities[0], self.tPokemonAbilities[1])
            elif bTagText == u'100级时经验值':
                self.sPokemon100Experience = self.getSingleText(jarTag)
                # print self.sPokemon100Experience
            elif bTagText == u'身高':
                self.sPokemonHeight = self.getSingleText(jarTag)
                # print self.sPokemonHeight
            elif bTagText == u'体重':
                self.sPokemonWeight = self.getSingleText(jarTag)
                # print self.sPokemonWeight
            elif bTagText == u'图鉴颜色':
                self.sPokemonBookColor = self.getSingleText(jarTag)
                # print self.sPokemonBookColor
            elif bTagText == u'捕获率':
                self.getCatchRate(jarTag)
                # print '捕获率:{}, 满体力捕获率:{}'.format(self.tPokemonCatchRate[0], self.tPokemonCatchRate[1])
            elif bTagText == u'性别比例':
                self.getGenderRatio(jarTag)
                # print self.sPokemonGenderRatio
            elif bTagText == u'培育':
                self.getBreedingInfo(jarTag)
                # print '蛋群为：{}, 孵化周期为：{}'.format(self.tPokemonBreedingInfo[0], self.tPokemonBreedingInfo[1])
            elif bTagText == u'取得基础点数':
                self.getBattleInfo(jarTag)
                # for k, v in self.dPokemonBattleInfo.iteritems():
                #     print k, v
        # 将所有数据插入到数据库
        self.doDatabaseInsert()
        return self.dPokemonSn['全国']


# 宝可梦详情页
class SinglePokemonPage:
    def __init__(self, pokemonPage):
        # 获取目标宝可梦页
        self.soup = BeautifulSoup(pokemonPage.text, 'lxml')
        self.pokemonName = ''
        self.nationalSn = ''
        self.dSpeciesStrength = {}

    def getName(self):
        sPokeName = u''
        h1TagList = self.soup.select('h1#firstHeading.firstHeading')
        if len(h1TagList) > 0: sPokeName = h1TagList[0].text.strip()
        self.pokemonName = sPokeName.encode('utf8')

    # 解析宝可梦种族值
    def parseSpecies(self, speciesTag):
        dPokeSpecies = {}
        hitPointTag = speciesTag.select('tr.bgl-HP')[0]
        attackTag = hitPointTag.find_next_sibling()
        defenseTag = attackTag.find_next_sibling()
        specialAttackTag = defenseTag.find_next_sibling()
        specialDefenseTag = specialAttackTag.find_next_sibling()
        speedTag = specialDefenseTag.find_next_sibling()
        dPokeSpecies['HP'] = hitPointTag.select('td > table > tbody > tr > th')[1].text.strip().encode('utf8')
        dPokeSpecies['攻击'] = attackTag.select('td > table > tbody > tr > th')[1].text.strip().encode('utf8')
        dPokeSpecies['防御'] = defenseTag.select('td > table > tbody > tr > th')[1].text.strip().encode('utf8')
        dPokeSpecies['特攻'] = specialAttackTag.select('td > table > tbody > tr > th')[1].text.strip().encode('utf8')
        dPokeSpecies['特防'] = specialDefenseTag.select('td > table > tbody > tr > th')[1].text.strip().encode('utf8')
        dPokeSpecies['速度'] = speedTag.select('td > table > tbody > tr > th')[1].text.strip().encode('utf8')
        return dPokeSpecies

    # 获取宝可梦的种族值，若有多形态
    def getSpeciesStrength(self):
        # 判断是否存在多形态种族值
        tabTagList = self.soup.select('.tabbertab > .alignt-center')
        contentTagList = self.soup.select('table.alignt-center')
        shapeCount = len(contentTagList)
        if shapeCount > 1 and len(tabTagList) == shapeCount:  # 种族值多形态
            for contentTag in contentTagList:
                shapeName = contentTag.find_parent()['title'].strip().encode('utf8')
                dSpecies = self.parseSpecies(contentTag)
                if shapeName in self.dSpeciesStrength: shapeName = shapeName + ''.join(
                    random.sample(string.ascii_letters + string.digits, 4))
                self.dSpeciesStrength[shapeName] = dSpecies
                # for k, v in dSpecies.iteritems():
                #     print k, v
        elif shapeCount == 1:  # 种族值单形态
            contentTag = contentTagList[0]
            dSpecies = self.parseSpecies(contentTag)
            self.dSpeciesStrength['基础'] = dSpecies
            # for k, v in dSpecies.iteritems():
            #     print k, v

    def doDatabaseInsert(self):
        insertList = []
        for k, v in self.dSpeciesStrength.iteritems():
            totalValue = int(v['HP']) + int(v['攻击']) + int(v['防御']) + int(v['特攻']) + int(v['特防']) + int(v['速度'])
            pokemonSpeciesStrengthTuple = (
                self.nationalSn, self.pokemonName, k, v['HP'], v['攻击'], v['防御'], v['特攻'], v['特防'], v['速度'], totalValue)
            insertList.append(pokemonSpeciesStrengthTuple)
        print sqliteConn.insert('PokemonSpeciesStrength', insertList)

    def run(self):
        # 获取宝可梦名字
        self.getName()
        # 获取宝可梦信息卡片
        # 若为属性页或多形态宝可梦，则该卡片是属性列表或多形态列表
        pokemonCardTagList = self.soup.select('#bodyContent > #mw-content-text > .mw-parser-output > .roundy.a-r.at-c')
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
                    targetPokemonCardTag = self.soup.select('tr._toggle.form' + str(sightPosition))[0]
                    pokemon = SinglePokemonCard(targetPokemonCardTag, sightText)
                    self.nationalSn = pokemon.run()
        else:
            pokemon = SinglePokemonCard(pokemonCardTag)
            self.nationalSn = pokemon.run()

        print self.nationalSn, self.pokemonName
        # 获取宝可梦种族值
        self.getSpeciesStrength()
        self.doDatabaseInsert()


def ClearAllDataFromDatabase():
    print sqliteConn.delete('PokemonBaseInfo')
    print sqliteConn.delete('PokemonSpeciesStrength')


def parsePokemon():
    websiteHome = "http://wiki.52poke.com/wiki/" \
                  + "%E5%AE%9D%E5%8F%AF%E6%A2%A6%E5%88%97%E8%A1%A8%EF%BC%88%E6%8C" \
                  + "%89%E5%85%A8%E5%9B%BD%E5%9B%BE%E9%89%B4%E7%BC%96%E5%8F%B7%EF%BC%89"
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
        SinglePokemonPage(pokemonPage).run()
        sys.stdout.flush()
        # break


if __name__ == '__main__':
    ClearAllDataFromDatabase()
    parsePokemon()
