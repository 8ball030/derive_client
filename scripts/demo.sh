#!/usr/bin/env bash

set -euo pipefail

SLEEP_TIME=4

clear
cowsay "The Derive client offers both a library and CLI tool to manage positions on Derive."
sleep $SLEEP_TIME
clear

cowsay "The client can be installed from pip:"
echo "pip install derive-client"
sleep $SLEEP_TIME
clear

cowsay "Once installed, we can interact with Derive programmatically via the CLI."
echo drv --help
drv --help
sleep $SLEEP_TIME
clear

# Account
cowsay "Let's start by querying our account details."
echo drv account get
drv account get
sleep $SLEEP_TIME
clear

cowsay "We can also view our subaccount portfolios."
echo drv account portfolios
drv account portfolios
sleep $SLEEP_TIME
clear

# Markets
cowsay "Next, let's explore market data. We can list all available currencies..."
echo drv market currency --all
drv market currency --all
sleep $SLEEP_TIME
clear

cowsay "...query instruments by currency and type..."
echo drv market instrument -c ETH -t option
drv market instrument -c ETH -t option
sleep $SLEEP_TIME
clear

cowsay "...and check real-time ticker data."
echo drv market ticker ETH-PERP
drv market ticker ETH-PERP
sleep $SLEEP_TIME
clear

# Orders
cowsay "Now for the fun part: let's place an order! How about buying ETH-PERP at \$100?"
sleep $SLEEP_TIME
clear

cowsay "...I mean, you never know, right?"
echo drv order create ETH-PERP buy -a 0.1 -p 100
drv order create ETH-PERP buy -a 0.1 -p 100
sleep $SLEEP_TIME
clear

cowsay "Let's check if anyone's desperate enough to sell at that price..."
echo drv order list-open
drv order list-open
sleep $SLEEP_TIME
clear

cowsay "Yeah, thought so. Let's cancel that pipe dream."
echo drv order cancel-all
drv order cancel-all
sleep $SLEEP_TIME
clear

# Positions
cowsay "On second thought, maybe I'm long enough already. Let's check our positions."
echo drv position list
drv position list
sleep $SLEEP_TIME
clear

cowsay "And that's only part of the CLI. Try the library for RFQs, bridging, and full market interactions."
sleep $SLEEP_TIME
clear
