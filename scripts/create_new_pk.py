"""
Helpful script to create a new ethereum key pair.
"""
from eth_account import Account

def main():
    """
    Create a new ethereum key pair and print it to the console.
    """
    account = Account.create()
    print(f"Address: {account.address}")
    print(f"Private Key: {account.key.hex()}")

if __name__ == "__main__":
    main()