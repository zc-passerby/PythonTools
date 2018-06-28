#! /usr/bin/env python
#-*- coding=utf-8 -*-

import sys, requests, time
import urllib, urllib2, re
from bs4 import BeautifulSoup

def getPokemonHead():
    homeUrl = 'https://www.pkparaiso.com'
    targetUrl = 'https://www.pkparaiso.com/xy/artworks_pokemon_global_link.php'
    targetPage = requests.get(targetUrl, verify=False)
    soup = BeautifulSoup(targetPage.text, 'lxml')
    #print targetPage.text
    imgL = soup.select('div > a.colorboxlink > img')
    for img in imgL:
        imgUrl = homeUrl + '/' + img['src']
        imgFilePath = 'pokemonHead/head_' + str(img['src'].split('/')[-1])
        urllib.urlretrieve(imgUrl, imgFilePath)
        print 'save', imgFilePath, 'successful'

if __name__ == '__main__':
    getPokemonHead()