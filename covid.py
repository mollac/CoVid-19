import sys
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import datetime as datetime
from bs4 import BeautifulSoup as bs
import requests
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

DATA_URL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/"

def load_data(the_file, the_country):
    data = pd.read_csv(the_file)
    data.rename(columns={'Country/Region':'Country', 'Country_Region':'Country'}, inplace=True)
    data = data[data['Country'] == the_country].fillna(0)
    data = data.groupby(['Country']).sum()
    data = data[['Confirmed', 'Recovered', 'Deaths']]
    return (data.iloc[0,0], data.iloc[0,1], data.iloc[0,2]) if not data.empty else (0,0,0)

def main(the_country):
    START_DATE = datetime.date(2020,1,22)
    TODAY_DATE = str(datetime.datetime.today())[:10]
    the_data = dict()
    print('Gathering data: ', end='')
    while str(START_DATE) < TODAY_DATE:
        the_date = START_DATE.strftime('%m-%d-%Y')
        print(the_date, end=', ', flush=True)
        file_name = f'{the_date}.csv'
        data = load_data(DATA_URL + file_name, the_country)
        if sum(data) > 0:
            the_data[str(START_DATE)] = data 
        START_DATE += datetime.timedelta(days=1)
    print(' done!')
    df = pd.DataFrame(the_data).T
    df.columns=['Eset', 'Gyógyult', 'Halott']

    if the_country == 'Hungary':
            url='https://koronavirus.gov.hu/'
            page = requests.get(url)
            soup = bs(page.content, 'html.parser')
            c = soup.find_all(class_ = 'number')
            eset = int(c[0].text)
            gyogyult = int(c[1].text)
            halott = int(c[2].text)
            dfT = df.T
            dfT[TODAY_DATE] = [eset, gyogyult, halott]
            df = dfT.T

    df['Aktív'] = df['Eset']-(df['Gyógyult']+df['Halott'])
    df['Eset+'] = df['Eset'].shift(1)
    df.fillna(0, inplace=True)
    df['EsetD'] = abs(df['Eset'] - df['Eset+'])

    plt.figure(figsize=(20,10), tight_layout=True)
    ax = plt.subplot(211, frameon=False)

    plt.plot(df.index, df['Eset'], 'b-',     label=f"{df['Eset'].max():8} összesen")
    plt.plot(df.index, df['Gyógyult'], 'g--', label=f"{df['Gyógyult'].max():8} gyógyult")
    plt.plot(df.index, df['Halott'], 'r-',    label=f"{df['Halott'].max():8} halott")
    plt.plot(df.index, df['Aktív'], 'b--',    label=f"{df['Aktív'].max():8} aktív")

    for i,j in df.Eset.items():
        ax.annotate(str(j), xy=(i, j + 2))

    plt.ylabel('Esetszám')
    plt.title(f'CoVid-19: {the_country} {datetime.datetime.today()}')
    plt.legend(shadow=True, fontsize='small')
    plt.xticks(rotation='vertical')

    bx = plt.subplot(212, frameon=True)
    plt.bar(df.index, df['EsetD'], label='Napi növekmény', color='gray')
    plt.ylabel('Napi új eset')
    plt.xticks(rotation='vertical')
    plt.legend(shadow=True, fontsize='small')

    for i,j in df.EsetD.items():
        bx.annotate(j, xy=(i, j + .3))

    plt.savefig(f'{the_country.lower()}.png')
    print(f'Image saved as: {the_country.lower()}.png')
    # plt.show()

if __name__ == '__main__':
    if len(sys.argv) == 1:
        c = 'Hungary'
    else:
        c = sys.argv[1]
main(c)