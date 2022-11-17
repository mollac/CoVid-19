# -*- coding: utf-8 -*-
import streamlit as st
import seaborn as sns
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import dates
import datetime as datetime
from bs4 import BeautifulSoup as bs
import requests
import sys
import pydeck as pdk
import folium
import time
import altair as alt


st.set_page_config(initial_sidebar_state="collapsed",
                   layout="wide", page_icon="🧊")

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


f_c = pd.read_csv(DATA_URL+FILE_C)
f_d = pd.read_csv(DATA_URL+FILE_D)
f_r = pd.read_csv(DATA_URL+FILE_R)


@st.cache
def load_data(data, country):
    countries = []
    def lowercase(x): return str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    data.rename(columns={'country/region': 'country',
                'province/state': 'state'}, inplace=True)
    data.fillna(0, inplace=True)
    countries.append(list(data['country']))
    data = data[data['country'] == country]
    if not data[data.state == 0].empty:
        data = data[data.state == 0]
    data = data.groupby(['country']).sum()
    data = data.iloc[:, 4:].T
    data = data[(data.T != 0).any()]
    data.rename(columns={data.columns[0]: 'Case'}, inplace=True)
    return data, countries


def str2int(s):
    s = s.strip()
    if s == '' or s == 'N/A':
        return 0
    s = s.replace(' ', '').replace(',', '').replace('.', '')
    return int(s)


@st.cache(allow_output_mutation=True)
def get_deads():
    try:
        df = pd.read_csv('./halottak.csv')
    except:
        df = pd.read_csv(
            'https://raw.githubusercontent.com/mollac/CoVid-19/master/halottak.csv')

    last = df['Sorszám'].iloc[0]
    page = 0
    hl = []

    while True:
        try:
            url = f'https://koronavirus.gov.hu/elhunytak?page={page}'
            hp = pd.read_html(url)
            hl.append(hp[0])
            page += 1
            if last in hp[0]['Sorszám'].to_list():
                break
        except:
            break
    try:
        hf_ = pd.DataFrame(hl[0])
    except:
        hf_ = pd.DataFrame()

    for x in range(1, len(hl)):
        # hf_ = hf_.append(pd.DataFrame(hl[x]))
        pd.concat([hf_, pd.DataFrame(hl[x])], ignore_index=True)

    pd.concat([df, hf_], ignore_index=True)
    df = df.drop_duplicates(subset='Sorszám')
    df.sort_values(by=['Sorszám'], ascending=False, inplace=True)
    try:
        df.to_csv('./halottak.csv', index=False)
    except:
        pass

    df['Alapbetegségek'] = df['Alapbetegségek'].str.lower()
    df.fillna('F', inplace=True)
    df['Nem'] = df['Nem'].str.upper()
    df['Nem'] = df['Nem'].apply(lambda x: "Férfi" if "F" in x[0] else "Nő")

    df.sort_values(by='Sorszám', axis=0, inplace=True)

    df.drop(['Sorszám'], axis=1, inplace=True)

    return(df)


_, countries = load_data(f_c, 'Hungary')  # Esetek
countries = sorted(list(set(countries[0])))

the_country = st.sidebar.selectbox('Select country', countries, 78)

st.title(f"Corona virus - {the_country}")
st.markdown(
    'The source data can be found [here](https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_time_series)!')


df_d, _ = load_data(f_d, the_country)  # Halottak
df_r, _ = load_data(f_r, the_country)  # Gyógyultak
df_c, _ = load_data(f_c, the_country)  # Esetek

df = pd.DataFrame()
df['Cases'] = df_c['Case']
df['Recovered'] = df_r['Case']
df['Dead'] = df_d['Case']

dfT = df.T

if the_country == 'Hungary':
    url = 'https://koronavirus.gov.hu/'
    page = requests.get(url)
    soup = bs(page.content, 'html.parser')
    fert_pest = str2int(soup.find(id='api-fertozott-pest').text)
    fert_videk = str2int(soup.find(id='api-fertozott-videk').text)
    gyogy_pest = str2int(soup.find(id='api-gyogyult-pest').text)
    gyogy_videk = str2int(soup.find(id='api-gyogyult-videk').text)
    halott_pest = str2int(soup.find(id='api-elhunyt-pest').text)
    halott_videk = str2int(soup.find(id='api-elhunyt-videk').text)

    fertozott = fert_pest + fert_videk
    gyogyult = gyogy_videk + gyogy_pest
    halott = halott_pest + halott_videk
    eset = fertozott + gyogyult + halott

    hf = get_deads()
    avg_man = round(hf[hf['Nem'] == 'Férfi'].Kor.mean(), 2)
    avg_wmn = round(hf[hf['Nem'] == 'Nő'].Kor.mean(), 2)

    gr = hf.groupby(['Nem']).count()
    def ages(x): return int(str(x)[:-1]+'0')

    hf['Kor'] = hf['Kor'].apply(ages)
    gf = hf.groupby(hf['Kor']).count()

    gr.rename(columns={'Kor': 'Eset/Nem'}, inplace=True)
    gf.rename(columns={'Nem': 'Eset/Korcsoport'}, inplace=True)

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

            eset = str2int(tds[2].text)
            halott = str2int(tds[4].text)
            gyogyult = str2int(tds[6].text)
            break
    if eset > -1:
        dfT[now] = [eset, gyogyult, halott]
    else:
        st.markdown(f'{the_country} is not on [page]({url}).')


