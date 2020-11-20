import requests, json, csv, pause, time, math
from config import *
import backtrader as bt
from datetime import datetime, timedelta


def market_open():
    r = requests.get(CLOCK_URL, headers=HEADERS)
    data = json.loads(r.content)
    # Take into account daylight savings
    time_format4 = '%Y-%m-%dT%H:%M:%S-04:00'
    time_format5 = '%Y-%m-%dT%H:%M:%S-05:00'
    formatted_current_time = datetime.now() + timedelta(hours=3)
    try:
        formatted_open_time = datetime.strptime(data['next_open'],
                                                time_format4)
        time_remaining_until_open = (formatted_open_time -
                                     formatted_current_time).total_seconds()
    except:
        formatted_open_time = datetime.strptime(data['next_open'],
                                                time_format5)
        time_remaining_until_open = (formatted_open_time -
                                     formatted_current_time).total_seconds()
    try:
        formatted_close_time = datetime.strptime(data['next_close'],
                                                 time_format4)
        time_remaining_until_close = (formatted_close_time -
                                      formatted_current_time).total_seconds()
    except:
        formatted_close_time = datetime.strptime(data['next_close'],
                                                 time_format5)
        time_remaining_until_close = (formatted_close_time -
                                      formatted_current_time).total_seconds()
    data['time_until_open_sec'] = time_remaining_until_open + 15
    data['time_until_close_sec'] = time_remaining_until_close
    return data


def get_account():
    r = requests.get(ACCOUNT_URL, headers=HEADERS)
    return json.loads(r.content)


def write_submitted_orders():
    r = requests.get(ORDERS_URL, headers=HEADERS)
    orders = json.loads(r.content)
    filename = 'data/orders.csv'
    f = open(filename, 'w+')
    f.write('Symbol, QTY, Side \n')
    for order in orders:
        line = '{}, {}, {}\n'.format(order['symbol'], order['qty'],
                                     order['side'])
        f.write(line)
    f.close()


def write_positions():
    r = requests.get(POSITIONS_URL, headers=HEADERS)
    positions = json.loads(r.content)
    filename = 'data/positions.csv'
    f = open(filename, 'w+')
    f.write(
        'Symbol, QTY, Current_Price[$], Market_Value[$], Cost_Basis[$], Unrealized_P/L[$], Unrealized_P/L[%] \n'
    )
    for position in positions:
        line = '{}, {}, {}, {}, {}, {}, {}\n'.format(
            position['symbol'], position['qty'], position['current_price'],
            position['market_value'], position['cost_basis'],
            position['unrealized_pl'],
            float(position['unrealized_plpc']) * 100)
        f.write(line)
    f.close()


def create_order(symbol, qty, take_profit, order_class, side, type_of_trade,
                 time_in_force, stop_price, limit_price):
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": type_of_trade,
        "time_in_force": time_in_force,
        "order_class": order_class,
        "take_profit": {
            "limit_price": take_profit
        },
        "stop_loss": {
            "stop_price": stop_price,
            "limit_price": limit_price
        }
    }
    r = requests.post(ORDERS_URL, json=data, headers=HEADERS)
    return json.loads(r.content)


def simple_order(symbol, qty, side):
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": "market",
        "time_in_force": "gtc",
    }
    r = requests.post(ORDERS_URL, json=data, headers=HEADERS)
    return json.loads(r.content)


def is_ordered(symbol):
    orders = open('data/orders.csv').readlines()
    symbols_list = [order.split(',')[0].strip() for order in orders][1:]
    return symbol in symbols_list


def is_in_positions(symbol):
    quantity = 0
    unrealized_percentage = 0
    positions = open('data/positions.csv').readlines()
    symbols_list = [position.split(',')[0].strip()
                    for position in positions][1:]
    in_position = symbol in symbols_list
    if in_position:
        index = symbols_list.index(symbol)
        quantity = [position.split(',')[1].strip()
                    for position in positions][1:][index]
        unrealized_percentage = [
            position.split(',')[6].strip() for position in positions
        ][1:][index]

    return in_position, quantity, unrealized_percentage


def is_increasing(length, tech_index, symbol):
    data_sheet = open(f'data/ohlc/{symbol}.csv').readlines()
    techs = [data_line.split(',')[tech_index]
             for data_line in data_sheet][(-length):]
    techs = [float(number_strings) for number_strings in techs]
    is_increasing = None
    i = 0
    for tech in techs[:-1]:
        if techs[i] < techs[i + 1]:
            is_increasing = True
            i += 1
        else:
            is_increasing = False
            break
    return is_increasing


