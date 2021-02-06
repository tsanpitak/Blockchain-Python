# IMPORTS
import os
from dotenv import load_dotenv

import subprocess
import json

from web3 import Web3
from web3.middleware import geth_poa_middleware 
from eth_account import Account

from bit import PrivateKeyTestnet, PrivateKey
from bit.network import NetworkAPI

from constants import *

# SETUP
load_dotenv()
mnemonic = os.getenv("MNEMONIC")

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# FUNCTIONS
def get_wallet_privkey(coin):
    """
    Derive private key for specified coin type
    ---
    Parameter:
    coin - coin type which support by hd-wallet-derive
    """
    command = f'php hd-wallet-derive/hd-wallet-derive.php -g --mnemonic="{mnemonic}" --cols=path,address,privkey,pubkey --coin={coin} --numderive=3 --format=json'
    
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output, err = p.communicate()
    p_status = p.wait()
    
    keys = json.loads(output)
    return keys[0]["privkey"]
#---
def priv_key_to_account(coin, priv_key):
    """
    Convert Private Key of specific coin type to wallet account
    ---
    Parameter:
    coin - coin type (defined in `constants.py`)
    priv_key - private key
    """
    if(coin == ETH):
        #print("ETH Account")
        return Account.privateKeyToAccount(priv_key)
    elif(coin == BTCTEST):
        #print("BTC-Test Account")
        return PrivateKeyTestnet(priv_key)
    elif(coin == BTC):
        return PrivateKey(priv_key)
    else:
        print(f"Unable to process {coin}")
        return ""
#---
def create_eth_tx(account, to, amount):
    """
    Create ETH transaction
    ---
    Parameter:
    account - eth_account Account object
    to - recipient wallet address
    amount - amount to send
    """
    gasEstimate = w3.eth.estimateGas(
        {"from": account.address, "to": to, "value": amount}
    )
    return {
        "from": account.address,
        "to": to,
        "value": amount,
        "gasPrice": w3.eth.gasPrice,
        "gas": gasEstimate,
        "nonce": w3.eth.getTransactionCount(account.address),
    }
#---
def create_tx(coin, account, to, amount):
    """
    Create transaction
    ---
    Parameter:
    coin - coin type (defined in `constants.py`)
    account - eth_account Account object
    to - recipient wallet address
    amount - amount to send
    """
    if(coin == ETH):
        return create_eth_tx(account, to, amount)
    elif(coin == BTCTEST):
        return PrivateKeyTestnet.prepare_transaction(account.address, [(to, amount, BTC)])
    elif(coin == BTC):
        return PrivateKey.prepare_transaction(account.address, [(to, amount, BTC)])
    else:
        print(f"Unable to process {coin}")
        return ""
#---
def send_tx(coin, account, to, amount):
    """
    Send transaction
    ---
    Parameter:
    coin - coin type (defined in `constants.py`)
    account - eth_account Account object
    to - recipient wallet address
    amount - amount to send
    """
    tx = create_tx(coin, account, to, amount)
    
    if(tx==""):
        print(f"Unable to process {coin}")
        return ""
    
    signed_tx = account.sign_transaction(tx)
    
    if(coin == ETH):
        return w3.eth.sendRawTransaction(signed_tx.rawTransaction)    
    elif(coin == BTCTEST):
        return NetworkAPI.broadcast_tx_testnet(signed_tx)
    elif(coin == BTC):
        return NetworkAPI.broadcast_tx(signed_tx)
    else:
        print(f"Unable to process {coin}")
        return ""
        
# MAIN
# Derive Private Keys
eth_priv_key = get_wallet_privkey(ETH)
btctest_priv_key = get_wallet_privkey(BTCTEST)

# Convert private keys to account
eth_acct = priv_key_to_account(ETH, eth_priv_key)
btctest_acct = priv_key_to_account(BTCTEST, btctest_priv_key)

# ETH Send
#eth_txid = send_tx(ETH, eth_acct, "0x837F5a0BC310226531458559468Cf60e8C9099fE", 1)
# BTC-Test Send
btctest_txid = send_tx(BTCTEST, btctest_acct, "n1iadJMBs4kyQUv39uRWdA7Njw4ERnDdK9", 0.001)

print(btctest_txid)