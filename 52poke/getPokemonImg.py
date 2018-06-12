#! /usr/bin/env python
#-*- coding=utf-8 -*-

import sys, requests, time
import urllib, urllib2, re
from bs4 import BeautifulSoup

websiteHome = "https://wiki.52poke.com/wiki/%E5%AE%9D%E5%8F%AF%E6%A2%A6%E5%88%97%E8%A1%A8%EF%BC%88%E6%8C%89%E5%85%A8%E5%9B%BD%E5%9B%BE%E9%89%B4%E7%BC%96%E5%8F%B7%EF%BC%89"

startPage = ''
#NovelList = []

def parseChapterPage(pageUrl):
    #print pageUrl
    global startPage
    startPage = pageUrl
    chapterPage = requests.get(pageUrl)
    chapterSoup = BeautifulSoup(chapterPage.text, 'lxml')
    chapterName = chapterSoup.select('.chaptercontent > .clearfix > h1')[0].text
    chapterBody = chapterSoup.select('.chaptercontent > .content')[0].get_text('\n\t','br/')
    chapterBody = chapterBody.replace('applyChapterSetting();', '')
    print chapterName, pageUrl
    f.write('\r\n' + chapterName + '\r\n')
    f.write(chapterBody)
    nextChapter = chapterSoup.select('.chaptercontent > .operate > ul > .last > a')
    if len(nextChapter) == 0:
        nextChapter = chapterSoup.select('.operate > ul > li.last > a')
    return nextChapter[0]['href']

def parseNovelPage(pageUrl, startFlag):
    nextPageHref = startPage
    if not startFlag:
        infoPage = requests.get(pageUrl)
        infoSoup = BeautifulSoup(infoPage.text, 'lxml')
        firstPageTag = infoSoup.select('.container > .left > .info > .operate.clearfix > .btn.btn-primary')[0]
        firstPageHref = firstPageTag['href']
        nextPageHref = firstPageHref
    while nextPageHref != pageUrl:
        nextPageHref = parseChapterPage(nextPageHref)
        time.sleep(0.1)
        #break

def getSearchedBookUrl(searchPage, startFlag):
    soup = BeautifulSoup(searchPage.text, 'lxml')
    bookATag = soup.select('.container > .left > .lastest > ul > li > .n2 > a')[0]
    bookHref = bookATag['href']
    bookName = bookATag.text
    if not startFlag:
        f.write(bookName)
    print bookHref, bookName
    return bookHref

def parseIndexPage(indexPage):
    soup = BeautifulSoup(searchPage.text, 'lxml')
    GuanDu = soup.select('#bodyContent.mw-body-content > .mw-content-ltr > .mw-parser-output > .roundy.eplist.s-关都')
    print Guandu

indexPage = requests.get(websiteHome)
parseIndexPage(indexPage)