def is_decreasing(length, tech_index, symbol):
    data_sheet = open(f'data/ohlc/{symbol}.csv').readlines()
    techs = [data_line.split(',')[tech_index]
             for data_line in data_sheet][(-length):]
    techs = [float(number_strings) for number_strings in techs]
    is_decreasing = None
    i = 0
    for tech in techs[:-1]:
        if techs[i] > techs[i + 1]:
            is_decreasing = True
            i += 1
        else:
            is_decreasing = False
            break
    return is_decreasing


def is_in_waitlist(symbol):
    # create list of symbols in waitlist to compare against
    data_sheet = open('data/waitlist.csv').readlines()
    data_lines = [data_line.split(',') for data_line in data_sheet][1:]
    waitlist = []
    for line in data_lines:
        waitlist.append(line[0])
    if symbol in waitlist:
        return True
    else:
        return False


def remove_from_waitlist(symbol):
    with open('data/waitlist.csv') as oldfile, open('data/temp.csv',
                                                    'w') as newfile:
        for line in oldfile:
            if symbol not in line:
                newfile.write(line)
    with open('data/temp.csv') as oldfile, open('data/waitlist.csv',
                                                'w') as newfile:
        for line in oldfile:
            newfile.write(line)


def is_in_lowboys(symbol):
    # create list of symbols in waitlist to compare against
    data_sheet = open('data/lowboys.csv').readlines()
    data_lines = [data_line.split(',') for data_line in data_sheet][1:]
    lowboyslist = []
    for line in data_lines:
        lowboyslist.append(line[0])
    if symbol in lowboyslist:
        return True
    else:
        return False


def remove_from_lowboys(symbol):
    with open('data/lowboys.csv') as oldfile, open('data/temp.csv',
                                                   'w') as newfile:
        for line in oldfile:
            if symbol not in line:
                newfile.write(line)
    with open('data/temp.csv') as oldfile, open('data/lowboys.csv',
                                                'w') as newfile:
        for line in oldfile:
            newfile.write(line)


def determine_order(symbols_list, buying_power):
    open_index, low_index, close_index, SMA6_index, SMA9_index, SMA10_index, SMA20_index, RSI_index, MACD_index, signal_index, histogram_index, delta_SMA6_SMA20_index = [
        1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14
    ]
    number_of_stocks = len(symbols_list)

    for symbol in symbols_list:
        in_orders = is_ordered(symbol)
        in_positions = is_in_positions(symbol)[0]
        in_waitlist = is_in_waitlist(symbol)
        in_lowboys = is_in_lowboys(symbol)
        unrealized_percentage = float(is_in_positions(symbol)[2])
        delta_SMA6_SMA20_is_decreasing = is_decreasing(2,
                                                       delta_SMA6_SMA20_index,
                                                       symbol)
        delta_SMA6_SMA20_is_increasing = is_increasing(3,
                                                       delta_SMA6_SMA20_index,
                                                       symbol)
        SMA20_is_increasing = is_increasing(3, SMA20_index, symbol)
        SMA6_is_increasing = is_increasing(3, SMA6_index, symbol)
        close_is_decreasing = is_decreasing(3, close_index, symbol)
        close_is_increasing = is_increasing(4, close_index, symbol)
        histogram_is_increasing = is_increasing(3, histogram_index, symbol)
        histogram_is_decreasing = is_decreasing(2, histogram_index, symbol)
        data_sheet = open(f'data/ohlc/{symbol}.csv').readlines()
        last_data_line = [data_line.split(',') for data_line in data_sheet][-1]
        open_indicator = float(last_data_line[open_index])
        close = float(last_data_line[close_index])
        SMA6 = float(last_data_line[SMA6_index])
        SMA9 = float(last_data_line[SMA9_index])
        SMA10 = float(last_data_line[SMA10_index])
        SMA20 = float(last_data_line[SMA20_index])
        RSI = float(last_data_line[RSI_index])
        histogram = float(last_data_line[histogram_index])
        delta_SMA6_SMA20 = float(last_data_line[delta_SMA6_SMA20_index])
        message = f'{symbol}, SMA6-SMA20 = {delta_SMA6_SMA20}, SMA6-SMA20 Increase = {delta_SMA6_SMA20_is_increasing}, Close Increase = {close_is_increasing}'

        if RSI < 2 and not in_waitlist and not in_lowboys and not in_positions and not in_orders:
            filename = 'data/lowboys.csv'
            f = open(filename, 'a')
            line = '{},{},{},{}\n'.format(symbol, RSI, close, SMA9)
            f.write(line)
            f.close()
            side = "buy"
            qty = int(math.ceil((number_of_stocks / number_of_stocks) / close))
            print(f'Buying {message}')
            resp = simple_order(symbol, qty, side)
            print(resp)
        elif histogram_is_decreasing and in_lowboys and in_positions and not in_orders:
            side = "sell"
            qty = int(is_in_positions(symbol)[1])
            if qty > 0:
                print(f'Selling {message}')
                resp = simple_order(symbol, qty, side)
                print(resp)
                remove_from_lowboys(symbol)
        elif not in_lowboys:
            if (delta_SMA6_SMA20 > 0 and delta_SMA6_SMA20_is_increasing
                    and SMA6_is_increasing and SMA20_is_increasing
                    and close_is_increasing
                    and close > 5) and not in_positions and not in_orders:
                side = "buy"
                qty = int(math.ceil((buying_power / number_of_stocks) / close))
                print(f'Buying {message}')
                resp = simple_order(symbol, qty, side)
                print(resp)
            elif (delta_SMA6_SMA20 <= 0 or delta_SMA6_SMA20_is_decreasing
                  or close_is_decreasing
                  or close < SMA6) and in_positions and not in_orders:
                side = "sell"
                qty = int(is_in_positions(symbol)[1])
                if qty > 0:
                    print(f'Selling {message}')
                    resp = simple_order(symbol, qty, side)
                    print(resp)
                    remove_from_waitlist(symbol)
            elif not in_positions:
                print(f'Not trading {message}')
            elif in_orders:
                print(f'{symbol} is in the order queue')
            elif in_positions:
                print(f'Holding {message}')
            else:
                print(
                    f'{symbol}, Uncaught exception, {message, SMA6, SMA10, histogram, close}'
                )
        else:
            print(f'{symbol} RSI = {RSI}')
    time.sleep(60)


