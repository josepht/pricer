#! python3
"""Stock price checker.

    Copyright 2020 Joe Talbott.
"""
import argparse
import datetime
import json
import requests
# from pprint import pprint

API_ENDPOINT = (
    "https://query1.finance.yahoo.com/v7/finance/quote"
    "?lang=en-US&region=US&corsDomain=finance.yahoo.com"
)

# Colors
RED = '\033[31m'
GREEN = '\033[32m'
BOLD = '\033[1m'
ENDC = '\033[0m'

DEFAULT_SHARES_FILE = '~/shares.json'
DATA_FILE='pricer_data.json'

MARKET_STATE_CLOSED = 'c'
MARKET_STATE_OPEN = ' '
MARKET_STATE_POST = '*'
MARKET_STATE_PRE = '*'


def append_data(data):
    return
    with open(DATA_FILE, 'a') as fp:
        fp.write('\n')
        json.dump(data, fp)


def color_value(value, color='', percent=False, width=10, precision=4,
                field_width=10, string=False, bold=False):
    cs = ce = ''
    type_str = 'f'
    if string:
        type_str = 's'

    if string:
        value_str = value
    else:
        if percent:
            value_str = '{{:.{}{}}}'.format(precision, type_str).format(value)
        else:
            value_str = '{{:{}.{}{}}}'.format(width,
                                              precision,
                                              type_str).format(value)
    if color == 'red':
        cs = RED
        ce = ENDC
    elif color == 'green':
        cs = GREEN
        ce = ENDC

    if bold:
        cs = '{}{}'.format(cs, BOLD)
        ce = ENDC

    value_str_fmt = '{{:>{}s}}'.format(field_width)
    if percent:
        value_str = value_str_fmt.format(
            '({}%)'.format(value_str))

    value_str = value_str_fmt.format(value_str)

    # add color codes last otherwise they count towards the string length
    if cs:
        value_str = '{}{}{}'.format(cs, value_str, ce)

    return value_str


def get_alert_report(symbol, price, share_data, verbose=False, agg=False):
    report = ""
    symbol_data = share_data
    alert = symbol_data.get('alert', {})
    alert_price_above = alert.get('price_above')
    alert_price_below = alert.get('price_below')
    alert_price = (alert_price_above is not None or
                   alert_price_below is not None)
    hidden = alert.get('hide', False)

    if hidden or not alert_price:
        return report

    if alert and alert_price and not hidden:
        alert_price = ''
        symbol_color = ''
        direction = ''
        if alert_price_above is not None and price > alert_price_above:
            direction = '^'
            symbol_color = 'green'
            alert_price = alert_price_above

        if alert_price_below is not None and price < alert_price_below:
            direction = 'v'
            symbol_color = 'green'
            alert_price = alert_price_below

        if direction == '':
            return report

        kwargs = {}
        if agg:
            kwargs['bold'] = True
        report = "{} {}".format(
            color_value(direction, color=symbol_color, string=True,
                        field_width=1, **kwargs),
            color_value(alert_price, color=symbol_color,
                        precision=2,
                        width=6,
                        field_width=6,
                        **kwargs
                        ),
        )

    return report


