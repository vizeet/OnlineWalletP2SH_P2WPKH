import unittest
import config
import create_raw_txn
from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import shutil
import os
import requests
import json
from utility_adapters import leveldb_utils
import subprocess
import copy
import signal

network_port_map = {
        'regtest': 18443,
        'mainnet': 8332
}

def removeRegtestDir():
        homedir = os.environ.get('HOME')
        shutil.rmtree('%s/.bitcoin/regtest' % os.getenv('HOME'))

class TestBitcoinWallet(unittest.TestCase):
        addr1 = 'bcrt1qxueekwvyeq30n7ye7wjpv44pwy8xath8xhk0r7'
        privkey1 = 'cUcSmC5p2Sr4mVNH2qcAS4YZqVk6tcxzwwvPVDNVfPVPGAsva53Q'
        addr2 = 'bcrt1qdscasv765km9t272ndyhn9vuvxx4t4atf4v26c'
        rpc_user = input('RPC Username: ')
        rpc_password = input('RPC Password: ')

        def establishRPCConnection(self, network: str):
                global network_port_map
                rpc_connection = AuthServiceProxy("http://%s:%s@127.0.0.1:%d" %(self.rpc_user, self.rpc_password, network_port_map[network]))

                return rpc_connection


        def init_blockchain(self):
                global addr1, addr2
                with open('transfer_info.json', 'rt') as transfer_info_f:
                        jsonobj = json.load(transfer_info_f)
                address_list = jsonobj['Addresses'][0:10]
                self.rpc_connection = self.establishRPCConnection('regtest')
                block_list = self.rpc_connection.generatetoaddress(1, self.addr1)
                self.rpc_connection.generatetoaddress(100, self.addr2)

                block = self.rpc_connection.getblock(block_list[0])
                tx_list = block['tx']
                raw_tx = self.rpc_connection.getrawtransaction(tx_list[0], True)

                in_value = float(raw_tx['vout'][0]['value'])
                print('in_value = %f' % in_value)

                tx_in = [{'txid': tx_list[0], "vout": 0}]
                out_value = in_value / (len(address_list) + 1)
                print('out_value = %f' % out_value)
                tx_out = [{address: 4.99} for address in address_list]

                raw_tx = self.rpc_connection.createrawtransaction(tx_in, tx_out)
                print('raw transaction = %s' % raw_tx)

                status = self.rpc_connection.signrawtransactionwithkey(raw_tx, [self.privkey1])

                print('status = %s' % status)

                if status['complete'] == True:
                        print('raw transaction status is complete')
                else:
                        print('raw transaction status is incomplete')

                status = self.rpc_connection.sendrawtransaction(status['hex'])

                print('send transaction status = %s' % status)
                
                tx = self.rpc_connection.getrawtransaction(status, True)
                print('sent transaction = %s' % tx)

                block_list = self.rpc_connection.generatetoaddress(1, self.addr2)
                block =  self.rpc_connection.getblock(block_list[0])
                print('SSSSSSSSSSSSSSS tx list = %s' % block['tx'])

        def run_bitcoind_regtest(self):
                self.process = subprocess.Popen(('bitcoind', '-regtest', '-txindex=1', '-rpcuser=%s' % self.rpc_user, '-rpcpassword=%s' % self.rpc_password), stdout=subprocess.PIPE, preexec_fn=os.setsid)
                while True:
                        output = self.process.stdout.readline()
                        if b'init message: Done loading' in output:
                                break
                        if output:
                                print(output.strip())
                print('Loading Done: bitcoind ready for rpc calls')

        def get_fee_from_mainnet(self):
                process = subprocess.Popen(('bitcoind', '-txindex=1', '-rpcuser=%s' % self.rpc_user, '-rpcpassword=%s' % self.rpc_password), stdout=subprocess.PIPE, preexec_fn=os.setsid)
                while True:
                        output = process.stdout.readline()
                        if b'init message: Done loading' in output:
                                break
                        if output:
                                print(output.strip())
                print('Loading Done: bitcoind ready for rpc calls')

                self.rpc_connection = self.establishRPCConnection('mainnet')

                conf_target = int(input('Transaction to be included in which next block (count)?'))

                fee_per_kb = self.rpc_connection.estimatesmartfee(conf_target)
 
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)

                return float(fee_per_kb['feerate'])

        def setUp(self):
                print('test started')

                header = {"content-type": "application/json", "Accept": "application/json"}
                res = requests.get('http://localhost:11099/addresses', headers = header)
                jsonobj = json.loads(res.text)

                with open('transfer_info.json', 'wt') as transfer_info_f:
                        json.dump(jsonobj, transfer_info_f)

                config.init()

                self.ldb_adapter = leveldb_utils.LevelDBAdapter("regtest")
                config.updateAddressConfig(self.ldb_adapter)

                with open('transfer_info.json', 'rt') as transfer_info_f:
                        print('************** jsonobj = %s' % json.dumps(json.load(transfer_info_f)))

                self.fee_per_kb = self.get_fee_from_mainnet()

                print('fee = %f' % self.fee_per_kb)

                removeRegtestDir()

                try:
                        self.run_bitcoind_regtest()

                        self.init_blockchain()

                        print('I am here')

                except Exception as e:
                        if self.process != None:
                                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

        def test_1_s1_t1(self):
                #print('test1: block count = %d' % self.rpc_connection.getblockcount())
                address = create_raw_txn.getUnusedAddresses()[0]
                config.updateAddressConfig(self.ldb_adapter)
                with open('transfer_info.json', 'rt') as transfer_info_f:
                        print('************** jsonobj = %s' % json.dumps(json.load(transfer_info_f)))

                txout = {}
                txout[address] = 4.0

                txn_obj = create_raw_txn.RawTxn('regtest', self.rpc_user, self.rpc_password)
                txn_obj.setRawTxnFromOuts(txout, fee_rate = self.fee_per_kb)
                with open('transfer_info.json', 'rt') as transfer_info_f:
                        jsonobj = json.load(transfer_info_f)
                res = requests.post('http://localhost:11099/sign_transaction', headers = header, data=json.dumps(jsonobj))
                jsonobj = json.loads(res.text)
                status = rpc_connection.sendrawtransaction(jsonobj['Signed Txn'])
 
                self.assertContains(status, 'error')

#        def test_1source_1target(self):
#                self.assertTrue(True)

        def tearDown(self):
                if self.process != None:
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

if __name__ == '__main__':
        unittest.main()
