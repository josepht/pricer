import colorama
import finnhub
import time
from config import API_KEY

import os
import json

finnhub_client = finnhub.Client(api_key=API_KEY)

with open(os.path.join(os.path.expanduser('~'), 'pricer.json'), 'r') as fp:
    data = json.load(fp)
    symbols = data['open']
    notes = data['notes']
    exclude_symbols = data['excludes']

# Due to strict API usage limitations only query a few symbols
symbols = {x: v for x, v in symbols.items() if x not in exclude_symbols}

comp_cur_value = 0.0
comp_gain = 0.0

for symbol in sorted(symbols):
    time.sleep(0.20)
    shares = symbols[symbol]
    data = finnhub_client.quote(symbol)
    price = data['c']
    delta = data['d']
    delta_percent = data['dp']

    if delta_percent < 0:
        fore = colorama.Fore.RED
    elif delta_percent > 0:
        fore = colorama.Fore.GREEN
    else:
        fore = ""

    end = colorama.Style.RESET_ALL

    note = ""
    if symbol in notes:
        note = notes[symbol]

    up = price * 1.02
    down = price * 0.99
    up_down = f" - {up: .2f} {down: .2f}"
    up_down = ""
    print(f"{symbol: <4} {fore}{price: >8.3f} {delta: .3f} "
          f"{delta_percent: .3f}%{end} {note} {up_down}")

    tot_count = 0
    tot_cost = 0.0
    tot_delta = 0.0
    tot_percent = 0.0
    tot_value = 0.0
    tot_items = 0
    tot_cur_value = 0.0

    sym_count = 0
    for share in shares:

        count, cost, hold, date, *rest = share
        if rest:  # This is a sold share
            continue

        tot_items += 1
        delta = price - cost
        delta_percent = (delta / cost) * 100
        value = delta * count
        cur_value = price * count

        tot_count += count
        tot_cost += cost
        tot_delta += delta
        tot_percent += delta_percent
        tot_value += value
        tot_cur_value += cur_value

        if delta_percent < 0:
            fore = colorama.Fore.RED
        elif delta_percent > 0:
            fore = colorama.Fore.GREEN
        else:
            fore = ""

        hold_str = ""
        if hold is not None:
            hold_str = f"{hold}"

        tot_only = False

        if not tot_only:
            print(f"    [{sym_count: 3d}] {count: 8.3g} {fore}{cost: 8.02f} "
                  f"{delta: >8.3f} {delta_percent: >8.3f}% {value: >8.3f}{end} "
                  f"{hold_str: >10} {cur_value: >8.3f}")
        sym_count += 1

    # Show the total values for the symbol
    if tot_value < 0:
        fore = colorama.Fore.RED
    else:
        fore = colorama.Fore.GREEN

    comp_cur_value += tot_cur_value
    comp_gain += tot_value

    if tot_items > 1:
        print("=============================================")
        print(f"Tot       {tot_count: 8.3g} {tot_cost / tot_items: 8.02f} "
              f"{fore}{tot_delta / tot_items: >8.3f} "
              f"{tot_percent / tot_items: >8.3f}% {tot_value: >8.3f}{end}"
              f"  {tot_cur_value: >18.3f}")
        print()

if comp_gain < 0:
    comp_fore = colorama.Fore.RED
else:
    comp_fore = colorama.Fore.GREEN

print(f"{comp_fore}{comp_gain: >55.3f}{end}"
      f"{comp_cur_value: >20.3f}")
