from data_write import get_symbols, write_min_bars, write_technical_analysis
from trade import market_open, get_account, write_positions, write_submitted_orders, determine_order
from datetime import datetime
import time, pause

while True:
    # Is market open
    is_open = market_open()['is_open']
    time_until_open_sec = market_open()['time_until_open_sec']

    if is_open:
        # Current buying power
        buying_power = float(get_account()['cash'])
        # Writing all positions and orders
        write_submitted_orders()  # Orders that are in Alpacas' system
        write_positions()
        # Extracting and setting symbols to analyze
        symbols_list = (get_symbols()[0])
        symbols = (get_symbols()[1])
        # Writing data retrieved and calculated to ohlc/
        write_min_bars(symbols)
        write_technical_analysis(symbols_list)
        # Buying/Selling stock as needed
        determine_order(symbols_list, buying_power)
        time.sleep(60)
    else:
        # Waiting until market opens
        print(f'Going to sleep...💤😴...for {time_until_open_sec} seconds...')
        time.sleep(time_until_open_sec)