def get_owned_report(symbol, price, share_data, verbose=False, agg=False,
                     hold=False, until=None, total_shares=None,
                     avg_price=None):
    sum_line = None
    symbol_data = share_data
    cost = symbol_data.get('cost')
    shares = symbol_data.get('shares')
    if total_shares is not None and total_shares > 0:
        if avg_price is not None:
            avg_price = (
                (shares * cost + total_shares * avg_price) /
                (total_shares + shares)
            )
    else:
        avg_price = cost
        total_shares = 0
    if shares is not None:
        total_shares += shares

    hold_str = ' '

    if hold:
        hold_str = 'H'

    if until is not None:
        hold_str = '{} {}'.format(hold_str, until)

    kwargs = {}
    if agg:
        kwargs['bold'] = True

    if cost is None or shares is None or shares == 0.0:
        # Fake out the column width for alerts
        if verbose:
            owned = ' '*67
        else:
            owned = ' '*57
    else:
        symbol_change = price - cost
        sum_symbol_change = price - avg_price
        symbol_color = ''
        sum_symbol_color = ''

        if symbol_change < 0.0:
            symbol_color = 'red'
        elif symbol_change > 0.0:
            symbol_color = 'green'

        if sum_symbol_change < 0.0:
            sum_symbol_color = 'red'
        elif sum_symbol_change > 0.0:
            sum_symbol_color = 'green'

        symbol_change_percent = symbol_change / cost * 100
        sum_symbol_change_percent = sum_symbol_change / avg_price * 100

        if verbose:
            owned = "{} {} {} {} {} {}".format(
                color_value(cost, color=symbol_color, **kwargs),
                color_value(symbol_change, color=symbol_color, **kwargs),
                color_value(symbol_change_percent,
                            color=symbol_color,
                            precision=2,
                            field_width=10,
                            percent=True, **kwargs),
                color_value(shares, color=symbol_color,
                            precision=2, width=8, **kwargs),
                color_value(shares * symbol_change,
                            field_width=11, precision=2,
                            color=symbol_color, **kwargs),
                color_value(hold_str, field_width=12, string=True,
                            color=symbol_color, **kwargs),
            )
            sum_line = "{} {} {} {} {} {}".format(
                color_value(cost, color=sum_symbol_color, bold=True),
                color_value(symbol_change, color=sum_symbol_color, bold=True),
                color_value(sum_symbol_change_percent,
                            color=sum_symbol_color,
                            precision=2,
                            field_width=10,
                            percent=True, bold=True),
                color_value(total_shares, color=sum_symbol_color,
                            precision=2, width=8, bold=True),
                color_value(total_shares * sum_symbol_change,
                            field_width=11, precision=2,
                            color=sum_symbol_color, bold=True),
                color_value(hold_str, field_width=12, string=True,
                            color=sum_symbol_color, bold=True),
            )
        else:
            owned = "{} {} {} {} {}".format(
                color_value(cost, color=symbol_color, **kwargs),
                color_value(symbol_change_percent,
                            color=symbol_color,
                            precision=2,
                            field_width=10,
                            percent=True, **kwargs),
                color_value(shares, color=symbol_color,
                            precision=2, width=8, **kwargs),
                color_value(shares * symbol_change,
                            field_width=11, precision=2,
                            color=symbol_color, **kwargs),
                color_value(hold_str, field_width=12, string=True,
                            color=symbol_color, **kwargs),
            )
            sum_line = "{} {} {} {} {}".format(
                color_value(avg_price, color=sum_symbol_color, bold=True),
                color_value(sum_symbol_change_percent,
                            color=sum_symbol_color,
                            precision=2,
                            field_width=10,
                            percent=True, bold=True),
                color_value(total_shares, color=sum_symbol_color,
                            precision=2, width=8, bold=True),
                color_value(total_shares * sum_symbol_change,
                            field_width=11, precision=2,
                            color=sum_symbol_color, bold=True),
                color_value(hold_str, field_width=12, string=True,
                            color=sum_symbol_color, bold=True),
            )

    return owned, total_shares, avg_price, sum_line


def get_price_data(market_state, symbol_data):

    market_state_str = '*' if market_state != 'REGULAR' else ' '
    price = change = percent = None

    if market_state in ['PRE']:
        price = symbol_data.get('preMarketPrice')
        change = symbol_data.get('preMarketChange')
        percent = symbol_data.get('preMarketChangePercent')
        market_state_str = MARKET_STATE_PRE

        # if there is no pre-market data get any post market data
        if price is None:
            price, change, percent, market_state_str = get_price_data(
                'POST', symbol_data)
    elif market_state in ['POST', 'POSTPOST']:
        price = symbol_data.get('postMarketPrice')
        change = symbol_data.get('postMarketChange')
        percent = symbol_data.get('postMarketChangePercent')
        market_state_str = MARKET_STATE_POST
    elif market_state == 'CLOSED':
        market_state_str = MARKET_STATE_CLOSED

    # If there isn't any post-market data use the regular data.
    if (
        price is None or change is None or percent is None or
        change == 0.0
    ):
        price = float(symbol_data.get('regularMarketPrice'))
        change = float(symbol_data.get('regularMarketChange'))
        percent = float(symbol_data.get('regularMarketChangePercent'))
        if market_state == 'CLOSED':
            market_state_str = MARKET_STATE_CLOSED
        else:
            market_state_str = MARKET_STATE_OPEN

    price = float(price)
    change = float(change)
    percent = float(percent)

    return price, change, percent, market_state_str


