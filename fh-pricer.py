import colorama
import finnhub
from config import API_KEY

finnhub_client = finnhub.Client(api_key=API_KEY)

shares = [

    (5, 376.0, None),
    (5, 377.0, None),
    (10, 378.0, None),
    (5, 382.5, None),
    (5, 383.5, None),
]

symbol = 'QQQ'
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

print(f"{fore}{symbol} {price} {delta:.3f} {delta_percent:.3f}%{end}")

tot_count = 0
tot_cost = 0.0
tot_delta = 0.0
tot_percent = 0.0
tot_value = 0.0
tot_items = 0

for share in shares:
    tot_items += 1

    count, cost, hold = share
    delta = price - cost
    delta_percent = (delta / cost) * 100
    value = delta * count

    tot_count += count
    tot_cost += cost
    tot_delta += delta
    tot_percent += delta_percent
    tot_value += value

    if delta_percent < 0:
        fore = colorama.Fore.RED
    elif delta_percent > 0:
        fore = colorama.Fore.GREEN
    else:
        fore = ""

    hold_str = ""
    if hold is not None:
        hold_str = f"{hold}"

    print(f"{fore}    {count:4} {cost:8.02f} {delta:>8.3f} "
          f"{delta_percent:>8.3f}% {value:>8.3f} {hold_str}{end}")

# Show the total values for the symbol
if tot_value < 0:
    fore = colorama.Fore.RED
else:
    fore = colorama.Fore.GREEN

if tot_items > 1:
    print("=================================================================")
    print(f"{fore}Tot {tot_count:4} {tot_cost / tot_items:8.02f} "
          f"{tot_delta / tot_items:>8.3f} "
          f"{tot_percent / tot_items:>8.3f}% {tot_value:>8.3f}{end}")
