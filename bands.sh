#!/bin/bash

PRICE=$1

if [ -z "$PRICE" ]; then
	echo "Usage: $0 <price>";
	exit 1
fi

echo "4k $PRICE sp lp 1.02 * n [ ]P lp 0.99 * p" | dc
