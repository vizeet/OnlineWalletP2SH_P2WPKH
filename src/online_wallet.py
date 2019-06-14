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
from functools import reduce

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
                self.rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:%d" %(self.rpc_user, self.rpc_password, self.rpc_port), timeout=600)
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

                unused_addresses = copy(self.unused_list)

                for i in range(out_count):
                        address_value = {}
                        address = input('Enter Target Address: ')
                        value = float(input('Enter Bitcoins: '))
                        address_value[address] = value

                        if address in unused_addresses:
                                unused_addresses.remove(address)

                        tx_out.append(address_value)

                change_address = unused_addresses[0]
                print('change address: %s' % change_address)
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

        def setNewAddresses(self, addresses: list, label: str):
                label_list = self.rpc_connection.listlabels()
                existing_addresses = []

                if label in label_list:
                        existing_addresses = self.rpc_connection.getaddressesbylabel(label)
                new_addresses = set(addresses) - set(existing_addresses)
                print('new_addresses = %s' % new_addresses)

                return new_addresses

        def registerAddresses(self, addresses: list, label: str):
                new_addresses = self.setNewAddresses(addresses, label)

                s = []
                for address in new_addresses:
                        i = {'scriptPubKey': {'address': address}, 'timestamp': 0, 'label': label, 'watchonly': True}
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
        def createRawTxn(self, fee_rate, user):
                print('transfer_info_filepath = %s' % self.transfer_info_filepath)
                sys.stdout.flush()

                self.registerAddresses(self.jsonobj['Addresses'], user)

                raw_txn = create_raw_txn.RawTxn(self.rpc_user, self.rpc_password, self.rpc_port, self.transfer_info_filepath, user)
                txout, change_address = self.getTargetAddresses()
                self.jsonobj = raw_txn.getRawTxnFromOuts(txout, change_address, fee_rate, self.jsonobj)

        def createRawTxnToDivideFunds(self, fee_rate, user):
                print('transfer_info_filepath = %s' % self.transfer_info_filepath)
                sys.stdout.flush()

                self.registerAddresses(self.jsonobj['Addresses'], user)

                raw_txn = create_raw_txn.RawTxn(self.rpc_user, self.rpc_password, self.rpc_port, self.transfer_info_filepath, user)
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
        print('7. Rescan Blockchain to include missed transactions')
        print('8. Total Bitcoins in wallet')
        print('9. Check Network Fee in Signed Transaction')
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
                user = input('Username: ').lower()

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

                wallet.createRawTxn(fee_rate, user)

                with open(wallet.transfer_info_filepath, 'wt') as transfer_file_f:
                        json.dump(wallet.jsonobj, transfer_file_f)
        elif choice == 4:
                user = input('Username: ').lower()

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

                wallet.createRawTxnToDivideFunds(fee_rate, user)

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
        elif choice == 7:
                user = input('Username: ').lower()
                rescan_block_index = int(input('Rescan Block Index (1): ') or '1')
                print('rescan_block_index = %d' % rescan_block_index)

                with open(wallet.transfer_info_filepath, 'rt') as transfer_file_f:
                        wallet.jsonobj = json.load(transfer_file_f)

                wallet.registerAddresses(wallet.jsonobj['Addresses'], user)

                wallet.rpc_connection.rescanblockchain(rescan_block_index)
        elif choice == 8:
                user = input('Username: ').lower()

                unspent_list = wallet.rpc_connection.listunspent()
                amount = reduce(lambda x, y: round(x, 8) + round(y, 8), [unspent['amount'] for unspent in unspent_list if unspent['label'] == user])
                print('Total amount in wallet = %.8f' % round(amount, 8))
        elif choice == 9:
                unspent_list = wallet.rpc_connection.listunspent()
                #print('unspent list = %s' % unspent_list)
                with open(wallet.transfer_info_filepath, 'rt') as transfer_file_f:
                        wallet.jsonobj = json.load(transfer_file_f)

                js = wallet.rpc_connection.decoderawtransaction(wallet.jsonobj['Signed Txn'])
                #print('decoded raw txn = %s' % js)
                print('Inputs:')
                input_value = 0.0
                input_txn_list = js['vin']
                for input_txn in input_txn_list:
                        for unspent in unspent_list:
                                if unspent['txid'] == input_txn['txid'] and unspent['vout'] == input_txn['vout']:
                                        print('txid = %s, vout = %d, amount = %.8f' % (unspent['txid'], unspent['vout'], float(unspent['amount'])))
                                        input_value = round(input_value + float(unspent['amount']), 8)
                print('Total Input Value = %.8f' % round(input_value, 8))

                out_value = 0.0
                print('Output:')
                for out in js['vout']:
                        print('addresses = %s, vout = %d, amount = %.8f' % (out['scriptPubKey']['addresses'], out['n'], float(out['value'])))
                        out_value = round(out_value + float(out['value']), 8)

                print('vbytes = %.8f' % wallet.jsonobj['VBytes'])
                network_fee_calculated = round(js['vsize'] * wallet.jsonobj['Fee Rate'] / 1000, 8)
                print('Calculated Network Fee = %.8f' % round(network_fee_calculated, 8))
                network_fee_actual = round(input_value - out_value, 8)
                print('Actual Network Fee = %.8f' % round(network_fee_actual, 8))

                diff_network_fee = abs(network_fee_actual - network_fee_calculated)
                print('Difference between Actual and Calculated Network Fee = %.8f' % round(diff_network_fee, 8))
        else:
                print('Invalid selection')
