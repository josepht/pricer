#!/bin/bash

PRICE=$1
SWING=$2

if [ $# -ne 2 ]; then
	echo "Usage: $0 <price> <swing %>"
	exit 1
fi

SWING_UP=$(echo "4k $SWING 100 / 1 + p" | dc)
SWING_DOWN=$(echo "4k 1 $SWING 100 / - p" | dc)

# echo "PRICE: $PRICE"
# echo "SWING: $SWING"
# echo "SWING_UP: $SWING_UP"
# echo "SWING_DOWN: $SWING_DOWN"

echo "$PRICE $SWING%: "
echo "4k $PRICE sp lp lp $SWING_UP * p lp $SWING_DOWN * p" | dc
