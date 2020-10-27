from config import *
from datetime import datetime
import requests, json
import btalib
import pandas as pd


def get_symbols():
    holdings = open('data/qqq.csv').readlines()
    symbols_list = [
        'UVXY', 'SVXY', 'SPPI', 'FSLY', 'PINS', 'TWTR', 'CHGG', 'ETSY', 'CVNA',
        'LPCN', 'AMD', 'BA', 'MU', 'ADMP', 'SQQQ', 'SPXS', 'LABU', 'LABD',
        'AAL', 'UAL', 'DAL', 'JBLU', 'LUV', 'SAVE', 'BA', 'SNAP', 'NIO',
        'AAPL', 'MSFT', 'FBIO', 'SPPI', 'KALA', 'DOGZ', 'MRIN', 'SCKT', 'AMZN',
        'FB', 'GOOGL', 'GOOG', 'TSLA', 'NVDA', 'PYPL', 'ADBE', 'INTC', 'NFLX',
        'CMCSA', 'PEP', 'COST', 'CSCO', 'AVGO', 'QCOM', 'TMUS', 'AMGN', 'TXN',
        'CHTR', 'SBUX', 'ZM', 'AMD', 'INTU', 'ISRG', 'MDLZ', 'JD', 'GILD',
        'BKNG', 'FISV', 'MELI', 'ATVI', 'ADP', 'CSX', 'REGN', 'MU', 'AMAT',
        'ADSK', 'VRTX', 'LRCX', 'ILMN', 'ADI', 'BIIB', 'MNST', 'EXC', 'KDP',
        'LULU', 'DOCU', 'WDAY', 'CTSH', 'KHC', 'NXPI', 'BIDU', 'XEL', 'DXCM',
        'EBAY', 'EA', 'IDXX', 'CTAS', 'SNPS', 'ORLY', 'SGEN', 'SPLK', 'ROST',
        'WBA', 'KLAC', 'NTES', 'PCAR', 'CDNS', 'MAR', 'VRSK', 'PAYX', 'ASML',
        'ANSS', 'MCHP', 'XLNX', 'MRNA', 'CPRT', 'ALGN', 'PDD', 'ALXN', 'SIRI',
        'FAST', 'SWKS', 'VRSN', 'DLTR', 'CERN', 'MXIM', 'INCY', 'TTWO', 'CDW',
        'CHKP', 'CTXS', 'TCOM', 'BMRN', 'ULTA', 'EXPE', 'FOXA', 'LBTYK', 'FOX',
        'LBTYA'
    ]
    symbols = ','.join(symbols_list)
    return symbols_list, symbols


get_symbols()


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

            dataframe['SMA-6'] = sma6.df
            dataframe['SMA-9'] = sma9.df
            dataframe['SMA-10'] = sma10.df
            dataframe['SMA-20'] = sma20.df
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