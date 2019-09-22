#! /usr/bin/env python
# -*- coding=utf-8 -*-

import sys
import requests
import json
from bs4 import BeautifulSoup

websiteBase = "http://wiki.52poke.com"
websiteHome = "http://wiki.52poke.com/wiki/" \
              + "%E5%AE%9D%E5%8F%AF%E6%A2%A6%E5%88%97%E8%A1%A8%EF%BC%88%E6%8C" \
              + "%89%E5%85%A8%E5%9B%BD%E5%9B%BE%E9%89%B4%E7%BC%96%E5%8F%B7%EF%BC%89"


def checkPokemonPage(pokemonPage):
    if not pokemonPage: return
    soup = BeautifulSoup(pokemonPage.text, 'lxml')
    # 解析宝可梦详情
    pokemonInfoTagList = soup.select('#bodyContent > #mw-content-text > .mw-parser-output')
    if len(pokemonInfoTagList) == 0: return
    pokemonInfoTag = pokemonInfoTagList[0]
    print pokemonInfoTag


def mainEntrance():
    homePage = requests.get(websiteHome)
    soup = BeautifulSoup(homePage.text, 'lxml')
    pokemonTagList = soup.select(
        '.mw-body-content > .mw-content-ltr > .mw-parser-output > .eplist > tbody > tr > td > a')
    i = 0
    for pokemonUrlTag in pokemonTagList:
        i += 1
        pokemonUrl = websiteBase + pokemonUrlTag['href']

        pokemonPage = None
        while True:
            try:
                pokemonPage = requests.get(pokemonUrl)
                break
            except:
                continue

        checkPokemonPage(pokemonPage)
        sys.stdout.flush()
        break


if __name__ == '__main__':
    mainEntrance()
