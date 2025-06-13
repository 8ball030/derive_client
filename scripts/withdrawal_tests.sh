#! /bin/bash

# check if SUBACCOUNT var is set, and set ask if not
if [ -z "$SUBACCOUNT_ID" ]; then
  read -p "Enter the subaccount number: " SUBACCOUNT
fi
if [ -z "$SIGNER_KEY_PATH" ]; then
    read -p "Enter the signer key path: " SIGNER_KEY_PATH
fi
# We check for the derive sc wallet address
if [ -z "$DERIVE_SC_WALLET_ADDRESS" ]; then
  read -p "Enter the Derive SC wallet address: " DERIVE_SC_WALLET_ADDRESS
fi

if [ -z "$SUBACCOUNT_ID" ] || [ -z "$SIGNER_KEY_PATH" ]; then
  echo "Both SUBACCOUNT and SIGNER_KEY_PATH must be set."
  exit 1
fi

if [ ! -f "$SIGNER_KEY_PATH" ]; then
  echo "Signer key file does not exist at $SIGNER_KEY_PATH"
  exit 1
fi



function deposit () {
    local currency=$1
    if [ -z "$currency" ]; then
        echo "No currency specified for deposit."
        return 1
    fi
    local amount=$2
    if [ -z "$amount" ]; then
        amount=1
    fi

    echo "Depositing $currency to subaccount $SUBACCOUNT_ID"
    drv -s $SUBACCOUNT_ID -w $DERIVE_SC_WALLET_ADDRESS -k $SIGNER_KEY_PATH bridge deposit -c BASE     -t $currency -a $amount
    drv -s $SUBACCOUNT_ID -w $DERIVE_SC_WALLET_ADDRESS -k $SIGNER_KEY_PATH bridge deposit -c OPTIMISM -t $currency -a $amount
    drv -s $SUBACCOUNT_ID -w $DERIVE_SC_WALLET_ADDRESS -k $SIGNER_KEY_PATH bridge deposit -c ARBITRUM -t $currency -a $amount
}

function withdraw () {
    local currency=$1
    if [ -z "$currency" ]; then
        echo "No currency specified for withdrawal."
        return 1
    fi
    local amount=$2
    if [ -z "$amount" ]; then
        amount=1
    fi
    echo "Withdrawing $currency from subaccount $SUBACCOUNT_ID"
    drv -s $SUBACCOUNT_ID -w $DERIVE_SC_WALLET_ADDRESS -k $SIGNER_KEY_PATH bridge withdraw -c BASE     -t $currency -a $amount
    drv -s $SUBACCOUNT_ID -w $DERIVE_SC_WALLET_ADDRESS -k $SIGNER_KEY_PATH bridge withdraw -c ARBITRUM -t $currency -a $amount
    drv -s $SUBACCOUNT_ID -w $DERIVE_SC_WALLET_ADDRESS -k $SIGNER_KEY_PATH bridge withdraw -c OPTIMISM -t $currency -a $amount
}

## Working calls
# deposit "USDC"
# withdraw "USDC"
# deposit "OLAS"
# withdraw "OLAS"
# deposit "DRV" 10
# withdraw "DRV" 10


## Working with notes
# currency="weETH"
# amount=0.00001
# deposit "$currency" "$amount"
# withdraw "$currency" "$amount"
# fails on optimism deposit + withdrawal....

# currency="LBTC"
# amount=0.000008
# deposit "$currency" "$amount"
# withdraw "$currency" "$amount"
# Fails on everything other than base.

# Failing?