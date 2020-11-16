"""Stock price checker."""
import argparse
import json
import requests

API_ENDPOINT = (
    "https://query1.finance.yahoo.com/v7/finance/quote"
    "?lang=en-US&region=US&corsDomain=finance.yahoo.com"
)

# Colors
RED = '\033[31m'
GREEN = '\033[32m'
BOLD = '\033[1m'
ENDC = '\033[0m'

DEFAULT_SHARES_FILE = 'shares.json'


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
                        **kwargs,
                        ),
        )

    return report


def get_owned_report(symbol, price, share_data, verbose=False, agg=False,
                     hold=False):
    symbol_data = share_data
    cost = symbol_data.get('cost')
    shares = symbol_data.get('shares')
    hold_str = ' '

    if hold:
        hold_str = 'H'

    kwargs = {}
    if agg:
        kwargs['bold'] = True

    if cost is None or shares is None or shares == 0.0:
        # Fake out the column width for alerts
        if verbose:
            owned = ' '*56
        else:
            owned = ' '*46
    else:
        symbol_change = price - cost
        symbol_color = ''

        if symbol_change < 0.0:
            symbol_color = 'red'
        elif symbol_change > 0.0:
            symbol_color = 'green'

        symbol_change_percent = symbol_change / cost * 100

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
                            precision=0, width=6, **kwargs),
                color_value(shares * symbol_change,
                            field_width=11,
                            color=symbol_color, **kwargs),
                color_value(hold_str, field_width=1, string=True,
                            color=symbol_color, **kwargs),
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
                            precision=0, width=6, **kwargs),
                color_value(shares * symbol_change,
                            field_width=11,
                            color=symbol_color, **kwargs),
                color_value(hold_str, field_width=1, string=True,
                            color=symbol_color, **kwargs),
            )

    return owned


def get_price_data(market_state, symbol_data):

    market_state_str = '*' if market_state != 'REGULAR' else ' '
    price = change = percent = None

    if market_state == 'PRE':
        price = symbol_data.get('preMarketPrice')
        change = symbol_data.get('preMarketChange')
        percent = symbol_data.get('preMarketChangePercent')
        market_state_str = '*'

        # if there is no pre-market data get any post market data
        if price is None:
            price, change, percent, market_state_str = get_price_data(
                'POST', symbol_data)
    elif market_state == 'POST':
        price = symbol_data.get('postMarketPrice')
        change = symbol_data.get('postMarketChange')
        percent = symbol_data.get('postMarketChangePercent')
        market_state_str = '*'

    # If there isn't any post-market data use the regular data.
    if (
        price is None or change is None or percent is None or
        change == 0.0
    ):
        price = float(symbol_data.get('regularMarketPrice'))
        change = float(symbol_data.get('regularMarketChange'))
        percent = float(symbol_data.get('regularMarketChangePercent'))
        market_state_str = ' '

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
    share_data = get_share_data(shares_file)

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
    result = requests.get(API_ENDPOINT, params={
        'symbols': ','.join(symbols),
        'fields': ','.join(fields),
    })
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
        for item in share_data:
            symbol = item['name']
            hide = item.get('hide', False)
            agg = item.get('agg', False)
            hold = item.get('hold', False)
            if hide:
                continue
            market_data = get_market_data(data, symbol)

            market_state = market_data.get('marketState')
            price = float(market_data.get('regularMarketPrice'))
            change = float(market_data.get('regularMarketChange'))
            percent = float(market_data.get('regularMarketChangePercent'))

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
            price_str = color_value(price, bold=True)
            line = "{:>5s} {} {} {} {:>1s}".format(
                symbol, price_str, change, percent, market_state_str)

            if symbol in symbols_seen:
                line = "{:>40s}".format("")
            else:
                symbols_seen.append(symbol)

            # Add user's owned shares info
            owned = get_owned_report(symbol, price, item,
                                     verbose=verbose, agg=agg, hold=hold)

            alert = get_alert_report(symbol, price, item,
                                     verbose=verbose, agg=agg)

            if owned:
                line = "{} {}".format(line, owned)

            if alert:
                line = "{} {}".format(line, alert)
            print(line)


def query_one(args):
    get_current_price(symbols=[args.symbol], verbose=args.verbose)


def query_all(args):
    get_current_price(verbose=args.verbose)


def check(args):
    """Check the return for selling a non-held stock based on the given
       cost, number of shares, and sell price."""
    diff = args.shares * (args.sell_price - args.buy_price)
    print(diff)


def check_sell(args):
    """Check the return for selling a given stock at a given price based
       on current holdings."""
    share_data = get_share_data(args.shares_file)
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

    return parser.parse_args()


def get_share_data(filename):
    """Get the share information for the user."""
    data = []
    with open(filename) as fp:
        data = json.load(fp)

    return data


def main():
    """The main method."""
    args = parse_args()

    args.func(args)


if __name__ == '__main__':
    main()
