# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime as datetime
from bs4 import BeautifulSoup as bs
import requests
import sys

now = datetime.datetime.today()
ido = str(now.hour)+':'+str(now.minute)
now = str(now.month)+'/'+str(now.day)+'/'+str(now.year)[2:]
country_table = {'United Kingdom': 'UK', 'United Arab Emirates': 'UAE', 'USA': 'US', 'Cote d\'Ivoire': 'Ivory Coast',
                 'Congo (Brazzaville)': 'Congo', 'Saint Vincent and the Grenadines': 'St. Vincent Grenadines',
                 'Korea, South': 'S. Korea', 'Taiwan*': 'Taiwan'}

DATA_URL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"
FILE_C = "time_series_covid19_confirmed_global.csv"
FILE_D = "time_series_covid19_deaths_global.csv"
FILE_R = "time_series_covid19_recovered_global.csv"
countries = []
st.title("Corona virus")
st.markdown('The source data can be found [here](https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_time_series)!')


f_c = pd.read_csv(DATA_URL+FILE_C)
f_d = pd.read_csv(DATA_URL+FILE_D)
f_r = pd.read_csv(DATA_URL+FILE_R)


def load_data(data, country):
    countries = []
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    data.rename(columns={'country/region':'country', 'province/state':'state'}, inplace=True)
    data.fillna(0, inplace=True)
    countries.append(list(data['country']))
    data = data[data['country'] == country]
    if not data[data.state == 0].empty:
        data = data[data.state == 0]
    data = data.groupby(['country']).sum()
    data = data.iloc[:,4:].T
    data = data[(data.T != 0).any()]
    data.rename(columns={data.columns[0]: 'Case'}, inplace=True)
    return data, countries

def str2int(s):
    s = s.strip()
    if s == '' or s == 'N/A':
        return 0
    s = s.replace(',','')
    return int(s)

_, countries = load_data(f_c, 'Hungary') # Esetek
countries = sorted(list(set(countries[0])))

the_country = st.selectbox('Select country', countries)

df_d,_ = load_data(f_d, the_country) # Halottak
df_r,_ = load_data(f_r, the_country) # Gyógyultak
df_c,_ = load_data(f_c, the_country) # Esetek

df = pd.DataFrame()
df['Cases'] = df_c['Case']
df['Recovered'] = df_r['Case']
df['Dead'] = df_d['Case']

dfT = df.T

if the_country == 'Hungary':
    url='https://koronavirus.gov.hu/'
    page = requests.get(url)
    soup = bs(page.content, 'html.parser')
    c = soup.find_all(class_ = 'number')
    eset = int(c[0].text.replace(' ',''))
    gyogyult = int(c[1].text.replace(' ',''))

    page = 0
    hl = []

    while True:
        try:
            url = f'https://koronavirus.gov.hu/elhunytak?page={page}'
            hp = pd.read_html(url)
            hl.append(hp[0])
            page += 1
        except:
            break

    hf = pd.DataFrame(hl[0])
    for x in range(1, len(hl)):
        hf = hf.append(pd.DataFrame(hl[x]))


    hf.drop(['Sorszám', 'Alapbetegségek'], axis=1, inplace = True)
    halott = hf.shape[0]
    avg_man = round(hf[hf['Nem'] == 'Férfi'].Kor.mean(),2)
    avg_wmn = round(hf[hf['Nem'] == 'Nő'].Kor.mean(),2)

    gr = hf.groupby(['Nem']).count()                    

    ages = lambda x: int(str(x)[:-1]+'0')
    hf['Kor'] = hf['Kor'].apply(ages)
    hf = hf.groupby(hf['Kor']).count()

    gr.rename(columns = {'Kor': 'Eset/Nem'}, inplace = True)
    hf.rename(columns = {'Nem': 'Eset/Korcsoport'}, inplace = True)

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
    dfT[now] = [eset, gyogyult, halott]
else:
    if the_country in country_table:
        the_country = country_table[the_country]

    url = 'https://www.worldometers.info/coronavirus/#countries'
    page = requests.get(url)
    soup = bs(page.content, 'html.parser')
    tbl = soup.find(id='main_table_countries_today')
    tbl = tbl.findAll('tr')
    eset = -1
    for tr in tbl:
        if the_country in tr.text:
            tds = tr.findAll('td')
            eset = str2int(tds[1].text)
            halott = str2int(tds[3].text)
            gyogyult = str2int(tds[5].text)
            break
    if eset > -1:
        dfT[now] = [eset, gyogyult, halott]
    else:
        st.markdown(f'{the_country} is not on [page]({url}).')



