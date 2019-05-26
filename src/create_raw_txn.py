#from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json
from utility_adapters import hash_utils
import tkinter
from functools import reduce
from copy import deepcopy
#from utility_adapters import leveldb_utils
import optparse
import config
import binascii

#def updateUnusedAddresses(network: str):
#        jsonobj = json.load(open('transfer_info.json', 'rt'))
#        unused_addresses = jsonobj['Unused Addresses']
#        # TODO to be implemented
#        unused_addresses = check_addresses_unused(unused_addresses)
#
#        if len(unused_addresses) == 0:
#                addresses = jsonobj['Addresses']
#                unused_addresses = check_addresses_unused(addresses)
#
#        jsonobj['Unused Addresses'] = unused_addresses
#        json.dump(jsonobj, open('transfer_info.json', 'wt'))
#
#inuse_address_value_map_g = {}
#
#def getUnspentValueForAddress(inuse_address_map: dict, address: str):
#        value = 0
#        for txn in inuse_address_map[address]:
#                for index in range(inuse_address_map[address][txn]):
#                        value += inuse_address_map[address][txn][index]['value']
#
#        return value
#
#def populateInuseAddressValueMap(network: str):
#        global inuse_address_value_map_g
#        with open('transfer_info.json', 'rt') as transfer_info_f:
#                jsonobj = json.load(transfer_info_f)
#        inuse_address_map = jsonobj['In-use Addresses']
#
#        for address in inuse_address_map:
#                inuse_address_value_map_g[address] = getUnspentValueForAddress(inuse_address_map, address)

def calculateVBytes(raw_txn: bytes):
        segwit_flag_bytes = 0x02
        script_size_bytes = 0x01 + len(b'\x00\x14') + 0x14

        input_count = getCount(raw_txn)
        witness_count_bytes = 0x01
        sig_size_bytes = 0x01
        max_sig_bytes = 0x49
        pubkey_size_bytes = 0x01
        pubkey_bytes = 0x21

        witness_bytes = segwit_flag_bytes + (input_count * (witness_count_bytes + sig_size_bytes + max_sig_bytes + pubkey_size_bytes + pubkey_bytes))

        non_witness_bytes = (input_count * script_size_bytes) + len(raw_txn)

        weight_units = witness_bytes + (non_witness_bytes * 4)

        vbytes = weight_units / 4

        return vbytes

def getCount(raw_txn: bytes):
        print('raw_txn = %s' % bytes.decode(binascii.hexlify(raw_txn)))
        txn_size = int(raw_txn[4])
        print('txn_size = %d' % txn_size)

        if txn_size < 0xfd:
                return txn_size
        elif txn_size == 0xfd:
                txn_size = int(binascii.hexlify(raw_txn[5:7][::-1]), 16)
                return txn_size
        elif txn_size == 0xfe:
                txn_size = int(binascii.hexlify(raw_txn[5:9][::-1]), 16)
                return txn_size
        else:
                txn_size = int(binascii.hexlify(count_bytes[5:13][::-1]), 16)
                return txn_size

def btc2bytes(btc: float):
        satoshis = int(btc * (10**8))
        print('satoshis = %s' % satoshis)
        hex_b = binascii.unhexlify('%016x' % satoshis)[::-1]
        return hex_b

def getInputValue(inputs: list):
        input_value = reduce((lambda x, y: x + y), [inp['value'] for inp in inputs])
        return input_value

def getTargetValue(tx_out: dict):
        target_value = reduce((lambda x, y: x + y), [v for k, v in tx_out.items()])
        return target_value

def getTargetAddresses():
        out_count = int(input('Enter Number of Target Addresses: '))

        tx_out = []

        for i in out_count:
                address_value = {}
                address = input('Enter Target Address: ')
                value = float(input('Enter Bitcoins: '))
                address_value[address] = value

                tx_out.append(address_value)

        return tx_out


