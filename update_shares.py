#! /usr/bin/env python3

import argparse
import datetime
import os
import json

import colorama

DEFAULT_SHARES_FILE=os.path.join(os.path.expanduser("~"), "pricer.json")
HOLD_FIELD_COUNT=4
DEFAULT_LIMIT=-1  # no limit

dt = datetime.datetime.today().strftime('%Y-%m-%d')

def add(args):
    print("Adding a new position")
    share_data = get_share_data(args.shares_file)

    symbol = args.symbol.upper()
    shares = args.shares
    cost = args.cost
    until = args.until
    if args.date:
        dt = args.date

    # Add the symbol if it isn't already in the share data
    if symbol not in share_data.keys():
        share_data[symbol] = []

    for item, values in share_data.items():
        if item.upper() == symbol:
            share_data[item].append((shares, cost, None, dt))

    set_share_data(args.shares_file, share_data)


def remove(args):
    print("Removing position at index (0 index)")
    share_data = get_share_data(args.shares_file)

    symbol = args.symbol.upper()
    price = args.price
    index = args.index
    if args.date:
        dt = args.date

    for item, values in share_data.items():
        if item.upper() == symbol:
            print("Found {}".format(symbol))
            if len(values) < index:
                print("Invalid position")
                return

            item_count = 0
            held_count = 0
            for item in values:
                # skip sold positions
                if len(values[item_count]) > HOLD_FIELD_COUNT:
                    item_count += 1
                    continue

                # we cound the matching index entry
                if held_count == index:
                    print(f"Removing index {index}")
                    values[item_count].append(price)
                    values[item_count].append(dt)
                    share_data[symbol] = values
                    break

                held_count += 1
                item_count += 1
            break

    set_share_data(args.shares_file, share_data)


def show_closed(args):
    share_data = get_share_data(args.shares_file)

    if 'limit' in args:
        limit = args.limit
    else:
        limit = DEFAULT_LIMIT
    symbol_req = []
    if 'symbol' in args:
        symbol_req = [x.upper() for x in args.symbol]

    show_all = args.show_all

    date = args.date

    total_pl = 0.0
    for symbol, data in share_data.items():
        if not data:  # skip untracked symbold
            continue
        if symbol_req and symbol.upper() not in symbol_req:
            continue

        total = 0.0
        count = 0
        closed = [x for x in data if len(x) > HOLD_FIELD_COUNT]
        if len(closed) == 0:
            continue

        print(symbol.upper())
        total_shares = 0.0
        for item in sorted(closed, key=lambda r: r[5], reverse=True):
            if not show_all and date and date != item[5]:   # only show the given date's trades
                continue
            total_shares += item[0]
            pl = (item[4] - item[1]) * item[0]
            total_pl += pl

            if pl < 0:
                fore = colorama.Fore.RED
            elif pl > 0:
                fore = colorama.Fore.GREEN
            else:
                fore = ""

            end = colorama.Style.RESET_ALL
            if limit == -1 or count + 1 <= limit:
                print(f"    {item[0]}: {fore}$ {pl:.3f}{end}: "
                      f"{item[3]} - {item[5]}: {item[1]} - {item[4]}")
            total += pl
            count += 1
        if len(closed) > 1:
            if total < 0.0:
                fore = colorama.Fore.RED
            elif total > 0.0:
                fore = colorama.Fore.GREEN
            else:
                fore = ""

            end = colorama.Style.RESET_ALL
            print(f"    ==============================")
            print(f"    Total: {total_shares}: ${fore}{total:.3f}{end}")

    if total_pl < 0.0:
        fore = colorama.Fore.RED
    elif total_pl > 0.0:
        fore = colorama.Fore.GREEN
    else:
        fore = ""
    print(f"Grand Total: {fore}{total_pl: .3}{end}")


def show_open(args):
    share_data = get_share_data(args.shares_file)

    symbol_req = []
    if args.symbol:
        symbol_req = [x.upper() for x in args.symbol]

    for symbol, data in share_data.items():
        if not data:  # skip untracked symbold
            continue
        if symbol_req and symbol.upper() not in symbol_req:
            continue

        total = 0.0
        held = [x for x in data if len(x) == HOLD_FIELD_COUNT]
        if len(held) == 0:
            continue

        print(symbol.upper())
        total_shares = 0.0
        held_count = 0
        for item in held:
            # print(f"JOE: show_all: {show_all}, item[3]: {item[3]}, date: {date}")

            pl = item[1] * item[0]
            total_shares += item[0]

            if pl < 0:
                fore = colorama.Fore.RED
            elif pl > 0:
                fore = colorama.Fore.GREEN
            else:
                fore = ""

            end = colorama.Style.RESET_ALL
            print(f"    {item[0]}: ${fore}{pl:.3f}{end}: {item[3]}")
            total += pl

        if len(held) > 1:
            if total < 0.0:
                fore = colorama.Fore.RED
            elif total > 0.0:
                fore = colorama.Fore.GREEN
            else:
                fore = ""

            end = colorama.Style.RESET_ALL
            print(f"    ==============================")
            print(f"    Total: {total_shares}: ${fore}{total:.3f}{end}")


def get_share_data(filename):
    """Get the share information for the user."""
    data = []
    with open(filename) as fp:
        data = json.load(fp)

    return data


def set_share_data(filename, share_data):
    """Write the share information for the user."""

    with open(filename, 'w') as fp:
        json.dump(share_data, fp, indent=1)



def parse_args():
    """Parse commandline options and sub-commands."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--shares-file', '-s',
                        default=DEFAULT_SHARES_FILE,
                        help='JSON data file with shares owned data')
    parser.set_defaults(func=show_closed)

    subparsers = parser.add_subparsers(help='sub-commands')

    parser_add = subparsers.add_parser(
        'add', help='Add a new position held')
    parser_add.add_argument('symbol', help='Stock symbol')
    parser_add.add_argument('shares', type=float, help='Stock shares')
    parser_add.add_argument('cost', type=float, help='Stock share cost')
    parser_add.add_argument('-u', '--until', help='Add until note')
    parser_add.add_argument('-d', '--date', default=dt,
                            help='Date of transaction')
    parser_add.set_defaults(func=add)

    parser_remove = subparsers.add_parser(
        'remove', aliases=['rm'], help='Remove a new position held')
    parser_remove.add_argument('symbol', help='Stock symbol')
    parser_remove.add_argument('price', type=float, help="sell price")
    parser_remove.add_argument('index', type=int, default=0, nargs='?',
                               help='Position index')
    parser_remove.add_argument('-d', '--date', default=dt,
                               help='Date of transaction')
    parser_remove.set_defaults(func=remove)

    parser_show_closed = subparsers.add_parser(
        'show-closed', help='Show closed positions')
    parser_show_closed.add_argument('symbol', nargs='*', help='Stock symbol')
    parser_show_closed.add_argument('-l', '--limit', type=int,
                                    default=DEFAULT_LIMIT,
                                    help='Stock symbol')
    parser_show_closed.add_argument('-d', '--date', default=dt,
                               help='Date of transaction')
    parser_show_closed.add_argument('-a', '--show-all', action='store_true',
                                    help='Show all positions')
    parser_show_closed.set_defaults(func=show_closed)

    parser_show_open = subparsers.add_parser(
        'show-open', help='Show open positions')
    parser_show_open.add_argument('symbol', nargs='*', help='Stock symbol')
    parser_show_open.set_defaults(func=show_open)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    args.func(args)
