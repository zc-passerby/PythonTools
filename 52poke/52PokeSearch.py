#! /usr/bin/env python
#-*- coding=utf-8 -*-

from urllib import request
from bs4 import BeautifulSoup
import re, os, sys, time

pokemonListBase = "https://wiki.52poke.com/wiki/%E5%AE%9D%E5%8F%AF%E6%A2%A6%E5%88%97%E8%A1%A8%EF%BC%88%E6%8C%89%E5%85%A8%E5%9B%BD%E5%9B%BE%E9%89%B4%E7%BC%96%E5%8F%B7%EF%BC%89"

def getPokemonInfo(pokemonListPage):
    soup = BeautifulSoup(pokemonListPage.text, 'lxml')


if __name__ == '__main__':
    pokemonListPage = requests.get(pokemonListBase)
    getPokemonInfo(pokemonListPage)