# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
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

st.title("Corona virus")
st.markdown('The source data can be found [here](https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_time_series)!')

the_country = 'Hungary'

@st.cache
def load_data(the_file, country):
    countries = []
    data = pd.read_csv(the_file)
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
    if s == '':
        return 0
    s = s.replace(',','')
    return int(s)

df_c, countries = load_data(DATA_URL + FILE_C, the_country) # Esetek
countries = sorted(list(set(countries[0])))

the_country = st.selectbox('Select country', countries)

df_d,_ = load_data(DATA_URL + FILE_D, the_country) # Halottak
df_r,_ = load_data(DATA_URL + FILE_R, the_country) # Gyógyultak
df_c, countries = load_data(DATA_URL + FILE_C, the_country) # Esetek

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
    eset = int(c[0].text)
    gyogyult = int(c[1].text)

    hf = pd.read_html('https://koronavirus.gov.hu/elhunytak')                                                                                                                                                                                                                   
    hf = pd.DataFrame(hf[0])
    hf.drop(['Sorszám', 'Alapbetegségek'], axis=1, inplace = True)
    halott = hf.shape[0]
    avg_man = round(hf[hf['Nem'] == 'Férfi'].Kor.mean(),2)
    avg_wmn = round(hf[hf['Nem'] == 'Nő'].Kor.mean(),2)
    
    gr = hf.groupby(['Nem']).count()                    
    
    ages = lambda x: int(str(x)[:-1]+'0')
    hf['Kor'] = hf['Kor'].apply(ages)
    hf = hf.groupby(hf['Kor']).count()
    
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
df = df.astype(int)

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
    gr.rename(columns = {'Kor': 'Eset/Nem'}, inplace = True)
    hf.rename(columns = {'Nem': 'Eset/Korcsoport'}, inplace = True)
    st.bar_chart(gr)
    st.bar_chart(hf)
    st.markdown(f'**Férfi átlag:** *{avg_man}* év **Női átlag:** *{avg_wmn}* év')