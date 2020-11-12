from config import *
from datetime import datetime
import requests, json
import btalib
import pandas as pd


def get_all_symbols():
    r = requests.get(ASSETS_URL, headers=HEADERS)
    assets = r.json()
    symbols_list = [
        asset['symbol'].split(',') for asset in assets
        if asset['tradable'] == True
    ]
    symbols = ','.join(symbols_list)
    return symbols_list, symbols


def get_symbols():
    symbols_list = [
        'AMD', 'UVXY', 'SVXY', 'SPXL', 'SPXS', 'LABU', 'LABD', 'NIO', 'PYPL',
        'TWTR', 'UBER', 'LYFT', 'WM', 'FNGU', 'FNGD', 'UCO', 'SCO', 'BLRX',
        'AAPL', 'GE', 'F', 'CCL', 'BAC', 'RIG', 'MDLZ', 'CLX', 'AMC', 'TRVG',
        'BA', 'MU', 'PLUG', 'SNDL', 'BABA', 'PTON', 'BYND', 'CRM', 'ZM',
        'TOUR', 'RDI', 'LIND', 'ITUB', 'CCL', 'TTNP', 'PBR', 'XOM', 'ACB',
        'UCO', 'SCO', 'DCTH', 'STAF', 'SNES', 'OPGN', 'XPEL', 'BLNK', 'AYTU',
        'ACHV', 'IPWR', 'DGLY', 'MJ', 'CGC', 'CRON', 'TLRY', 'FTEK', 'FUBO',
        'NEON', 'NRP', 'KDMN', 'COCP', 'FPRX', 'VXRT', 'ARCT', 'REV', 'BRKS',
        'GRAY', 'PACB', 'AGR', 'MEOH', 'MPLN', 'PFS', 'RPRX', 'VAC', 'WETF'
    ]
    symbols = ','.join(symbols_list)
    return symbols_list, symbols


def write_min_bars(symbols):
    minute_bars_url = '{}/5Min?symbols={}&limit=100'.format(BARS_URL, symbols)
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
            sma9 = btalib.sma(dataframe, period=9)
            sma10 = btalib.sma(dataframe, period=10)
            sma20 = btalib.sma(dataframe, period=20)
            rsi = btalib.rsi(dataframe)
            macd = btalib.macd(dataframe)

            dataframe['SMA-6'] = round(sma6.df, 2)
            dataframe['SMA-9'] = round(sma9.df, 2)
            dataframe['SMA-10'] = round(sma10.df, 2)
            dataframe['SMA-20'] = round(sma20.df, 2)
            dataframe['RSI'] = round(rsi.df, 2)
            dataframe['MACD'] = round(macd.df['macd'], 2)
            dataframe['Signal'] = round(macd.df['signal'], 2)
            dataframe['Histogram'] = macd.df['histogram']

            f = open(file_path, 'w+')
            dataframe.to_csv(file_path, sep=',', index=True)
            f.close()
        except:
            print(f'{symbol} is not writing the technical data.')
            f.close()