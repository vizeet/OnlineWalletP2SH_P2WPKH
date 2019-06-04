############
#MIT License
#
#Copyright (c) 2019 vizeet srivastava
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
############

import json
import create_raw_txn
from optparse import OptionParser
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import sys
import requests
from copy import copy
from pprint import pprint

network_port_map_g = {
        'regtest': 18443,
        'mainnet': 8332
}

transfer_info_map_g = {
        'regtest': 'transfer_info_test.json',
        'mainnet': 'transfer_info.json'
}

class Wallet:
        def __init__(self, network: str, datadir: str):
                global network_port_map_g, transfer_info_map_g

                self.rpc_user = input('RPC Username: ')
                self.rpc_password = input('RPC Password: ')
                self.rpc_port = network_port_map_g[network]
                self.rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:%d" %(self.rpc_user, self.rpc_password, self.rpc_port))
                self.network = network
                self.transfer_info_filepath = datadir + '/' + transfer_info_map_g[network]

        def isAddressUnused(self, address: str):
                res = requests.get('https://blockchain.info/rawaddr/' + address)
                jsonobj = json.loads(res.text)
                return (jsonobj['total_received'] == 0)

        def setUnusedAddresses(self):
                self.unused_list = [address for address in self.jsonobj['Addresses'] if self.isAddressUnused(address) == True]

        def setUnusedAddressesTest(self):
                unspent_list = self.rpc_connection.listunspent()
                if len(unspent_list) > 0:
                        inuse_addresses = [unspent['address'] for unspent in unspent_list]
                        index = 0
                        for inuse_address in inuse_addresses:
                                if inuse_address in self.jsonobj['Addresses']:
                                        new_index = self.jsonobj['Addresses'].index(inuse_address)
                                        index = new_index if new_index > index else index
                        self.unused_list = copy(self.jsonobj['Addresses'][index + 1:])
                else:
                        self.unused_list = copy(self.jsonobj['Addresses'])

                print('unused list = %s' % self.unused_list)

        def getNextAddresses(self):
                if network == 'regtest':
                        self.setUnusedAddressesTest()
                else:
                        self.setUnusedAddresses()

                count = int(input('Enter Number of Unused Addresses: '))
                addresses = self.unused_list[0: count]

                return addresses

        def getTargetAddresses(self):
                if network == 'regtest':
                        self.setUnusedAddressesTest()
                else:
                        self.setUnusedAddresses()

                out_count = int(input('Enter Number of Target Addresses: '))

                tx_out = []

                unused_index = 0

                for i in range(out_count):
                        address_value = {}
                        address = self.unused_list[unused_index]
                        use_address = ((input('Use Address %s: Y/n? ' % address) or 'Y').lower() == 'y')
                        if use_address ==False:
                                address = input('Enter Target Address: ')
                        else:
                                unused_index += 1
                        value = float(input('Enter Bitcoins: '))
                        address_value[address] = value

                        tx_out.append(address_value)

                change_address = self.unused_list[unused_index]
                return tx_out, change_address

        def getSourceTargetAddresses(self):
                if network == 'regtest':
                        self.setUnusedAddressesTest()
                else:
                        self.setUnusedAddresses()

                out_count = int(input('Enter Number of Input Addresses: '))

                input_addresses = []

                for i in range(out_count):
                        address = input('Enter Input Address: ')

                        input_addresses.append(address)

                out_count = int(input('Enter Number of Target Addresses: '))

                out_addresses = []

                for i in range(out_count):
                        #address = input('Enter Target Address: ')
                        address = self.unused_list[i]
                        #use_address = ((input('Use Address %s: Y/n? ' % address) or 'Y').lower() == 'y')

                        out_addresses.append(address)

                print('out_addresses = %s' % out_addresses)

                return input_addresses, out_addresses

        def validateAddresses(self):
                address_valid_map = {}
                for address in self.jsonobj['Addresses']:
                       address_valid_map[address] = self.rpc_connection.validateaddress(address)['isvalid']
                return address_valid_map

        def setNewAddresses(self, addresses: list):
                label_list = self.rpc_connection.listlabels()
                existing_addresses = []

                if 'wallet' in label_list:
                        existing_addresses = self.rpc_connection.getaddressesbylabel('wallet')
                new_addresses = set(addresses) - set(existing_addresses)
                print('new_addresses = %s' % new_addresses)

                return new_addresses

        def registerAddresses(self, addresses: list):
                new_addresses = self.setNewAddresses(addresses)

                s = []
                for address in new_addresses:
                        i = {'scriptPubKey': {'address': address}, 'timestamp': 0, 'label': 'wallet', 'watchonly': True}
                        s.append(i)

                if len(s) > 0:
                        self.rpc_connection.importmulti(s)

                return new_addresses

