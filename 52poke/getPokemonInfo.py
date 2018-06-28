#! /usr/bin/env python
#-*- coding=utf-8 -*-

import sys, requests, time
import urllib, urllib2, re
from bs4 import BeautifulSoup

websiteBase = "http://wiki.52poke.com"
websiteHome = "http://wiki.52poke.com/wiki/%E5%AE%9D%E5%8F%AF%E6%A2%A6%E5%88%97%E8%A1%A8%EF%BC%88%E6%8C%89%E5%85%A8%E5%9B%BD%E5%9B%BE%E9%89%B4%E7%BC%96%E5%8F%B7%EF%BC%89"

sqlFormat = "INSERT INTO `pokemonDefine` (`id`, `name_zh`, `name_en`, `name_jp`, `attributes`, `class`) VALUES ('{_id}', '{zh}', '{en}', '{jp}', '{attr}', '{cls}');"

def parseTargetPokemon(pokemonName, soup, position):
    bRet = True
    try:
        #print 'tr._toggle.form' + str(position)
        targetPokemon = soup.select('tr._toggle.form' + str(position))[0]
        pokemonNameL = targetPokemon.select('.textblack.bgwhite > span > b')
        pokemonNameL += targetPokemon.select('.textblack.bgwhite > b')
        #print pokemonNameL
        if len(pokemonNameL) < 3: return False
        pokemonId = soup.select('.textblack.bgwhite > a')[0].text.lstrip('#').lstrip('0')
        name_zh = pokemonNameL[0].text + u'-' + pokemonName
        name_jp = pokemonNameL[1].text
        name_en = pokemonNameL[2].text
        #print '----------------------------------------------------------'
        #print pokemonId
        #print name_zh, name_jp, name_en
        pokemonAttrL = targetPokemon.select('.bgwhite.fulltable > tr > .roundy > span > a')
        attributes = ""
        for atag in pokemonAttrL:
            if attributes != "":
                attributes += "|"
            attributes += atag.text.strip()
        #print attributes
        pokemonClassL = targetPokemon.select('table.roundy.bgwhite.fulltable > tr > td.roundy.bgwhite.bw-1')
        pokemonClass = pokemonClassL[0].text.strip()
        #print pokemonClass
        print sqlFormat.format(_id = pokemonId.encode('utf-8'), zh = name_zh.encode('utf-8'), en = name_en.encode('utf-8'), jp = name_jp.encode('utf-8'), attr = attributes.encode('utf-8'), cls = pokemonClass.encode('utf-8'))
    except:
        bRet = False
    return bRet

def parsePokemonPageMulti(soup):
    bRet = False
    sightL = soup.select('div.mw-parser-output > table.roundy.at-c.a-r > tr > th')
    i = 0
    for sight in sightL:
        text = sight.text.strip('\n')
        if text and text != u'形态':
            #print text
            i += 1
            if parseTargetPokemon(text, soup, i) == False : i = 0
    if i != 0 : bRet = True
    return bRet

def parsePokemonPage(pokemonPage):
    soup = BeautifulSoup(pokemonPage.text, 'lxml')
    pokemonNameList = soup.select('.textblack.bgwhite > span > b')
    pokemonNameList += soup.select('.textblack.bgwhite > b')
    if len(pokemonNameList) < 3: return
    pokemonId = soup.select('.textblack.bgwhite > a')[0].text.lstrip('#').lstrip('0')
    if parsePokemonPageMulti(soup) == True : return
    #print '----------------------------------------------------------'
    #print pokemonId
    name_zh = pokemonNameList[0].text
    name_jp = pokemonNameList[1].text
    name_en = pokemonNameList[2].text
    #print name_zh, name_jp, name_en
    #pokemonImg = soup.select('.roundy > tr > td > div > a > img')
    #imgUrl = pokemonImg[0]['data-url'].strip('/')
    #print imgUrl
    pokemonAttrL = soup.select('.bgwhite.fulltable > tr > .roundy > span > a')
    attributes = ""
    for atag in pokemonAttrL:
        if attributes != "":
            attributes += "|"
        attributes += atag.text.strip()
    #print attributes
    pokemonClassL = soup.select('table.roundy.bgwhite.fulltable > tr > td.roundy.bgwhite.bw-1')
    pokemonClass = pokemonClassL[0].text.strip()
    #print pokemonClass
    print sqlFormat.format(_id = pokemonId.encode('utf-8'), zh = name_zh.encode('utf-8'), en = name_en.encode('utf-8'), jp = name_jp.encode('utf-8'), attr = attributes.encode('utf-8'), cls = pokemonClass.encode('utf-8'))

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
        parsePokemonPage(pokemonPage)
        #if i >= 100 : break

indexPage = requests.get(websiteHome)
getPokemonInfo(indexPage)