# Authentication

To interact with Derive using the client, you first need to register and configure your accounts. This involves creating a **LightAccount**, **Subaccount**, and **Session Key**.

At the moment, registration is done via the [Derive web app](https://derive.xyz). Programmatic account creation is not yet supported by this client (TODO).

---

## What You Need

1. **Session Key Private Key:**  
   The EOA private key for the session key you registered (this can be the owner EOA or a secondary signer).
2. **LightAccount Address:**  
   The smart contract wallet that holds your funds on Derive.
3. **Subaccount ID:**  
   The trading account within your LightAccount.
   - Currently optional in the client: if omitted, the first subaccount will be used.
   - **Best practice:** always provide explicitly to avoid ambiguity.

---

## Step 1. Generate a Private Key

You can generate a private key using the helper script:

```shell
python ./scripts/create-private-key.py
```

Or use an existing key

## Step 2: Create Your LightAccount

1. Visit [derive.xyz](https://derive.xyz)
2. Connect your wallet and create an account
3. This creates your **LightAccount** (funding wallet)
4. Copy the LightAccount address from the Developer section

---

## Step 3: Create a Subaccount

1. Go to the [Developers](https://www.derive.xyz/developers) section
2. Click **Create Subaccount**
3. Select your margin type: _Standard_ or _Portfolio_
4. Name the subaccount
5. Click **Create Subaccount**

---

## Step 4: Register a Session Key

1. In the [Developers](https://www.derive.xyz/developers) section
2. Click **Register Session Key**
3. Provide the EOA you want to use as a session key (can be the owner or a secondary signer)
4. Select permissions (Admin / Account / Read-only) and expiry
5. Note your **Subaccount ID**

> ⚠️ Important:
>
> - Even the owner EOA must be registered as a session key in order to trade on Derive.
> - This client currently only supports bridging when using the owner EOA. This is a deliberate precaution to prevent confusion and mistakes. See [Bridging & Funding](bridging.md) for details.

---

## Step 5: Store Your Credentials

You will need the following information to use the client:

```bash
export DERIVE_SESSION_KEY=0x742d...  # Required: EOA private key registered as a session key
export DERIVE_WALLET=0x8f5B...       # Required: LightAccount (smart contract wallet) address
export DERIVE_SUBACCOUNT_ID=123456   # Required: Subaccount ID
```

---

Next: [Bridging & Funding](bridging.md) - How to fund your accounts and get ready to trade.