class RawTxn:
        def __init__(self, rpc_connection, transfer_info_filepath: str):
                global network_port_map_g
                self.rpc_connection = rpc_connection
                self.transfer_info_filepath = transfer_info_filepath

        def getUnusedAddresses(self, network: str):
                with open(self.transfer_info_filepath, 'rt') as transfer_info_f:
                        jsonobj = json.load(transfer_info_f)
                        
                return jsonobj['Unused Addresses']

        def getChangeAddressFromInUse(self, change_value: float):
                global inuse_address_value_map_g

                with open(self.transfer_info_filepath, 'rt') as transfer_info_f:
                        jsonobj = json.load(transfer_info_f)
                threshold = jsonobj['Address Value Threshold']

                sorted_addresses = sorted(d, key=lambda k: d[k])

                ret_address = inuse_address_value_map_g[sorted_addresses[0]] + change_value

                if (ret_address) > threshold:
                        return None

                return ret_address

        def getInputsForAddress(address: str, network: str):
                with open(self.transfer_info_filepath, 'rt') as transfer_info_f:
                        jsonobj = json.load(transfer_info_f)
                inuse_address_map = jsonobj['In-use Addresses']

                inputs = []
                for txn in inuse_address_map[address]:
                        for index in range(inuse_address_map[address][txn]):
                                value = inuse_address_map[address][txn][index]['value']
                                out_index = inuse_address_map[address][txn][index]['out_index']
                                inputs.append({'txid': txn, 'vout': out_index, 'address': address, 'value': value})

                return inputs

        def getInputs(self, amount: float):
                global inuse_address_value_map_g

                if len(inuse_address_value_map_g) == 0:
                        print('Inuse addresses are 0')
                        populateInuseAddressValueMap()

                inputs = []
                value = 0
                for address, address_value in inuse_address_value_map_g.items():
                        address_inputs = getInputsForAddress(address)
                        value += address_value
                        inputs.extend(address_inputs)

                        if value >= amount:
                                break

                print('inputs = %s' % inputs)
                return inputs

        def setEstimatedFeeRate(self):
                with open(self.transfer_info_filepath, 'rt') as transfer_file_f:
                        jsonobj = json.load(transfer_file_f)
                conf_target = json.load(jsonobj)['Confirmation Target Block']
                self.estimated_fee_rate = self.rpc_connection.estimatesmartfee(conf_target)
                print('estimated_fee_rate = %s' % self.estimated_fee_rate)

        def estimatefee(self, raw_txn: bytes):

                vbytes = calculateVBytes(raw_txn)

                if self.estimated_fee_rate == 0.0:
                        self.setEstimatedFeeRate()

                estimated_fee = self.estimated_fee_rate * (vbytes / 1000)

                return estimated_fee

        def setRawTransaction(self, inputs: list, outs: dict, fee_rate=0.0):
                self.estimated_fee_rate = fee_rate

                tx_ins = [{'txid': inp['txid'], 'vout': inp['vout']} for inp in inputs]

                # first get raw transaction without change
                raw_txn = binascii.unhexlify(self.rpc_connection.createrawtransaction(tx_ins, outs))

                estimated_fee = self.estimatefee(raw_txn)
                target_value = getTargetValue(outs)
                target_addresses = list(outs)

                input_value = getInputValue(inputs)

                change_value = input_value - target_value - estimated_fee

                # if change_value is not 0 then estimated_fee and change_value are wrong
                if change_value == 0:
                        return raw_txn, estimated_fee

                unused_addresses = self, getUnusedAddresses()
                change_address = self.getChangeAddressFromInUse(change_value)
                if change_address == None:
                        change_address = list(set(unused_addresses) - set(target_addresses))[0]

                outs[change_address] = change_value
                raw_txn = self.rpc_connection.createrawtransaction(tx_ins, outs)
                estimated_fee = self.estimatefee(raw_txn)
                change_value = input_value - target_value - estimated_fee
                while change_value < 0:
                        inputs = self.getInputs(target_value + estimated_fee)
                        tx_ins = [{'txid': inp['txid'], 'vout': inp['vout']} for inp in inputs]
                        raw_txn = self.rpc_connection.createrawtransaction(tx_ins, outs)
                        estimated_fee = self.estimatefee(raw_txn)
                        input_value = getInputValue(inputs)

                        change_value = input_value - target_value - estimated_fee
                        change_address_temp = self.getChangeAddressFromInUse(change_value)
                        if change_address_temp != None:
                                change_address = change_address_temp

                outs[change_address] = change_value
                raw_txn = rpc_connection.createrawtransaction(tx_ins, outs)

                with open(transfer_info_filepath, 'wt') as transfer_info_f:
                        jsonobj['Raw txn'] = raw_txn
                        jsonobj['Inputs'] = inputs

                        json.dump(jsonobj, transfer_info_f)

        def setRawTxnFromOuts(self, txout: dict, fee_rate=0.0):
                target_value = getTargetValue(txout)
                inputs = self.getInputs(target_value)
                self.setRawTransaction(inputs, txout, fee_rate=fee_rate)

if __name__ == '__main__':
        parser = optparse.OptionParser(usage="python3 create_raw_transaction.py -u <RPC Username> -p <RPC Password>")
        parser.add_option('-u', '--username', action='store', dest='user', help='Username to make RPC connection with bitcoind.')
        parser.add_option('-p', '--password', action='store', dest='password', help='Password to make RPC connection with bitcoind.')
        parser.add_option('-t', '--test', action='store_true', dest='test', help='Execute in test mode')
        (options, _) = parser.parse_args()

        rpc_user = options.user
        rpc_password = options.password

        if options.test:
                network_g = 'regtest'
        else:
                network_g = 'mainnet'

#        rpc_connection_g = AuthServiceProxy("http://%s:%s@127.0.0.1:18443"%(rpc_user, rpc_password))

        txn_obj = RawTxn(network_g, rpc_user, rpc_password)

        tx_out = getTargetAddresses()

        target_value = getTargetValue(tx_out)

        with open('../config/hd_wallet.conf') as hd_wallet:
                jsonobj = json.load(hd_wallet)
        nettype = jsonobj['network']
        ldb_adapter = leveldb_utils.LevelDBAdapter(nettype)

        
        jsonobj = json.load(open('transfer_info.json', 'rt'))
        config.updateAddressConfig(jsonobj, ldb_adapter)
        inputs = raw_txn.getInputs(target_value)

        txn_obj.setRawTransaction(inputs, tx_out)