df = dfT.T

df.fillna(0, inplace=True)
df['Active'] = df['Cases']-df['Recovered'] - df['Dead']

df = df.reset_index()
df.rename(columns={'index': 'Date'}, inplace=True)
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
st.subheader('Today:')
st.markdown(
    f'**{m_cases - df["Cases"].iloc[-2]}** new cases, **{m_dead - df["Dead"].iloc[-2]}** deads and **{m_recovered - df["Recovered"].iloc[-2]}** pepole recovered.')
if st.sidebar.checkbox('Show generated datatable:'):
    st.header('The datatable')
    st.dataframe(df)

st.header('Cases, Active, Recovered and Deads')
# st.line_chart(df[['Cases', 'Active', 'Recovered', 'Dead']])


x = range(0, df.shape[0], 10)
df['Dátum'] = df.index.strftime("%Y-%m-%d")
x_label = list(df['Dátum'])[::10]

fig = plt.figure(figsize=(16, 8))
plt.xticks(rotation=45)
plt.xticks(fontsize=10)
plt.grid(alpha=.5, linestyle='-')
# fig.autofmt_xdate()
# plt.locator_params(axis="y", nbins=30)
# plt.locator_params(axis="x", nbins=30)

sns.lineplot(data=df[['Cases', 'Active', 'Recovered', 'Dead']])
st.pyplot(fig)


st.header('Cases/day')
fig = plt.figure(figsize=(16, 8))
plt.xticks(rotation=45)
plt.xticks(fontsize=10)
plt.grid(alpha=.5, linestyle='-')
sns.lineplot(data=df['Cases/day'])
st.pyplot(fig)


st.header('Recovered/day')
fig = plt.figure(figsize=(16, 8))
plt.xticks(rotation=45)
plt.xticks(fontsize=10)
plt.grid(alpha=.5, linestyle='-')
sns.lineplot(data=df['Recovered/day'])
st.pyplot(fig)

st.header('Deads/day')
fig = plt.figure(figsize=(16, 8))
plt.xticks(rotation=45)
plt.xticks(fontsize=10)
plt.grid(alpha=.5, linestyle='-')
sns.lineplot(data=df['Deads/day'], color='black')
st.pyplot(fig)