#        def getInputs(self, amount: float):
#                if len(self.inuse_address_value_map) == 0:
#                        print('Inuse addresses are 0')
#                        self.setInuseAddressValueMap()
#
#                inputs = []
#                value = 0
#                for address, address_value in self.inuse_address_value_map.items():
#                        address_inputs = getInputsForAddress(address)
#                        value += address_value
#                        inputs.extend(address_inputs)
#
#                        if value >= amount:
#                                break
#
#                if value < amount:
#                        print('Insufficient Balance')
#                        return inputs
#                print('inputs = %s' % inputs)
#                return inputs
#
        def createRawTxn(self, fee_rate):
                print('transfer_info_filepath = %s' % self.transfer_info_filepath)
                sys.stdout.flush()

                self.registerAddresses(self.jsonobj['Addresses'])

                raw_txn = create_raw_txn.RawTxn(self.rpc_user, self.rpc_password, self.rpc_port, self.transfer_info_filepath)
                txout, change_address = self.getTargetAddresses()
                self.jsonobj = raw_txn.getRawTxnFromOuts(txout, change_address, fee_rate, self.jsonobj)

        def createRawTxnToDivideFunds(self, fee_rate):
                print('transfer_info_filepath = %s' % self.transfer_info_filepath)
                sys.stdout.flush()

                self.registerAddresses(self.jsonobj['Addresses'])

                raw_txn = create_raw_txn.RawTxn(self.rpc_user, self.rpc_password, self.rpc_port, self.transfer_info_filepath)
                input_addresses, out_addresses = self.getSourceTargetAddresses()
                self.jsonobj = raw_txn.getRawTxnToDivideFunds(input_addresses, out_addresses, fee_rate, self.jsonobj)

        def publishSignedTxn(self):
                return self.rpc_connection.sendrawtransaction(self.jsonobj['Signed Txn'])

        def getFeeRate(self, conf_target_block: float):
                return self.rpc_connection.estimatesmartfee(conf_target_block)['feerate']

        def decodeSignedTransaction(self):
                return self.rpc_connection.decoderawtransaction(self.jsonobj['Signed Txn'])

if __name__ == '__main__':
        parser = OptionParser()
        parser.add_option("-t", "--test",
                  action="store_true", dest="test",
                  help="Execute in Test Mode")
        (options, _) = parser.parse_args()

        if options.test:
                network = 'regtest'
                datadir = '/home/online/wallet'
        else:
                with open('../config/hd_wallet.conf', 'rt') as conf_f:
                        jsonobj = json.load(conf_f)
                network = jsonobj['network']
                datadir = jsonobj['datadir']

        print('1. Validate Addresses')
        print('2. Get Next Addresses')
        print('3. Create Raw Transaction')
        print('4. Create Raw Transaction to Divide Funds')
        print('5. Decode Signed Transaction')
        print('6. Publish Signed Transaction')
        choice = int(input('Selection: '))

        wallet = Wallet(network, datadir)

        if choice == 1:
                with open(wallet.transfer_info_filepath, 'rt') as transfer_file_f:
                        wallet.jsonobj = json.load(transfer_file_f)

                address_valid_map = wallet.validateAddresses()
                print(address_valid_map)
        elif choice == 2:
                with open(wallet.transfer_info_filepath, 'rt') as transfer_file_f:
                        wallet.jsonobj = json.load(transfer_file_f)
                addresses = wallet.getNextAddresses()
                print('Use Addresses: %s' % addresses)
        elif choice == 3:
                if network == 'regtest':
                        fee_rate = 0.00005
                else:
                        conf_target_block = int(input('Confirmation Target Block for fee estimation: '))
                        fee_rate = float(wallet.getFeeRate(conf_target_block))
                        print('fee_rate = %f' % fee_rate)

                with open(wallet.transfer_info_filepath, 'rt') as transfer_file_f:
                        wallet.jsonobj = json.load(transfer_file_f)

                fee_rate = float(input('change fee_rate (%f btc/kb): ' % fee_rate) or '%f' % fee_rate)
                fee_rate = round(fee_rate, 8)
                print('fee_rate = %.8f' % fee_rate)
                wallet.jsonobj['Fee Rate'] = round(fee_rate, 8)

                wallet.createRawTxn(fee_rate)

                with open(wallet.transfer_info_filepath, 'wt') as transfer_file_f:
                        json.dump(wallet.jsonobj, transfer_file_f)
        elif choice == 4:
                if network == 'regtest':
                        fee_rate = 0.00005
                else:
                        conf_target_block = int(input('Confirmation Target Block for fee estimation: '))
                        fee_rate = float(wallet.getFeeRate(conf_target_block))
                        print('fee_rate = %f' % fee_rate)

                with open(wallet.transfer_info_filepath, 'rt') as transfer_file_f:
                        wallet.jsonobj = json.load(transfer_file_f)

                fee_rate = float(input('change fee_rate (%f btc/kb): ' % fee_rate) or '%f' % fee_rate)
                fee_rate = round(fee_rate, 8)
                print('fee_rate = %.8f' % fee_rate)
                wallet.jsonobj['Fee Rate'] = round(fee_rate, 8)

                wallet.createRawTxnToDivideFunds(fee_rate)

                with open(wallet.transfer_info_filepath, 'wt') as transfer_file_f:
                        json.dump(wallet.jsonobj, transfer_file_f)
        elif choice == 5:
                with open(wallet.transfer_info_filepath, 'rt') as transfer_file_f:
                        wallet.jsonobj = json.load(transfer_file_f)

                decoded_txn = wallet.decodeSignedTransaction()
                pprint(decoded_txn)

        elif choice == 6:
                with open(wallet.transfer_info_filepath, 'rt') as transfer_file_f:
                        wallet.jsonobj = json.load(transfer_file_f)

                status = wallet.publishSignedTxn()
                print(status)
        else:
                print('Invalid selection')
