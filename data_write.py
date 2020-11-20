from config import *
from datetime import datetime, timedelta
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
        'AMD', 'UVXY', 'SVXY', 'SPXL', 'SPXS', 'LABU', 'LABD', 'NIO', 'TWTR',
        'UBER', 'LYFT', 'FNGU', 'FNGD', 'UCO', 'SCO', 'VXRT'
    ]
    symbols = ','.join(symbols_list)
    return symbols_list, symbols


def write_min_bars(symbols):
    minute_bars_url = '{}/5Min?symbols={}&limit=50'.format(BARS_URL, symbols)
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


# Makes sure that bar data is equally spaced out
def check_bar_data(symbol, length):
    data_sheet = open(f'data/ohlc/{symbol}.csv').readlines()
    timestamps = [data_line.split(',')[0]
                  for data_line in data_sheet][-length:]
    bars_are_consistent = None
    count = 0
    for timestamp in timestamps[:-1]:
        FMT = '%I:%M%p_%Y-%m-%d'
        tdelta = datetime.strptime(timestamps[count + 1],
                                   FMT) - datetime.strptime(
                                       timestamps[count], FMT)
        print(tdelta)
        if tdelta == 300:
            bars_are_consistent = True
        else:
            bars_are_consistent = False
            break
        count += 1
    return bars_are_consistent


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
            sub_SMA6_SMA20 = btalib.sub(sma6, sma20)

            dataframe['SMA-6'] = round(sma6.df, 3)
            dataframe['SMA-9'] = round(sma9.df, 3)
            dataframe['SMA-10'] = round(sma10.df, 3)
            dataframe['SMA-20'] = round(sma20.df, 3)
            dataframe['RSI'] = round(rsi.df, 2)
            dataframe['MACD'] = round(macd.df['macd'], 2)
            dataframe['Signal'] = round(macd.df['signal'], 2)
            dataframe['Histogram'] = macd.df['histogram']
            dataframe['Delta_SMA6_SMA20'] = round(sub_SMA6_SMA20.df, 4)

            f = open(file_path, 'w+')
            dataframe.to_csv(file_path, sep=',', index=True)
            f.close()
        except:
            print(f'{symbol} is not writing the technical data.')
