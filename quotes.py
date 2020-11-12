from config import *
import requests

quote = QUOTE_URL + "/AAPL"
r = requests.get(ASSETS_URL, headers=HEADERS)
assets = r.json()

symbols = [asset['symbol'] for asset in assets if asset['tradable'] == True]
print(symbols)