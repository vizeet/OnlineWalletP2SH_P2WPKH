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
2. Start bitcoin daemon
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


3. Validate generated addresses
```bash
cd src
python2 online_wallet.py [-t]
```
-t is for test mode.
Select option 1.

4. To use next address for receiving bitcoins
```bash
cd src
python2 online_wallet.py [-t]
```
-t is for test mode.
Select option 2.


5. Generate Raw Transaction:
```bash
python2 online_wallet.py [-t]
```
-t is for test mode.
Select option 3.

7.  Decode Signed Transaction to check inputs and outputs of transactions are as expected:
```bash
python2 online_wallet.py [-t]
```
-t is for test mode.
Select option 4.

8.  Publish Signed Transaction to push it into network:
```bash
python2 online_wallet.py [-t]
```
-t is for test mode.
Select option 5.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
