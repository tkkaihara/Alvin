from data_write import get_symbols, write_min_bars, write_technical_analysis
from trade import market_open, get_account, write_positions, write_submitted_orders, determine_order, sell_all_positions, clear_watchlist
from datetime import datetime
import time

while True:
    # Checking if market is open (all time is in to EST)
    is_open = market_open()['is_open']
    time_until_open_sec = market_open()['time_until_open_sec']
    time_until_close_sec = market_open()['time_until_close_sec']
    desired_selloff_time_sec = 15 * 60

    if is_open:
        # Current buying power
        buying_power = float(get_account()['daytrading_buying_power'])
        # Writing all positions and orders
        write_submitted_orders()
        write_positions()  # Positions that are in Alpacas' system
        # Extracting and setting symbols to analyze
        symbols_list = (get_symbols()[0])
        symbols = (get_symbols()[1])
        # Writing data retrieved and calculated to ohlc/
        write_min_bars(symbols)
        write_technical_analysis(symbols_list)

        if time_until_close_sec > desired_selloff_time_sec:
            # Buying/Selling stock as needed
            determine_order(symbols_list, buying_power)
        else:
            write_positions()
            clear_watchlist(symbols_list)
            sell_all_positions(time_until_close_sec)
    else:
        # Waiting until market opens
        print(f'Going to sleep...💤😴...for {time_until_open_sec} seconds...')
        time.sleep(time_until_open_sec)