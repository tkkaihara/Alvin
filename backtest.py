from data_write import get_symbols
from trade import TestStrategy
import alpaca_backtrader_api
from datetime import datetime
from config import *
import backtrader as bt
import time


def remove_from_backtest(symbol):
    with open('data/backtest.csv') as oldfile, open('data/backtest_temp.csv',
                                                    'w') as newfile:
        for line in oldfile:
            if symbol not in line:
                newfile.write(line)
    with open('data/backtest_temp.csv') as oldfile, open(
            'data/backtest.csv', 'w') as newfile:
        for line in oldfile:
            newfile.write(line)


def clear_watchlist(symbols_list):
    for symbol in symbols_list:
        remove_from_backtest(symbol)


starting_portfolio_value = 100000
symbols_list = get_symbols()[0]
clear_watchlist(symbols_list)
number_of_stocks = len(symbols_list)
portfolio_split = starting_portfolio_value / number_of_stocks

for symbol in symbols_list:
    ALPACA_PAPER = True
    cerebro = bt.Cerebro()
    cerebro.addstrategy(TestStrategy)
    cerebro.broker.setcash(portfolio_split)
    store = alpaca_backtrader_api.AlpacaStore(key_id=API_KEY,
                                              secret_key=SECRET_KEY,
                                              paper=ALPACA_PAPER)
    if not ALPACA_PAPER:
        broker = store.getbroker()
        cerebro.setbroker(broker)

    DataFactory = store.getdata
    data0 = DataFactory(dataname=symbol,
                        historical=True,
                        fromdate=datetime(2019, 11, 13),
                        timeframe=bt.TimeFrame.TFrame("Days"))
    cerebro.adddata(data0)
    # Make the data into 5 min bars
    # cerebro.resampledata(data0, timeframe=bt.TimeFrame.Minutes, compression=5)
    stock_amount_before = cerebro.broker.getvalue()

    cerebro.run()
    stock_amount_after = cerebro.broker.getvalue()
    unrealized_percentage = (stock_amount_after -
                             stock_amount_before) / stock_amount_before * 100
    filename = 'data/backtest.csv'
    f = open(filename, 'a')
    line = '{},{},{},{}\n'.format(symbol, stock_amount_before,
                                  stock_amount_after,
                                  stock_amount_after - stock_amount_before)
    f.write(line)
    f.close()
    # print(round(stock_amount_after, 2))
    print(f'{symbol}, Unrealized % = {round(unrealized_percentage, 2)}')
#   cerebro.plot()
data_sheet = open(f'data/backtest.csv').readlines()[1:]
ending_stock_values = [
    float(data_line.split(',')[2]) for data_line in data_sheet
]
ending_portfolio_value = sum(ending_stock_values)
print(f'Final Portfolio = {ending_portfolio_value}')
net_unrealized = (ending_portfolio_value -
                  starting_portfolio_value) / starting_portfolio_value * 100
print(f'Net Unrealized = {net_unrealized}')
