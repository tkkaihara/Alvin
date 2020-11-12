import requests, json, csv, pause, time, math
from config import *
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


def determine_order(symbols_list, buying_power):
    open_index, low_index, close_index, SMA6_index, SMA9_index, SMA10_index, SMA20_index, RSI_index, MACD_index, signal_index, histogram_index = [
        1, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13
    ]
    number_of_stocks = len(symbols_list)
    for symbol in symbols_list:
        in_orders = is_ordered(symbol)
        in_positions = is_in_positions(symbol)[0]
        unrealized_percentage = float(is_in_positions(symbol)[2])
        SMA20_is_increasing = is_increasing(3, SMA20_index, symbol)
        histogram_is_increasing = is_increasing(2, histogram_index, symbol)
        data_sheet = open(f'data/ohlc/{symbol}.csv').readlines()
        last_data_line = [data_line.split(',') for data_line in data_sheet][-1]
        open_indicator = float(last_data_line[open_index])
        low = float(last_data_line[low_index])
        close = float(last_data_line[close_index])
        SMA6 = float(last_data_line[SMA6_index])
        SMA9 = float(last_data_line[SMA9_index])
        SMA10 = float(last_data_line[SMA10_index])
        SMA20 = float(last_data_line[SMA20_index])
        RSI = float(last_data_line[RSI_index])
        histogram = float(last_data_line[histogram_index])
        message = f'{symbol}, close-SMA9 = {close-SMA9}, close-SMA6 = {close-SMA6}, SMA20 Increasing [3] = {SMA20_is_increasing}, Histogram Increasing = {histogram_is_increasing}'

        if (
                open_indicator < close and open_indicator > SMA9
        ) and SMA9 > SMA20 and histogram_is_increasing and SMA20_is_increasing and not in_positions and not in_orders:
            side = "buy"
            qty = int(math.ceil((buying_power / number_of_stocks) / close))
            print(f'Buying {message}')
            resp = simple_order(symbol, qty, side)
            print(resp)
        elif (close <= SMA9 or not SMA20_is_increasing
              or unrealized_percentage <= -0.2
              or SMA9 <= SMA20) and in_positions and not in_orders:
            side = "sell"
            qty = int(is_in_positions(symbol)[1])
            if qty > 0:
                print(f'Selling {message}')
                resp = simple_order(symbol, qty, side)
                print(resp)
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
    time.sleep(60)


# Sells all positions
def sell_all_positions(time_until_close):
    positions = open('data/positions.csv').readlines()
    symbols_list = [position.split(',')[0].strip()
                    for position in positions][1:]
    for symbol in symbols_list:
        index = symbols_list.index(symbol)
        # quantity = [position.split(',')[1].strip()
        #             for position in positions][1:][index]
        side = "sell"
        qty = int(is_in_positions(symbol)[1])
        print(f'Selling {symbol}, end of trading clean-up')
        resp = simple_order(symbol, qty, side)
        print(resp)
    time.sleep(time_until_close + 10)