# Waitlist buy strategy
# def determine_order(symbols_list, buying_power):
#     open_index, low_index, close_index, SMA6_index, SMA9_index, SMA10_index, SMA20_index, RSI_index, MACD_index, signal_index, histogram_index = [
#         1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13
#     ]
#     number_of_stocks = len(symbols_list)

#     for symbol in symbols_list:
#         in_orders = is_ordered(symbol)
#         in_positions = is_in_positions(symbol)[0]
#         in_waitlist = is_in_waitlist(symbol)
#         in_lowboys = is_in_lowboys(symbol)
#         unrealized_percentage = float(is_in_positions(symbol)[2])
#         SMA20_is_increasing = is_increasing(3, SMA20_index, symbol)
#         SMA6_is_increasing = is_increasing(3, SMA6_index, symbol)
#         close_is_decreasing = is_decreasing(4, close_index, symbol)
#         close_is_increasing = is_increasing(3, close_index, symbol)
#         histogram_is_increasing = is_increasing(3, histogram_index, symbol)
#         histogram_is_decreasing = is_decreasing(2, histogram_index, symbol)
#         data_sheet = open(f'data/ohlc/{symbol}.csv').readlines()
#         last_data_line = [data_line.split(',') for data_line in data_sheet][-1]
#         open_indicator = float(last_data_line[open_index])
#         close = float(last_data_line[close_index])
#         SMA6 = float(last_data_line[SMA6_index])
#         SMA9 = float(last_data_line[SMA9_index])
#         SMA10 = float(last_data_line[SMA10_index])
#         SMA20 = float(last_data_line[SMA20_index])
#         RSI = float(last_data_line[RSI_index])
#         histogram = float(last_data_line[histogram_index])
#         message = f'{symbol}, RSI = {RSI}, Histogram Increasing [2] = {histogram_is_increasing}, SMA6-SMA9 = {SMA6-SMA9}, Open-SMA9 = {open_indicator-SMA9}, Open-Close = {open_indicator-close}'

