from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json
from utility_adapters import hash_utils
import tkinter
from functools import reduce
from copy import deepcopy
from utility_adapters import leveldb_utils
import optparse
import config

def updateUnusedAddresses():
        jsonobj = json.load(open('transfer_info.json', 'rt'))
        unused_addresses = jsonobj['Unused Addresses']
        # TODO to be implemented
        unused_addresses = check_addresses_unused(unused_addresses)

        if len(unused_addresses) == 0:
                addresses = jsonobj['Addresses']
                unused_addresses = check_addresses_unused(addresses)

        jsonobj['Unused Addresses'] = unused_addresses
        json.dump(jsonobj, open('transfer_info.json', 'wt'))

def getUnusedAddresses():
        return json.load(open('transfer_info.json', 'rt'))['Unused Addresses']

inuse_address_value_map_g = {}

def getUnspentValueForAddress(inuse_address_map: dict, address: str):
        value = 0
        for txn in inuse_address_map[address]:
                for index in range(inuse_address_map[address][txn]):
                        value += inuse_address_map[address][txn][index]['value']

        return value

def populateInuseAddressValueMap():
        global inuse_address_value_map_g
        jsonobj = json.load(open('transfer_info.json', 'rt'))
        inuse_address_map = jsonobj['In-use Addresses']

        for address in inuse_address_map:
                inuse_address_value_map_g[address] = getUnspentValueForAddress(inuse_address_map, address)

def getInputsForAddress(address: str):
        jsonobj = json.load(open('transfer_info.json', 'rt'))
        inuse_address_map = jsonobj['In-use Addresses']

        inputs = []
        for txn in inuse_address_map[address]:
                for index in range(inuse_address_map[address][txn]):
                        value = inuse_address_map[address][txn][index]['value']
                        out_index = inuse_address_map[address][txn][index]['out_index']
                        inputs.append({'txid': txn, 'vout': out_index, 'address': address, 'value': value})

        return inputs

def getInputs(amount: float):
        global inuse_address_value_map_g

        if len(inuse_address_value_map_g) == 0:
                populateInuseAddressValueMap()

        inputs = []
        value = 0
        for address, address_value in inuse_address_value_map_g.items():
                address_inputs = getInputsForAddress(address)
                value += address_value
                inputs.extend(address_inputs)

                if value >= amount:
                        break

        return inputs

def calculateVBytes(raw_txn: bytes):
        segwit_flag_bytes = 0x02
        script_size_bytes = 0x01 + len(bytes([b'\x00\x14'])) + 0x14

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

def getCount(raw_txn: int):
        txn_size = raw_txn[4]

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

def estimatefee(raw_txn: bytes):
        global rpc_connection_g

        conf_target = json.load(open('transfer_info.json', 'rt'))['Confirmation Target Block']
        estimated_fee_rate = rpc_connection_g.estimatesmartfee(conf_target)

        vbytes = calculateVBytes(raw_txn)

        estimated_fee = estimated_fee_rate * (vbytes / 1000)

        return estimated_fee

def btc2bytes(btc: float):
        satoshis = int(btc * (10**8))
        print('satoshis = %s' % satoshis)
        hex_b = binascii.unhexlify('%016x' % satoshis)[::-1]
        return hex_b

def getInputValue(inputs: list):
        input_value = reduce((lambda x, y: x + y), [inp['value'] for inp in inputs])
        return input_value

def getChangeAddressFromInUse(change_value: float):
        global inuse_address_value_map_g

        threshold = json.load(open('transfer_info.json', 'rt'))['Address Value Threshold']

        sorted_addresses = sorted(d, key=lambda k: d[k])

        ret_address = inuse_address_value_map_g[sorted_addresses[0]] + change_value

        if (ret_address) > threshold:
                return None

        return ret_address

def setRawTransaction(inputs: list, outs: dict):
        global rpc_connection_g

        tx_ins = [{'txid': inp['txid'], 'vout': inp['vout']} for inp in inputs]

        # first get raw transaction without change
        raw_txn = rpc_connection_g.createrawtransaction(tx_ins, outs)

        estimated_fee = estimatefee(raw_txn)
        target_value = getTargetValue(outs)
        target_addresses = list(outs)

        input_value = getInputValue(inputs)

        change_value = input_value - target_value - estimated_fee

        # if change_value is not 0 then estimated_fee and change_value are wrong
        if change_value == 0:
                return raw_txn, estimated_fee

        unused_addresses = getUnusedAddresses()
        change_address = getChangeAddressFromInUse(change_value)
        if change_address == None:
                change_address = list(set(unused_addresses) - set(target_addresses))[0]

        outs[change_address] = change_value
        raw_txn = rpc_connection.createrawtransaction(tx_ins, outs)
        estimated_fee = estimatefee(raw_txn)
        change_value = input_value - target_value - estimated_fee
        while change_value < 0:
                inputs = getInputs(target_value + estimated_fee)
                tx_ins = [{'txid': inp['txid'], 'vout': inp['vout']} for inp in inputs]
                raw_txn = rpc_connection.createrawtransaction(tx_ins, outs)
                estimated_fee = estimatefee(raw_txn)
                input_value = getInputValue(inputs)

                change_value = input_value - target_value - estimated_fee
                change_address_temp = getChangeAddressFromInUse(change_value)
                if change_address_temp != None:
                        change_address = change_address_temp

        outs[change_address] = change_value
        raw_txn = rpc_connection.createrawtransaction(tx_ins, outs)
        jsonobj = open('transfer_info.json', 'rt')
        jsonobj['Raw txn'] = raw_txn
        json.dump(jsonobj, open('transfer_info.json', 'wt'))

def getTargetValue(tx_out: dict):
        target_value = reduce((lambda x, y: x + y), [v for k, v in items(tx_out)])
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

if __name__ == '__main__':
        parser = optparse.OptionParser(usage="python3 create_raw_transaction.py -u <RPC Username> -p <RPC Password>")
        parser.add_option('-u', '--username', action='store', dest='user', help='Username to make RPC connection with bitcoind.')
        parser.add_option('-p', '--password', action='store', dest='password', help='Password to make RPC connection with bitcoind.')
        (args, _) = parser.parse_args()
        if args.port == None:
                logging.error ("Missing required argument")
                sys.exit(1)

        rpc_user = args.user
        rpc_password = args.password

        rpc_connection_g = AuthServiceProxy("http://%s:%s@127.0.0.1:18443"%(rpc_user, rpc_password))

        tx_out = getTargetAddresses()

        target_value = getTargetValue(tx_out)

        nettype = json.load(open('hd_wallet.conf'))['network']
        ldb_adapter = leveldb_utils.LevelDBAdapter(nettype)

        jsonobj = json.load(open('transfer_info.json', 'rt'))
        config.updateAddressConfig(jsonobj, ldb_adapter)
        inputs = getInputs(target_value)

        setRawTransaction(inputs, tx_out)