def get_market_data(data, symbol):
    for item in data:
        if item.get('symbol') == symbol:
            return item
    return None


def get_current_price(symbols=None, shares_file=DEFAULT_SHARES_FILE,
                      verbose=False):
    all_share_data = get_share_data(shares_file)
    share_data = all_share_data.get('own')
    data_file = "pricer.dat"
    data_record = {}
    try:
        # with open(data_file) as fp:
        #     data_record = json.load(fp)
        pass
    except IOError:
        pass

    if symbols is None:
        symbols = list(set(x['name'] for x in share_data))

    string_fields = [
        'symbol',
        'marketState',
        'regularMarketPrice',
    ]
    float_fields = [
        'regularMarketChange',
        'regularMarketChangePercent',
        'preMarketPrice',
        'preMarketChange',
        'preMarketChangePercent',
        'postMarketPrice',
        'postMarketChange',
        'postMarketChangePercent',
    ]
    fields = string_fields + float_fields
    result = requests.get(
        API_ENDPOINT,
        params={
            'symbols': ','.join(symbols),
            'fields': ','.join(fields),
        },
        headers={
            'User-Agent': '',
        },
    )
    if result.status_code == 200:
        data = result.json()

        response = data.get('quoteResponse')
        if response is not None:
            data = response

        data_result = data.get('result')
        data_error = data.get('error')
        if data_error is not None:
            print("data_error: {}".format(data_error))
        if data_result is not None:
            data = data_result

        symbols_seen = []
        last_symbol = None
        last_symbol_count = 0
        sum_line = None
        for item in share_data:
            symbol = item['name'].upper()
            hide = item.get('hide', False)
            agg = item.get('agg', False)
            hold = item.get('hold', False)
            until = item.get('until')
            alias = item.get('alias')
            skip_record = item.get('skip_record', True)
            positions = item.get('positions', [])
            if until is not None:
                hold = True
            if hide:
                continue
            market_data = get_market_data(data, symbol)

            market_state = market_data.get('marketState')
            if symbol != 'ES=F' and market_state not in ['PREPRE', 'POSTPOST', 'CLOSED']:
                append_data(market_data)
            # print("JOE: market_state: {}".format(market_state))
            # pprint(market_data)
            state = market_data.get('marketState')
            price = float(market_data.get('regularMarketPrice', 0.0))
            change = float(market_data.get('regularMarketChange', 0.0))
            percent = float(market_data.get('regularMarketChangePercent', 0.0))
            record_time = market_data.get('regularMarketTime')
            record_type = "regular"
            if state == 'PRE':
                price = float(market_data.get('preMarketPrice', market_data.get('regularMarketPrice')))
                change = float(market_data.get('preMarketChange', market_data.get('regularMarketChange')))
                percent = float(market_data.get('preMarketChangePercent', market_data.get('regularMarketChangePercent')))
                record_time = market_data.get('preMarketTime')
                record_type = "pre"
            elif state == 'POST':
                price = float(market_data.get('postMarketPrice', market_data.get('regularMarketPrice')))
                change = float(market_data.get('postMarketChange', market_data.get('regularMarketChange')))
                percent = float(market_data.get('postMarketChangePercent', market_data.get('regularMarketChangePercent')))
                record_time = market_data.get('postMarketTime')
                record_type = "post"
            symbol_data = data_record.setdefault(symbol, {})
            symbol_price_data =  {
                "price": price,
                "change": change,
                "percent": percent,
                "market_state": market_state,
                "type": record_type,
            }
            if not skip_record:
                if record_time is not None and record_time != "null":
                    symbol_data[record_time] = symbol_price_data

            price, change, percent, market_state_str = get_price_data(
                market_state, market_data)

            color = ''
            if change < 0:
                color = 'red'
            elif change > 0.0:
                color = 'green'

            change = color_value(change, color=color, width=9)
            percent = color_value(percent, color=color, precision=2,
                                  field_width=10,
                                  percent=True)
            price_str = color_value(price, precision=4, bold=True)
            sym = symbol
            if alias is not None:
                sym = alias
            line = "{:>7s} {} {} {} {:>1s}".format(
                sym, price_str, change, percent, market_state_str)

            if symbol in symbols_seen and last_symbol == symbol:
                line = "{:>42s}".format("")
            else:
                symbols_seen.append(symbol)

            if symbol == last_symbol:
                last_symbol_count += 1
            else:
                total_shares = None
                avg_price = None
                if sum_line is not None and last_symbol_count > 0:
                    sum_line = "{} {}".format("{:>42s}".format(""), sum_line)
                    print(sum_line)
                last_symbol_count = 0
                sum_line = None
            last_symbol = symbol

            # Add user's owned shares info
            positions = [x for x in positions if not x.get('hide', False)]
            if positions:
                index = 0
                non_hidden_positions = 0
                show_alert = False
                for position in positions:
                    if index != 0:
                        line = "{:>42s}".format("")
                    share_data = position
                    if share_data.get('hide', False):
                        continue
                    non_hidden_positions += 1
                    until = share_data.get('until')
                    hold = share_data.get('hold', False)
                    if until is not None:
                        hold = True

                    owned, total_shares, avg_price, sum_line = get_owned_report(
                        symbol, price, share_data,
                        verbose=verbose, agg=agg, hold=hold,
                        until=until,
                        total_shares=total_shares, avg_price=avg_price
                    )

                    if owned:
                        line = "{} {}".format(line, owned)

                    if not show_alert:
                        alert = get_alert_report(symbol, price, item,
                                                verbose=verbose, agg=agg)

                        if alert:
                            line = "{} {}".format(line, alert)
                            show_alert = True
                    print(line)
                    index += 1
                if (
                    sum_line is not None and
                    len(positions) > 1 and
                    non_hidden_positions > 1
                ):
                    sum_line = "{} {}".format("{:>42s}".format(""), sum_line)
                    print(sum_line)
            else:
                share_data = item
                owned, total_shares, avg_price, sum_line = get_owned_report(
                    symbol, price, share_data,
                    verbose=verbose, agg=agg, hold=hold,
                    until=until,
                    total_shares=total_shares, avg_price=avg_price
                )

                alert = get_alert_report(symbol, price, item,
                                         verbose=verbose, agg=agg)

                if owned:
                    line = "{} {}".format(line, owned)

                if alert:
                    line = "{} {}".format(line, alert)
                print(line)

    # with open(data_file, 'w') as fp:
    #     json.dump(data_record, fp)


