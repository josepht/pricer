import argparse
import datetime
import json
import os

#https://pypi.org/project/websocket_client/
import websocket

import colorama

from config import API_KEY

DEFAULT_SHARES_FILE=os.path.join(os.path.expanduser("~"), "pricer.json")
DEFAULT_PRICE_DATA_FILE=os.path.join(os.path.expanduser("~"),
                                     "pricer_price_data.json")

# global data
symbols = []
price_data = {}
end = colorama.Style.RESET_ALL


def on_message(ws, message):
    # Here we would parse the data and add it to a structure or print it or
    # whatever.
    dt = datetime.datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
    data = json.loads(message)

    if data['type'] == 'ping':
        ws.send('{"type":"pong"}')
    elif data['type'] == 'trade':
        updated = False
        for t in data['data']:
            s = t['s']
            if s not in price_data:
                price_data[s] = {}
            p = t['p']
            old_p = price_data[s]['price'] if 'price' in price_data[s] else p
            d = p - old_p

            price_data[s] = {
                'price': p,
                'time': t['t'],
                'delta': d,
            }
            if d != 0.0:
                updated = True
                # print(f"{dt}: {s}: {p: .3f} {t['t']} {d: .3f}")
        if updated:
            show_price_data()
    else:
        print(f"{dt}: {data}")
    update_price_data_file(args.price_data_file)


def show_price_data():

    print("")
    print("")
    for symbol, data in sorted(price_data.items()):
        price = data['price']
        time = data['time']
        delta = data['delta']

        if delta < 0.0:
            fore = colorama.Fore.RED
        elif delta > 0.0:
            fore = colorama.Fore.GREEN
        else:
            fore = ""

        print(f"{symbol}: {fore}{price: .3f} {time} {delta: .3f}{end}")


def on_error(ws, error):
    print(error)

def on_close(ws, *data):
    print("### closed ###")
    print(f"data: {data}")

def on_open(ws):
    for symbol in symbols:
        print(f'symbol: {symbol}')
        ws.send(f'{{"type":"subscribe","symbol":"{symbol}"}}')


def parse_args():
    """Parse commandline options and sub-commands."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--shares-file', '-s',
                        default=DEFAULT_SHARES_FILE,
                        help='JSON data file with shares owned data')
    parser.add_argument('--price-data-file', '-p',
                        default=DEFAULT_PRICE_DATA_FILE,
                        help='JSON price data file')

    return parser.parse_args()


def get_share_data(filename):
    """Get the share information for the user."""
    data = []
    with open(filename) as fp:
        data = json.load(fp)

    return data

def update_price_data_file(data_filename):
    """Store the last price data."""
    with open(data_filename, "w") as fp:
         json.dump(price_data, fp, indent=1)

if __name__ == "__main__":
    args = parse_args()

    share_data = get_share_data(args.shares_file)
    price_data = get_share_data(args.price_data_file)
    symbols = [x for x in share_data['open'].keys()]


    # websocket.enableTrace(True)
    ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={API_KEY}",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()
