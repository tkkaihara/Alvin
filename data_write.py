from config import *
from datetime import datetime
import requests, json
import btalib
import pandas as pd


def get_symbols():
    holdings = open('data/qqq.csv').readlines()
    symbols_list = [holding.split(',')[2].strip() for holding in holdings][1:]
    symbols = ','.join(symbols_list)
    return symbols_list, symbols


def write_min_bars(symbols):
    minute_bars_url = '{}/1Min?symbols={}&limit=100'.format(BARS_URL, symbols)
    r = requests.get(minute_bars_url, headers=HEADERS)
    ohlc_data = r.json()

    for symbol in ohlc_data:
        filename = 'data/ohlc/{}.csv'.format(symbol)
        f = open(filename, 'w+')
        f.write('Timestamp,Open,High,Low,Close,Volume\n')
        for bar in ohlc_data[symbol]:
            t = datetime.fromtimestamp(bar['t'])
            timestamp = t.strftime('%I:%M%p_%Y-%m-%d')
            line = '{},{},{},{},{},{}\n'.format(timestamp, bar['o'], bar['h'],
                                                bar['l'], bar['c'], bar['v'])
            f.write(line)
        f.close()


def write_technical_analysis(symbols_list):
    for symbol in symbols_list:
        try:
            file_path = f'data/ohlc/{symbol}.csv'
            dataframe = pd.read_csv(file_path,
                                    parse_dates=True,
                                    index_col='Timestamp')

            sma6 = btalib.sma(dataframe, period=6)
            sma10 = btalib.sma(dataframe, period=10)
            rsi = btalib.rsi(dataframe)
            macd = btalib.macd(dataframe)

            dataframe['SMA-6'] = sma6.df
            dataframe['SMA-10'] = sma10.df
            dataframe['RSI'] = rsi.df
            dataframe['MACD'] = macd.df['macd']
            dataframe['Signal'] = macd.df['signal']
            dataframe['Histogram'] = macd.df['histogram']

            f = open(file_path, 'w+')
            dataframe.to_csv(file_path, sep=',', index=True)
            f.close()
        except:
            print(f'{symbol} is not writing the technical data.')
            f.close()
