# OnlineWalletP2SH_P2WPKH

OnlineWalletP2SH_P2WPKH is an online bitcoin wallet implementation. It works with its Offline counter part project BitcoinHDWallet.

Installation instruction currently covers only Linux environment.

>> Disclaimer: Code is well tested and tested with my own funds. But no testing is complete without third party user. Use the wallet at your own risk and keep smaller funds in each address. 

## Features
1. Easy setup: Does not require extra computer or special device.
2. Secure: As transaction signing happens offline. At no point private-key is printed or provided. Secret is not stored. 
3. Open source and mostly uses bitcoin-core wallet.
4. Smart Fee estimation: Uses bitcoin-cli command "estimatefeeestimate" to calculate fee for transaction.
5. Privacy: Does not use SPVs. And Uses all transactions associated with one address when creating a new transaction. This prevents exposure of public keys which may help in tracking transaction or can be attacked by quantum computers in future.
6. Low fee: Uses Segwit wrapped in Pay-to-script hash i.e. P2SH-P2WPKH address. Which saves on network fee.

## Requirements
1. python 3.6
2. python pip package manager
3. bitcoin-core 0.17 is installed

## Installation
Steps:
1. Clone code
```bash
git clone https://github.com/vizeet/OnlineWalletP2SH_P2WPKH.git
```

## Usage
1. Begin with Project "BitcoinHDWallet"
2. Start bitcoin daemon and provide rpcuser rpcpassword as you wish
```bash
bitcoind -dbcache=4096 -txindex=1 -rpcuser=test -rpcpassword=test -timeout=30
```

3. Configure wallet
```bash
cd config
cp hd_wallet.conf.template hd_wallet.conf
vim hd_wallet.conf
```
Now update json config file
```json
{
"salt": <provide and remember salt>,
"network": "mainnet",
"datadir": <data dir path>
}
```


3. List of options
Online wallet provides list of options. 
For each selection you will require to enter RPC user and RPC password which is used by bitcoind. 
Also you will need to provide username to associate addresses with a tag. 
-t is for test mode.

```bash
cd src
python3 online_wallet.py -t
1. Validate Addresses
2. Get Next Addresses
3. Create Raw Transaction
4. Create Raw Transaction to Divide Funds
5. Decode Signed Transaction
6. Publish Signed Transaction
7. Rescan Blockchain to include missed transactions
8. Total Bitcoins in wallet
9. Check Network Fee in Signed Transaction
10. Generate QR Code for Address
Selection: 1
RPC Username: test
RPC Password: test
Username: test
```
i. Validate generated addresses
Option 1. This will print json with each address as true or false.

ii. To use next address for receiving bitcoins
Option 2. Enter number of addresses and this will return unused addresses which can be used to receive bitcoins.

iii. Generate Raw Transaction:
Option 3. Provide out addresses along with amount. This generates a pre-signed transaction.

iv. Create Raw Transaction to Divide Funds
Option 4. This helps in dividing funds at an address to multiple addresses.

v. Decode Signed Transaction to check inputs and outputs of transactions are as expected:
Option 5. This prints signed transaction in json format.

vi.  Publish Signed Transaction to push it into network
Option 6. This publishes/broadcasts signed transaction to network and returns transaction-id. This can be checked for confirmation.s

vii. Rescan Blockchain to include missed transactions
Option 7. If an address is not registered you need to provide block height at which the transaction which includes missed address was confirmed. 

viii. Total Bitcoins in wallet
Option 8. This provides total bitcoins associated with user

ix. Check Network Fee in Signed Transaction
Option 9. This provides information about input txids, values and out addresses and out values and also network fees paid. It also checks if there is any calculation mismatch.

x. Generate QR Code for Address
Option 10. This provides 3 ways to generate QR code which might be useful for different exchanges or apps.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
