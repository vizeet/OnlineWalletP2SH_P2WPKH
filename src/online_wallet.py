import json
import create_raw_txn
from optparse import OptionParser
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException

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

                rpc_user = input('RPC Username: ')
                rpc_password = input('RPC Password: ')
                self.rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:%d" %(rpc_user, rpc_password, network_port_map_g[network]))
                self.network = network
                self.transfer_info_filepath = datadir + '/' + transfer_info_map_g[network]

        def validateAddresses(self):
                with open(self.transfer_info_filepath, 'rt') as transfer_file_f:
                        jsonobj = json.load(transfer_file_f)

                address_valid_map = {}
                for address in jsonobj['Addresses']:
                       address_valid_map[address] = self.rpc_connection.validateaddress(address)['isvalid']
                return address_valid_map

        def setNewAddresses(addresses: list):
                existing_addresses = self.rpc_connection.getaddressesbyaccount('')
                new_addresses = set(addresses) - set(existing_addresses)

                return new_addresses

        def registerAddresses(addresses: list):
                new_addresses = setNewAddresses(addresses)

                s = []
                for address in self.new_addresses:
                        i = {'scriptPubKey': {'address': address}, 'timestamp': 0}
                        s.append(i)

                self.rpc_connection.importmulti(s)

                return new_addresses

        def populateInuseAddressMap(unspent_list: list):
                inuse_address_map = {}
                for unspent in unspent_list:
                        address = unspent['address']
                        if address not in inuse_address_map:
                                inuse_address_map[address] = {}
                        txid = unspent['txid']
                        if txid not in inuse_address_map[address]:
                                inuse_address_map[address][txid] = []
                        vout = unspent['vout']
                        amount = unspent['amount']
                        self.inuse_address_map[address][txid].append({'vout': vout, 'amount': amount})

        def updateAddresses():
                with open(self.transfer_info_filepath, 'rt') as transfer_file_f:
                        jsonobj = json.load(transfer_file_f)

                unspent_list = self.rpc_connections.listunspent()
                self.populateInuseAddressMap(unspent_list)

                inuse_addresses = [unspent['address'] for unspent in unspent_list]

                new_used_addresses = set(jsonobj['In-use Addresses']) - set(inuse_addresses)

                jsonobj['In-use Addresses'] = inuse_addresses

                jsonobj['Used Addresses'] = list(set(jsonobj['Used Addresses']).union(new_used_addresses))

        def createRawTxn(self):
                with open(self.transfer_info_filepath, 'rt') as transfer_file_f:
                        jsonobj = json.load(transfer_file_f)

                if jsonobj['Address Flag'] == 'modified':
                        new_addresses = self.registerAddresses(jsonobj['Addresses'])
                        jsonobj['Unused Addresses'].extend(new_addresses)
                        jsonobj['Address Flag'] = 'registered'
                self.updateAddresses()

                raw_txn = create_raw_txn.RawTxn(self.network, self.rpc_connection, self.transfer_info_filepath)
                fee_rate = 0.00005
                txout = raw_txn.getTargetAddresses()
                raw_txn.setRawTxnFromOuts(txout, fee_rate=fee_rate)

        def publishSignedTxn(self):
                with open(self.transfer_info_filepath, 'rt') as transfer_file_f:
                        jsonobj = json.load(transfer_file_f)

                return self.rpc_connection.sendrawtransaction(jsonobj['Signed Txn'])

if __name__ == '__main__':
        parser = OptionParser()
        parser.add_option("-t", "--test",
                  action="store_true", dest="test",
                  help="Execute in Test Mode")
        (options, _) = parser.parse_args()

        if options.test:
                network = 'regtest'
                datadir = '/tmp/share'
        else:
                with open('../config/hd_wallet.conf', 'rt') as conf_f:
                        jsonobj = json.load(conf_f)
                network = jsonobj['network']
                datadir = jsonobj['datadir']

        print('1. Validate Addresses')
        print('2. Create Raw Transaction')
        print('3. Publish Signed Transaction')
        choice = int(input('Selection: '))

        wallet = Wallet(network, datadir)

        if choice == 1:
                address_valid_map = wallet.validateAddresses()
                print(address_valid_map)
        elif choice == 2:
                wallet.createRawTxn()
        elif choice == 3:
                status = wallet.publishSignedTxn()
                print(status)
        else:
                print('Invalid selection')