def query_one(args):
    get_current_price(symbols=[args.symbol], shares_file=args.shares_file,
                      verbose=args.verbose)


def query_all(args):
    get_current_price(shares_file=args.shares_file,
                      verbose=args.verbose)


def remove(args):
    print("Removing position at index (0 index)")

    all_share_data = get_share_data(args.shares_file)
    share_data = all_share_data.get('own')
    sold_data = all_share_data.setdefault('sold', {})

    symbol = args.symbol.lower()
    index = args.index

    for item in share_data:
        if item['name'].lower() == symbol:
            print("Found {}".format(symbol))
            if len(item['positions']) < index:
                print("Invalid position")
                return

            # skip hidden entries
            while item['positions'][index].get('hide', False):
                index += 1
                continue

            item['positions'][index]['hide'] = True
            item['positions'][index]['note'] = (
                "Deleted automatically ({})".format(datetime.datetime.now())
            )

            sold_data.get(item['name'], []).append(item['positions'][index])
            del(item['positions'][index])

    set_share_data(args.shares_file, all_share_data)


def until(args):
    print("Adding until")

    all_share_data = get_share_data(args.shares_file)
    share_data = all_share_data.get('own')

    symbol = args.symbol.lower()
    index = args.index
    until = args.until

    for item in share_data:
        if item['name'].lower() == symbol:
            print("Found {}".format(symbol))
            if len(item['positions']) < index:
                print("Invalid position")
                return

            # skip hidden entries
            while item['positions'][index].get('hide', False):
                index += 1
                continue

            item['positions'][index]['until'] = until

    set_share_data(args.shares_file, all_share_data)


