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
from functools import reduce
from copy import deepcopy
import optparse
import binascii
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

inuse_address_value_map_g = {}

def getUnspentValueForAddress(inuse_address_map: dict, address: str):
        print('********** inuse_address_map = %s' % json.dumps(inuse_address_map))
        value = 0
        for txn in inuse_address_map[address]:
                print('************** txn = %s' % txn)
                for vout_value_map in inuse_address_map[address][txn]:
                        value += vout_value_map['amount']

        return value

def setInuseAddressValueMap(inuse_address_map: dict):
        global inuse_address_value_map_g

        for address in inuse_address_map:
                inuse_address_value_map_g[address] = getUnspentValueForAddress(inuse_address_map, address)

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
        print('inputs = %s' % inputs)
        input_value = reduce((lambda x, y: x + y), [inp['value'] for inp in inputs])
        return input_value

def getTargetValue(tx_out: list):
        print('tx_out = %s' % tx_out)
        target_value = 0
        target_value = reduce(lambda x, y: x + y, [list(out.items())[0][1] for out in tx_out])
        return target_value

class RawTxn:
        def __init__(self, rpc_user, rpc_password, rpc_port, transfer_info_filepath: str):
                global network_port_map_g
                #self.rpc_connection = rpc_connection
                self.transfer_info_filepath = transfer_info_filepath
                print('rpc_user = %s' % rpc_user)
                print('rpc_password = %s' % rpc_password)
                print('rpc_port = %d' % rpc_port)
                self.rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:%d" % (rpc_user, rpc_password, rpc_port))
                self.inuseAddressMap = None

        def getInputsForAddress(self, address: str):
                inputs = []

                print('address = %s' % address)

                if self.inuseAddressMap == None:
                        unspent_list = self.rpc_connection.listunspent()
                        self.setInuseAddressMap(unspent_list)

                print('inuse_address_map[%s] = %s' % (address, self.inuse_address_map[address]))

                for txn in self.inuse_address_map[address]:
                        print('txn = %s' % txn)
                        for vout_amount_map in self.inuse_address_map[address][txn]:
                                value = vout_amount_map['amount']
                                out_index = vout_amount_map['vout']
                                inputs.append({'txid': txn, 'vout': out_index, 'address': address, 'value': value})

                return inputs

        def setInuseAddressMap(self, unspent_list: list):
                self.inuse_address_map = {}
                for unspent in unspent_list:
                        address = unspent['address']
                        if address not in self.inuse_address_map:
                                self.inuse_address_map[address] = {}
                        txid = unspent['txid']
                        if txid not in self.inuse_address_map[address]:
                                self.inuse_address_map[address][txid] = []
                        vout = unspent['vout']
                        amount = unspent['amount']
                        self.inuse_address_map[address][txid].append({'vout': vout, 'amount': float(amount)})

        def getInputs(self, amount: float):
                global inuse_address_value_map_g

                print('********** target value = %f' % amount)

                if len(inuse_address_value_map_g) == 0:
                        unspent_list = self.rpc_connection.listunspent()
                        self.setInuseAddressMap(unspent_list)

                        print('Inuse addresses are 0')
                        setInuseAddressValueMap(self.inuse_address_map)

                print('************* inuse_address_value_map = %s' % inuse_address_value_map_g)

                inputs = []
                value = 0
                for address, address_value in inuse_address_value_map_g.items():
                        address_inputs = self.getInputsForAddress(address)
                        value += address_value
                        inputs.extend(address_inputs)

                        if value >= amount:
                                break

                if value < amount:
                        print('Error: Insufficient Balance')
                        return None

                print('inputs = %s' % inputs)
                return inputs

        def getInputsForAddressList(self, address_list: list):
                inputs = []
                for address in address_list:
                        address_inputs = self.getInputsForAddress(address)
                        inputs.extend(address_inputs)

                print('inputs = %s' % inputs)
                return inputs

        def getAmountFromInputs(self, inputs: list):
                reduce(lambda x, y: x + y, [inp[amount] for inp in inputs])

        def estimatefee(self, raw_txn: bytes, fee_rate: float):

                vbytes = calculateVBytes(raw_txn)

                print('vbytes = %f' % vbytes)

                estimated_fee = round(fee_rate * (vbytes / 1000), 8)

                print('vbytes = %f' % vbytes)
                print('estimated_fee = %f' % estimated_fee)

                return estimated_fee

        def getRawTransaction(self, inputs: list, outs: list, change_address: str, fee_rate: float, jsonobj: dict):
                print('fee_rate = %f' % fee_rate)

                tx_ins = [{'txid': inp['txid'], 'vout': inp['vout']} for inp in inputs]

                # first get raw transaction without change
                print('111111111: tx_ins = %s, outs = %s' % (tx_ins, outs))
                raw_txn = self.rpc_connection.createrawtransaction(tx_ins, outs)

                estimated_fee = self.estimatefee(binascii.unhexlify(raw_txn), fee_rate)
                target_value = getTargetValue(outs)
                #target_addresses = list(outs)

                input_value = getInputValue(inputs)

                change_value = round(input_value - target_value - estimated_fee, 8)

                # if change_value is not 0 then estimated_fee and change_value are wrong
                if change_value == 0:
                        jsonobj['Raw Txn'] = raw_txn
                        jsonobj['Inputs'] = inputs

                        return jsonobj

                new_outs = deepcopy(outs)
                new_outs.append({change_address: round(change_value, 8)})
                print('2222222222: tx_ins = %s, new_outs = %s' % (tx_ins, new_outs))
                print('estimated_fee = %f' % estimated_fee)
                raw_txn = self.rpc_connection.createrawtransaction(tx_ins, new_outs)
                estimated_fee = self.estimatefee(binascii.unhexlify(raw_txn), fee_rate)
                change_value = round(input_value - target_value - estimated_fee, 8)
                while change_value < 0:
                        inputs = self.getInputs(round(target_value + estimated_fee, 8))
                        tx_ins = [{'txid': inp['txid'], 'vout': inp['vout']} for inp in inputs]
                        print('33333333333: tx_ins = %s, outs = %s' % (tx_ins, outs))
                        print('estimated_fee = %f' % estimated_fee)
                        raw_txn = self.rpc_connection.createrawtransaction(tx_ins, new_outs)
                        estimated_fee = self.estimatefee(binascii.unhexlify(raw_txn), fee_rate)
                        input_value = getInputValue(inputs)

                        change_value = round(input_value - target_value - estimated_fee, 8)
                new_outs = deepcopy(outs)
                new_outs.append({change_address: round(change_value, 8)})
                print('44444444444444: tx_ins = %s, new_outs = %s' % (tx_ins, new_outs))
                print('estimated_fee = %f' % estimated_fee)
                raw_txn = self.rpc_connection.createrawtransaction(tx_ins, new_outs)
                print('raw txn = %s' % raw_txn)

                jsonobj['Raw Txn'] = raw_txn
                jsonobj['Inputs'] = inputs

                return jsonobj

        def getRawTxnFromOuts(self, txout: list, change_address: str, fee_rate: float, jsonobj: dict):
                target_value = getTargetValue(txout)
                inputs = self.getInputs(target_value)
                return self.getRawTransaction(inputs, txout, change_address, fee_rate, jsonobj)

        def getRawTxnToDivideFunds(self, input_addresses: list, out_addresses: list, fee_rate: float, jsonobj: dict):
                print('fee_rate = %f' % fee_rate)

                inputs = self.getInputsForAddressList(input_addresses)
                input_value = getInputValue(inputs)

                each_out_value = round(input_value / len(out_addresses), 8)

                outs = dict([(address, each_out_value) for address in out_addresses])

                tx_ins = [{'txid': inp['txid'], 'vout': inp['vout']} for inp in inputs]

                # first get raw transaction without change
                print('111111111: tx_ins = %s, outs = %s' % (tx_ins, outs))
                raw_txn = self.rpc_connection.createrawtransaction(tx_ins, outs)

                estimated_fee = self.estimatefee(binascii.unhexlify(raw_txn), fee_rate)
                each_out_value = round((input_value - estimated_fee) / len(out_addresses), 8)
                outs = dict([(address, each_out_value) for address in out_addresses])

                # second get raw transaction without change
                print('22222222: tx_ins = %s, outs = %s' % (tx_ins, outs))
                raw_txn = self.rpc_connection.createrawtransaction(tx_ins, outs)
                print('raw txn = %s' % raw_txn)

                jsonobj['Raw Txn'] = raw_txn
                jsonobj['Inputs'] = inputs

                return jsonobj

