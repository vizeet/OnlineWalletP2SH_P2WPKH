import unittest
import config
import create_raw_transaction
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import shutil
import os

app = Flask(__name__)

network_port_map = {
        'regtest': 18443,
        'mainnet': 8332
}

def removeRegtestDir():
        homedir = os.environ.get('HOME')
        shutil.rmtree('%s/.bitcoin/regtest')

def establishRPCConnection(network: str):
        rpc_user = input('RPC Username: ')
        rpc_password = input('RPC Password: ')
        
        rpc_connection = authserviceproxy("http://%s:%s@127.0.0.1:%d" %(rpc_user, rpc_password, network_port_map[network]))

        return rpc_user, rpc_password, rpc_connection

class TestBitcoinWallet(unittest.TestCase):
        addr1 = 'bcrt1qxueekwvyeq30n7ye7wjpv44pwy8xath8xhk0r7'
        privkey1 = 'cUcSmC5p2Sr4mVNH2qcAS4YZqVk6tcxzwwvPVDNVfPVPGAsva53Q'
        addr2 = 'bcrt1qdscasv765km9t272ndyhn9vuvxx4t4atf4v26c'

        def init_blockchain():
                global addr1, addr2
                address_list = json.load(open('transfer_info.json', 'rt'))
                self.rpc_user, self.rpc_password, self.rpc_connection = establishRPCConnection('regtest')
                block_list = self.rpc_connection.generatetoaddress(1, self.addr1)
                self.rpc_connection.generatetoaddress(100, self.addr2)

                block = rpc_connection.getblock(block_list[0])
                tx_list = block['tx']
                raw_tx = rpc_connection.getrawtransaction(tx_list[0], True)

                in_value = float(raw_tx['vout'][0]['value'])
                print('in_value = %f' % in_value)

                tx_in = [{'txid': tx_list[0], "vout": 0}]
                tx_out = [{address: 0.1} for address in address_list]

                raw_tx = rpc_connection.createrawtransaction(tx_in, tx_out)
                print('raw transaction = %s' % new_raw_tx)

                status = rpc_connection.signrawtransactionwithkey(raw_tx, [privkey1])

                print('status = %s' % status)

                if status['complete'] == True:
                        print('raw transaction status is complete')
                else:
                        print('raw transaction status is incomplete')

                status = rpc_connection.sendrawtransaction(status['hex'])

                print('send transaction status = %s' % status)

        def run_bitcoind_regtest(self):
                self.process = subprocess.Popen(('bitcoind', '-regtest', '-txindex=1', '-rpcuser=%s' % self.rpc_user, '-rpcpassword=%s' % self.rpc_password), stdout=subprocess.PIPE)
                while True:
                        output = self.process.stdout.readline()
                        if b'init message: Done loading' in output:
                                break
                        if output:
                                print(output.strip())
                print('Loading Done: bitcoind ready for rpc calls')

        def get_fee_from_mainnet(self):
                process = subprocess.Popen(('bitcoind', '-regtest', '-txindex=1', '-rpcuser=%s' % self.rpc_user, '-rpcpassword=%s' % self.rpc_password), stdout=subprocess.PIPE)
                while True:
                        output = process.stdout.readline()
                        if b'init message: Done loading' in output:
                                break
                        if output:
                                print(output.strip())
                print('Loading Done: bitcoind ready for rpc calls')

                self.rpc_user, self.rpc_password, self.rpc_connection = establishRPCConnection('mainnet')

                conf_target = int(input('Transaction to be included in which next block (count)?'))

                fee_per_kb = self.rpc_connection.estimatesmartfee(conf_target)
 
                process.kill()

                return fee_per_kb

        def setUp(self):
                config.init()
                res = request.post('http://localhost:11099/addresses', headers={"content-type":"application/json"})
                data = res.data
                jsonobj = json.loads(data)

                ldb_adapter = leveldb_utils.LevelDBAdapter("regtest")
                config.updateAddressConfig(jsonobj, ldb_adapter)

                self.fee_per_kb = self.get_fee_from_mainnet()

                removeRegtestDir()

                self.run_bitcoind_regtest()

                init_blockchain():

        def test_1source_1target(self):
                self.assertEqual( 3*4, 12)

        def tearDown(self):
                self.process.kill()
