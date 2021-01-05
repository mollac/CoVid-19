# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup as bs
import requests

def get_deads():
    page = 0
    hl = []
    print('Downloading pages ', end='')
    while True:
        try:
            url = f'https://koronavirus.gov.hu/elhunytak?page={page}'
            hp = pd.read_html(url)
            hl.append(hp[0])
            page += 1
            print(page, end=', ',flush=True)
        except:
            break

    hf_ = pd.DataFrame(hl[0])
    for x in range(1, len(hl)):
        hf_ = hf_.append(pd.DataFrame(hl[x]))
    hf_['Nem'] = hf_['Nem'].str.upper()
    hf_['Nem'] = hf_['Nem'].apply(lambda x: "Férfi" if x[0]=="F" else "Nő")
    hf_.to_csv('halottak.csv')
    print(' done.')
    return(hf_)

x = get_deads()
