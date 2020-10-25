import requests, json, csv, pause, pytz
from config import *
from datetime import datetime

pause.until(datetime(2015, 8, 12, 2))


def market_open():
    r = requests.get(CLOCK_URL, headers=HEADERS)
    data = json.loads(r.content)
    time_format = '%Y-%m-%dT%H:%M:%S-04:00'
    timezone_pacific = pytz.timezone('America/Los_Angeles')
    formatted_current_time = datetime.now().astimezone(timezone_pacific)
    formatted_open_time = datetime.strptime(
        data['next_open'], time_format).astimezone(timezone_pacific)
    time_remaining = (formatted_open_time -
                      formatted_current_time).total_seconds()
    data['time_until_open_sec'] = time_remaining
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
        'Symbol, QTY, Current_Price[$], Market_Value[$], Cost_Basis[$], Unrealized_P/L[$] \n'
    )
    for position in positions:
        line = '{}, {}, {}, {}, {}, {}\n'.format(position['symbol'],
                                                 position['qty'],
                                                 position['current_price'],
                                                 position['market_value'],
                                                 position['cost_basis'],
                                                 position['unrealized_pl'])
        f.write(line)
    f.close()


def create_order(symbol, qty, order_class, side, type_of_trade, time_in_force,
                 stop_price):
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": type_of_trade,
        "time_in_force": time_in_force,
        "order_class": order_class,
        "stop_loss": {
            "stop_price": stop_price
        }
    }
    r = requests.post(ORDERS_URL, json=data, headers=HEADERS)
    return json.loads(r.content)


def is_ordered(symbol):
    orders = open('data/orders.csv').readlines()
    symbols_list = [order.split(',')[0].strip() for order in orders][1:]
    return symbol in symbols_list


def is_in_positions(symbol):
    quantity = 0
    positions = open('data/positions.csv').readlines()
    symbols_list = [position.split(',')[0].strip()
                    for position in positions][1:]
    in_position = symbol in symbols_list
    if in_position:
        index = symbols_list.index(symbol)
        quantity = [position.split(',')[1].strip()
                    for position in positions][1:][index]
    return in_position, quantity


def determine_order(symbols_list, buying_power):
    close_index, SMA6_index, SMA10_index = [4, 6, 7]

    for symbol in symbols_list:
        in_orders = is_ordered(symbol)
        in_positions = is_in_positions(symbol)[0]

        data_sheet = open(f'data/ohlc/{symbol}.csv').readlines()
        last_data_line = [data_line.split(',') for data_line in data_sheet][-1]
        close = float(last_data_line[close_index])
        SMA6 = float(last_data_line[SMA6_index])
        SMA10 = float(last_data_line[SMA10_index])

        if SMA6 > SMA10 and not in_orders and not in_positions:  # and is not ordered and not in positions!
            side = 'buy'
            type_of_trade = 'market'
            time_in_force = 'gtc'  # may want to change to 'day'
            order_class = 'bracket'
            qty = (buying_power * 0.01) / close
            stop_price = close - (0.25)
            print(f'Buying {symbol}, SMA6-SMA10 = {SMA6-SMA10}')
            create_order(symbol, qty, side, order_class, type_of_trade,
                         time_in_force, stop_price)
        elif SMA6 < SMA10 and not in_orders and in_positions:  # and is not ordered and is in positions!
            side = 'sell'
            type_of_trade = 'market'
            time_in_force = 'gtc'
            order_class = 'simple'
            stop_price = close
            qty = float(is_in_positions(symbol)[1])
            print(f'Selling {symbol}, SMA6-SMA10 = {SMA6-SMA10}')
            create_order(symbol, qty, side, order_class, type_of_trade,
                         time_in_force, stop_price)
        elif SMA6 < SMA10 and not in_orders and not in_positions:
            print(f'Not trading {symbol}, SMA6-SMA10 = {SMA6-SMA10}')
        elif SMA6 > SMA10 and (in_orders or in_positions):
            print(
                f'Already have a position on {symbol}, SMA6-SMA10 = {SMA6-SMA10}'
            )
        else:
            print(
                'Error with analyzing technical analysis data or orders/positions'
            )
