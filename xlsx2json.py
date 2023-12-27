## https://amis.afa.gov.tw/fruit/FruitProdDayTransInfo.aspx

from pandas import read_excel  
from re import compile as newRE
from json import dumps as jsdump
from sys import argv
from os import path

for a in argv[1:] :
    df = read_excel(a)

    print(df.head())

    print(path.join("docs/db/",path.basename(a)+".json"));
    df.to_json(path.join("docs/db/",path.basename(a)+".json"));