#         if RSI < 2 and not in_waitlist and not in_lowboys and not in_positions and not in_orders:
#             filename = 'data/lowboys.csv'
#             f = open(filename, 'a')
#             line = '{},{},{},{}\n'.format(symbol, RSI, close, SMA9)
#             f.write(line)
#             f.close()
#             side = "buy"
#             qty = int(math.ceil((buying_power / 4) / close))
#             print(f'Buying {message}')
#             resp = simple_order(symbol, qty, side)
#             print(resp)
#         elif histogram_is_decreasing and in_lowboys and in_positions and not in_orders:
#             side = "sell"
#             qty = int(is_in_positions(symbol)[1])
#             if qty > 0:
#                 print(f'Selling {message}')
#                 resp = simple_order(symbol, qty, side)
#                 print(resp)
#                 remove_from_lowboys(symbol)
#         elif RSI < 40 and not in_waitlist and not in_lowboys:
#             filename = 'data/waitlist.csv'
#             f = open(filename, 'a')
#             line = '{},{},{},{}\n'.format(symbol, RSI, close, SMA9)
#             f.write(line)
#             f.close()
#         elif RSI >= 50 and in_waitlist and not in_lowboys and not in_positions and not in_orders:
#             remove_from_waitlist(symbol)
#         elif in_waitlist:
#             if SMA6 > SMA9 > SMA20 and not in_lowboys and not in_positions and not in_orders:
#                 side = "buy"
#                 qty = int(
#                     math.ceil(
#                         (buying_power / (number_of_stocks / 20)) / close))
#                 print(f'Buying {message}')
#                 resp = simple_order(symbol, qty, side)
#                 print(resp)
#             elif unrealized_percentage <= -0.3 or RSI > 60 or SMA6 < SMA9 and not in_lowboys and in_positions and not in_orders:
#                 side = "sell"
#                 qty = int(is_in_positions(symbol)[1])
#                 if qty > 0:
#                     print(f'Selling {message}')
#                     resp = simple_order(symbol, qty, side)
#                     print(resp)
#                     remove_from_waitlist(symbol)
#             elif not in_positions and not in_lowboys:
#                 print(f'Not trading {message}')
#             elif in_orders and not in_lowboys:
#                 print(f'{symbol} is in the order queue')
#             elif in_positions and not in_lowboys:
#                 print(f'Holding {message}')
#             else:
#                 print(
#                     f'{symbol}, Uncaught exception, {message, SMA6, SMA10, histogram, close}'
#                 )
#         else:
#             print(f'{symbol} RSI = {RSI}')
#     time.sleep(60)


# Sells all positions
def sell_all_positions(time_until_close):
    positions = open('data/positions.csv').readlines()
    symbols_list = [position.split(',')[0].strip()
                    for position in positions][1:]
    for symbol in symbols_list:
        index = symbols_list.index(symbol)
        side = "sell"
        qty = int(is_in_positions(symbol)[1])
        print(f'Selling {symbol}, end of trading clean-up')
        resp = simple_order(symbol, qty, side)
        print(resp)
        remove_from_waitlist(symbol)
    time.sleep(time_until_close + 10)


# Deletes all stocks from the watchlist
def clear_watchlist(symbols_list):
    for symbol in symbols_list:
        remove_from_waitlist(symbol)


# Deletes all stocks from the lowboyslist
def clear_lowboys(symbols_list):
    for symbol in symbols_list:
        remove_from_lowboys(symbol)


# Backtesting Strategies
class TestStrategy(bt.Strategy):
    def __init__(self):
        self.SMA6, self.SMA9, self.SMA20, self.SMA40 = bt.ind.SMA(
            period=6), bt.ind.SMA(period=9), bt.ind.SMA(period=20), bt.ind.SMA(
                period=40)
        self.RSI = bt.ind.RelativeStrengthIndex()
        self.close = self.datas[0].close
        self.open_indicator = self.datas[0].open

    def next(self):
        size = int(self.broker.getcash() / self.close)

        if self.SMA20 > self.SMA40 and not self.position:
            self.buy(size=size)
        if self.SMA40 > self.SMA20 and self.position.size > 0:
            self.sell(size=self.position.size)

        # if (
        #         self.open_indicator < self.close
        #         and self.open_indicator > self.SMA9
        # ) and self.SMA6 > self.SMA20 and self.SMA6 > self.SMA9 and self.RSI < 40 and not self.position:
        #     self.buy(size=size)
        # if self.close < self.SMA9 and self.position.size > 0:
        #     self.sell(size=self.position.size)

        #  or self.SMA6 < self.SMA20 or self.SMA6 < self.SMA9