if the_country == 'Hungary':
    st.subheader('Alapbetegségek gyakorisága')
    alapbetegsegek = hf['Alapbetegségek'].str.split(',', expand=True).stack()
    alapbetegsegek = alapbetegsegek.str.strip()
    alapbetegsegek = alapbetegsegek.apply(
        lambda x: "magas vérnyomás" if "vérnyomás" in x else x)
    alapbetegsegek = alapbetegsegek.apply(
        lambda x: "cukorbetegség" if "cukor" in x else x)
    alapbetegsegek = alapbetegsegek.apply(
        lambda x: "adat feltöltés alatt" if "adat" in x or 'nem' in x else x)
    alapbetegsegek = alapbetegsegek.apply(
        lambda x: "hasnyálmirigy-gyulladás" if "hasnyál" in x else x)

    alapfreq = alapbetegsegek.value_counts()
    st.dataframe(alapfreq, width=600)

    c1, c2 = st.columns(2)
    c1.subheader('Átlag életkorok')
    c1.markdown(f'**Férfi:** *{avg_man}* év **Nő:** *{avg_wmn}* év')

    c2.subheader('Nemek szerinti megoszlás')
    c2.markdown(
        f"**Férfi:** {round(gr['Eset/Nem'][0]/m_dead*100,2)}% **Nő:** {round(gr['Eset/Nem'][1]/m_dead*100,2)}%")

    st.subheader('Korosztályos megoszlás')
    st.bar_chart(gf['Eset/Korcsoport'], height=350,
                 use_container_width=True)

    st.header('Megyei adatok')
    try:
        df = pd.read_csv('./korona_megyei.csv', sep=',')
    except:
        df = pd.read_csv(
            'https://raw.githubusercontent.com/mollac/CoVid-19/master/korona_megyei.csv', sep=',')

    datumok = df['Dátum']
    df['Dátum'] = pd.to_datetime(df['Dátum'])
    df = df.set_index('Dátum', drop=True)

    st.subheader('Új esetek megyénként')
    last2 = df.T.iloc[:, -2:]
    last2['Változás'] = last2.iloc[:, 1] - last2.iloc[:, 0]
    last2 = last2['Változás'].sort_values().astype(int)
    c1, c2 = st.columns(2)
    c2.write(f'Mai új esetek száma: {int(sum(last2))}')
    c1.bar_chart(last2, height=400)
    c2.dataframe(last2)

    megyek = list(df.columns)

    with st.expander('Kiválasztott megyék egy ábrán:'):
        select = st.multiselect('Válassz megyéket:', megyek, [
            'Győr-Moson-Sopron', 'Komárom-Esztergom'])
        if select:
            fig = plt.figure(figsize=(16, 8))
            plt.xticks(rotation=45)
            plt.xticks(fontsize=10)
            plt.grid(alpha=.5, linestyle='-')
            sns.lineplot(data=df[select])
            st.pyplot(fig)

    with st.expander('Összes megye egy ábrán:'):
        fig = plt.figure(figsize=(16, 8))
        plt.xticks(rotation=45)
        plt.xticks(fontsize=10)
        plt.grid(alpha=.5, linestyle='-')
        sns.lineplot(data=df)
        st.pyplot(fig)

    # with st.expander('Megyénként külön ábra:'):
    #     st.warning('Az (y) tengely megyénként eltér!')

    #     c1, c2 = st.columns(2)

    #     for i, megye in enumerate(megyek):
    #         fig = plt.figure(figsize=(8, 6))
    #         plt.title(megye)
    #         plt.grid(alpha=.5, linestyle='-')
    #         sns.lineplot(data=df[megye])
    #         if i % 2 == 0:
    #             # c1.line_chart(df[megye])
    #             c1.pyplot(fig)
    #         else:
    #             # c2.line_chart(df[megye])
    #             c2.pyplot(fig)

    st.subheader('Regisztrált esetszám/megye')
    datum_filter = st.slider('Nap', 0, len(datumok)-1, len(datumok)-1)
    st.bar_chart(df.iloc[datum_filter, :], use_container_width=True)

    # with st.expander(f'Regisztrált esetszámok a {datum_filter}. nap alapján.'):
    #     st.write(df.iloc[datum_filter, :].sort_values(ascending=False))

    url = r'https://hu.wikipedia.org/wiki/Magyarorsz%C3%A1g_megy%C3%A9i'
    dl_ = pd.read_html(url)
    mf = pd.DataFrame(dl_[2][['Megye', 'Népesség']])

    mf.dropna(inplace=True)
    mf.columns = ['megye', 'lakos']

    mf.set_index('megye', drop=True, inplace=True)
    # mf.T.loc['megye',20] = 'Budapest'

    as_list = mf.index.tolist()
    idx = as_list.index('Budapest (főváros)')
    as_list[idx] = 'Budapest'
    mf.index = as_list
    def st_num(x): return int(x.replace('\xa0', ''))

    mf['lakos'] = mf['lakos'].apply(st_num)
    mf['eset'] = df.T.iloc[:, -1]

    st.header('Esetek száma a megye lakosságához viszonyítva')
    mf['százalék'] = round(mf.eset / mf.lakos * 100, 3)
    st.bar_chart(mf[['százalék']])

    hungary = [46.98, 18.97]
    url = 'https://raw.githubusercontent.com/mollac/CoVid-19/master/megye_koord.csv'

    df = pd.read_csv(url, encoding='utf-8')
    df['eset'] = list(mf['százalék'])

    if st.sidebar.button('Save map to map.html'):
        lats = list(df.lat)
        lons = list(df.lon)
        cases = list(df.eset)
        names = list(df.megye)
        map = folium.Map(location=hungary, zoom_start=7,
                         control_scale=True)
        for lat, lon, eset, name in zip(lats, lons, cases, names):
            html = f'<div width=500><h4>{str(name)}</h4><p>Esetszám lakosság-arányosam: <b>{eset}%</b></p></div>'
            map.add_child(folium.Circle(location=[lat, lon],
                                        popup=html,
                                        radius=eset*5000,
                                        color='#bb0000',
                                        fill_color='#ff0000',
                                        fill_opacity=0.4,
                                        fill=True))

        map.save('map.html')

    st.write(pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v10?optimize=true',
        initial_view_state={
            "latitude": 46.98,
            "longitude": 19.57,
            "zoom": 6,
            "pitch": 0
        },
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                df,
                get_position=['lon', 'lat'],
                radius_scale=500,
                get_radius="eset",
                pickable=True,
                opacity=0.25,
                stroked=False,
                get_fill_color=[5, 221, 5, 128],
                filled=True,
                wireframe=False
            ),
            pdk.Layer(
                "HeatmapLayer",
                df,
                opacity=.9,
                get_position=["lon", "lat"],
                threshold=.25,
                get_weight="eset"
            ),
            # pdk.Layer(
            #     "TextLayer",
            #     df,
            #     pickable=True,
            #     get_position=["lon", "lat"],
            #     get_text="megye",
            #     get_size=14,
            #     get_color=[255, 255, 100],
            #     get_angle=0,
            #     get_text_anchor="'middle'",
            #     get_alignment_baseline="'center'"
            # )
        ]
    ))