def deuntil(args):
    print("Removing until")

    all_share_data = get_share_data(args.shares_file)
    share_data = all_share_data.get('own')

    symbol = args.symbol.lower()
    index = args.index

    for item in share_data:
        if item['name'].lower() == symbol:
            print("Found {}".format(symbol))
            if len(item['positions']) < index:
                print("Invalid position")
                return

            # skip hidden entries
            while item['positions'][index].get('hide', False):
                index += 1
                continue

            if item['positions'][index].get('until') is not None:
                del(item['positions'][index]['until'])

    set_share_data(args.shares_file, all_share_data)



def add(args):
    print("Adding a new position")
    all_share_data = get_share_data(args.shares_file)
    share_data = all_share_data.get('own')

    symbol = args.symbol.lower()
    shares = args.shares
    cost = args.cost
    until = args.until

    # Add the symbol if it isn't already in the share data
    if symbol not in [x['name'] for x in share_data]:
        share_data.append({'name': symbol, 'positions': []})

    for item in share_data:
        if item['name'].lower() == symbol:
            datum = {
                'cost': cost,
                'shares': shares,
            }
            if until is not None:
                datum['until'] = until
            item['positions'].append(datum)
            item['positions'] = sorted(item['positions'], key=lambda r: r['cost'])
            positions = item['positions']

    set_share_data(args.shares_file, all_share_data)


def sub(args):
    print("Subtracting share from a position")
    all_share_data = get_share_data(args.shares_file)
    share_data = all_share_data.get('own')
    sold_data = all_share_data.setdefault('sold', {})

    symbol = args.symbol.lower()
    shares = args.shares
    index = args.index

    # Add the symbol if it isn't already in the share data
    if symbol not in [x['name'] for x in share_data]:
        print("ERROR: {} not found".format(symbol))
        return

    for item in share_data:
        if item['name'].lower() == symbol:
            print("Found {}".format(symbol))
            if len(item['positions']) < index:
                print("Invalid position")
                return

            # skip hidden entries
            while item['positions'][index].get('hide', False):
                index += 1
                continue

            # XXX: handle incorrect share amounts i.e. > total, negative, etc.
            item['positions'][index]['shares'] -= shares
            sold_data.setdefault(item['name'], []).append({
                'shares': shares,
                'cost': item['positions'][index]['cost'],
                'note': (
                    "Removed ({})".format(datetime.datetime.now())
                ),
            })
            item['positions'] = (
                sorted(item['positions'], key=lambda r: r['cost'])
            )
            positions = item['positions']

    set_share_data(args.shares_file, all_share_data)


def increment(args):
    print("Incrementing shares for a position")
    all_share_data = get_share_data(args.shares_file)
    share_data = all_share_data.get('own')

    symbol = args.symbol.lower()
    shares = args.shares
    index = args.index

    # Add the symbol if it isn't already in the share data
    if symbol not in [x['name'] for x in share_data]:
        print("ERROR: {} not found".format(symbol))
        return

    for item in share_data:
        if item['name'].lower() == symbol:
            print("Found {}".format(symbol))
            if len(item['positions']) < index:
                print("Invalid position")
                return

            # skip hidden entries
            while item['positions'][index].get('hide', False):
                index += 1
                continue

            # XXX: handle incorrect share amounts i.e. > total, negative, etc.
            item['positions'][index]['shares'] += shares
            item['positions'] = (
                sorted(item['positions'], key=lambda r: r['cost'])
            )
            positions = item['positions']

    set_share_data(args.shares_file, all_share_data)


def check(args):
    """Check the return for selling a non-held stock based on the given
       cost, number of shares, and sell price."""
    diff = args.shares * (args.sell_price - args.buy_price)
    print(diff)


def check_sell(args):
    """Check the return for selling a given stock at a given price based
       on current holdings."""
    all_share_data = get_share_data(args.shares_file)
    share_data = all_share_data.get('own')
    ret = None

    for item in share_data:
        symbol = item.get('symbol')
        if symbol is not None:
            symbol = symbol.lower()

        if symbol is not None and symbol == args.symbol.lower():
            cost = item.get('cost', 0.0)
            shares = item.get('shares', 0.0)

            ret = shares * (args.price - cost)
            break

    if ret is not None:
        print(ret)