df = dfT.T

df.fillna(0, inplace= True)
df['Active'] = df['Cases']-df['Recovered'] - df['Dead']

df = df.reset_index()
df.rename(columns = {'index': 'Date'}, inplace=True)
df['Date'] = pd.to_datetime(df['Date'])
df.set_index(['Date'], drop=True, inplace=True)

df['Active'] = df['Cases']-(df['Recovered']+df['Dead'])
df['Cases+'] = df['Cases'].shift(1)
df['Dead+'] = df['Dead'].shift(1)
df['Recovered+'] = df['Recovered'].shift(1)
df.fillna(0, inplace=True)
df['Cases/day'] = abs(df['Cases'] - df['Cases+'])
df['Deads/day'] = abs(df['Dead'] - df['Dead+'])
df['Recovered/day'] = abs(df['Recovered'] - df['Recovered+'])

df.drop(['Cases+', 'Dead+', 'Recovered+'], axis=1, inplace=True)
df = df.astype(int)

m_cases = df['Cases'].iloc[-1]
m_recovered = df['Recovered'].iloc[-1]
m_dead = df['Dead'].iloc[-1]
m_active = df['Active'].iloc[-1]

st.header('The numbers')
st.markdown(f'Cases: **{m_cases}** Recovered: **{m_recovered}** ({round(m_recovered/m_cases*100,2)}%) Deads: **{m_dead}** ({round(m_dead/m_cases*100,2)}%) Active: **{m_active}**')

if st.checkbox('Show data'):
    st.header('The datatable')
    st.dataframe(df)

st.header('Cases, Active, Recovered and Deads')
st.line_chart(df[['Cases', 'Active', 'Recovered', 'Dead']])

st.header('Cases/day')
st.bar_chart(df['Cases/day'])

st.header('Recovered/day')
st.bar_chart(df['Recovered/day'])

st.header('Deads/day')
st.bar_chart(df['Deads/day'])

if the_country == 'Hungary':
    st.subheader('Nemek szerinti megoszlás')
    st.markdown(f"**Férfi:** {round(gr['Eset/Nem'][0]/m_dead*100,2)}% **Nő:** {round(gr['Eset/Nem'][1]/m_dead*100,2)}%")
    st.bar_chart(gr, use_container_width = False,  width = 200)

    st.subheader('Átlag életkorok')
    st.markdown(f'**Férfi:** *{avg_man}* év **Nő:** *{avg_wmn}* év')

    st.subheader('Korosztályos megoszlás')
    st.bar_chart(hf, use_container_width = False,  width = 600)

    st.subheader('Megyei megoszlás')
    url = 'korona_megyei.csv'
    df = pd.read_csv(url, sep=';')
    df = df.set_index('Dátum', drop = True)
    if st.checkbox('Adatok mutatása'):
        st.dataframe(df)
    megyek = list(df.columns)        
    datumok = list(df.index)
    select = st.multiselect('Válassz megyéket:', megyek, ('Győr-Moson-Sopron'))
    st.line_chart(df[select])
    st.subheader('Aktuális esetszám/megye')
    datum_filter = st.slider('Nap', 0, len(datumok)-1)
    st.bar_chart(df.iloc[datum_filter,:])

    url = r'https://hu.wikipedia.org/wiki/Magyarorsz%C3%A1g_megy%C3%A9i'
    dl = pd.read_html(url)
    mf = pd.DataFrame(dl[0][['Megye','Népesség']])
    mf.dropna(inplace = True)
    mf.T.loc['Megye',20] = 'Budapest'
    mf.columns = ['megye', 'lakos']
    mf.set_index('megye', drop = True, inplace = True)
    st_num = lambda x: int(x.replace('\xa0',''))
    mf['lakos'] = mf['lakos'].apply(st_num)
    mf['eset'] =  df.T.iloc[:,-1]
    st.subheader('Esetek száma a megye lakosságához viszonyítva')
    mf['százalék'] = round(mf.eset / mf.lakos * 100,3)
    st.bar_chart(mf[['százalék']])


