#!/usr/bin/env python3

import colorama
import finnhub
import pprint
import time

from config import API_KEY

import os
import json

finnhub_client = finnhub.Client(api_key=API_KEY)
symbol_file = os.path.join(os.path.expanduser('~'), 'pricer.json')
quote_file = os.path.join(os.path.expanduser('~'), 'pricer_quotes.json')

quote_data = {}

with open(symbol_file, 'r') as fp:
    data = json.load(fp)
    symbols = data['open']
    notes = data['notes']
    exclude_symbols = data['excludes']

with open(quote_file) as fp:
    quote_date = json.load(fp)

# Due to strict API usage limitations only query a few symbols
symbols = {x: v for x, v in symbols.items() if x not in exclude_symbols}

comp_cur_value = 0.0
comp_gain = 0.0


for symbol in sorted(symbols):
    time.sleep(0.20)
    shares = symbols[symbol]
    data = finnhub_client.quote(symbol)

    high_day = data['h']
    low_day = data['l']
    open_day = data['o']
    prev_close = data['pc']

    quote_data[symbol] = (prev_close, open_day, low_day, high_day,)

for symbol, data in sorted(quote_data.items()):
    print(f"{symbol}: {data}")

with open(quote_file, 'w') as fp:
    json.dump(quote_data, fp, indent=1)