def parse_args():
    """Parse commandline options and sub-commands."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--shares-file', '-s',
                        default=DEFAULT_SHARES_FILE,
                        help='JSON data file with shares owned data')
    parser.add_argument('--verbose', '-v', action='store_true',
                        default=False,
                        help='Show more data')
    parser.set_defaults(func=query_all)

    subparsers = parser.add_subparsers(help='sub-commands')
    parser_check = subparsers.add_parser(
        'check', help='Check return on a transaction')
    parser_check.add_argument('buy_price', type=float,
                              help='Buy price for stock',)
    parser_check.add_argument('sell_price', type=float,
                              help='Sell price for stock',)
    parser_check.add_argument('shares', type=float,
                              help='Number of shares of the stock',)
    parser_check.set_defaults(func=check)

    parser_check_stock = subparsers.add_parser(
        'check_sell', help='Check sell scenario for a specific stock')
    parser_check_stock.add_argument('symbol',
                                    help='Stock symbol')
    parser_check_stock.add_argument('price', type=float,
                                    help='Sell price')
    parser_check_stock.set_defaults(func=check_sell)

    parser_query_one = subparsers.add_parser(
        'query_one', help='Query one symbol')
    parser_query_one.add_argument('symbol',
                                  help='Stock symbol')
    parser_query_one.set_defaults(func=query_one)

    parser_query_all = subparsers.add_parser(
        'query_all', help='Query all symbols')
    parser_query_all.set_defaults(func=query_all)

    parser_add = subparsers.add_parser(
        'add', help='Add a new position held')
    parser_add.add_argument('symbol', help='Stock symbol')
    parser_add.add_argument('shares', type=float, help='Stock shares')
    parser_add.add_argument('cost', type=float, help='Stock share cost')
    parser_add.add_argument('-u', '--until', help='Add until note')
    parser_add.set_defaults(func=add)

    parser_remove = subparsers.add_parser(
        'remove', aliases=['rm'], help='Remove a new position held')
    parser_remove.add_argument('symbol', help='Stock symbol')
    parser_remove.add_argument('index', type=int, default=0, nargs='?',
                               help='Position index')
    parser_remove.set_defaults(func=remove)

    parser_sub = subparsers.add_parser(
        'sub', aliases=['dec'], help='Add a new position held')
    parser_sub.add_argument('symbol', help='Stock symbol')
    parser_sub.add_argument('shares', type=float, help='Stock shares')
    parser_sub.add_argument('index', type=int, default=0, nargs='?',
                            help='Position index')
    parser_sub.set_defaults(func=sub)

    parser_increment = subparsers.add_parser(
        'increment', aliases=['inc'], help='Add a new position held')
    parser_increment.add_argument('symbol', help='Stock symbol')
    parser_increment.add_argument('shares', type=float, help='Stock shares')
    parser_increment.add_argument('index', type=int, default=0, nargs='?',
                                  help='Position index')
    parser_increment.set_defaults(func=increment)

    parser_deuntil = subparsers.add_parser(
        'deuntil', aliases=['du'], help='Remove an until from a position held')
    parser_deuntil.add_argument('symbol', help='Stock symbol')
    parser_deuntil.add_argument('index', type=int, default=0, nargs='?',
                                help='Position index')
    parser_deuntil.set_defaults(func=deuntil)

    parser_until = subparsers.add_parser(
        'until', help='Remove an until from a position held')
    parser_until.add_argument('symbol', help='Stock symbol')
    parser_until.add_argument('until', help='Until note')
    parser_until.add_argument('index', type=int, default=0, nargs='?',
                                help='Position index')
    parser_until.set_defaults(func=until)

    return parser.parse_args()


def get_share_data(filename):
    """Get the share information for the user."""
    data = []
    with open(filename) as fp:
        data = json.load(fp)

    return data


def set_share_data(filename, share_data):
    """Write the share information for the user."""

    with open(filename, 'w') as fp:
        json.dump(share_data, fp, indent=4)


def main():
    """The main method."""
    args = parse_args()

    args.func(args)


if __name__ == '__main__':
    main()
