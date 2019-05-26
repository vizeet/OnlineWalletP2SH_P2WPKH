from utils import leveldb_class
import pubkey_address
import binascii

class LevelDBAdapter:
        def __init__(self, nettype: str):
                self.nettype = nettype
                self.ldb = leveldb_class.LevelDB(nettype = nettype)

        def check_addresses_unused(self, addresses: list):
                #it = chainstate_db.iterator(include_value=False)
                it = self.ldb.getIteratorChainstateDB()
                required_hash160_b_list = [pubkey_address.address2hash(address) for address in addresses]
                for required_h160 in required_hash160_b_list:
                        print('required_h160 = %s' % (bytes.decode(binascii.hexlify(required_h160))))

                inuse_addresses = []

                counter = len(addresses)
                while  counter > 0:
                        try:
                                key = next(it)
                        except StopIteration:
                                break
                        prefix = key[0:1]
                        if prefix == b'C':
                                out_index, pos = leveldb_class.b128_varint_decode(key[33:])
                                txn_hash_big_endian_b = key[1:33]
                                txn_hash_little_endian = bytes.decode(binascii.hexlify(key[1:33][::-1]))
                                jsonobj = self.ldb.getChainstateData(txn_hash_big_endian_b, out_index)
                                if jsonobj['script_type'] == 1:
                                        size_hash = int(binascii.hexlify(jsonobj['script'][1:2]), 16)
                                        hash160_b = jsonobj['script'][2:2 + size_hash]
                                        print('hash160 = %s' % bytes.decode(binascii.hexlify(hash160_b)))
                                        recent_block_hash = self.ldb.getRecentBlockHash()
                                        recent_block_height = self.ldb.getBlockIndex(recent_block_hash)['height']
                                        block_height = jsonobj['height']
                                        block_depth = recent_block_height - block_height
                                        print('block depth = %d' % block_depth)
                                        # coinbase transaction can be redeemed only after 100th confirmation
                                        if jsonobj['is_coinbase'] == True and block_depth < 100:
                                                continue
                                        if hash160_b in required_hash160_b_list:
                                                inuse_addresses.append(pubkey_address.sh2address(hash160_b, self.nettype))
                                                counter = counter - 1
                return inuse_addresses

        def getRequiredTxnsInP2SH(self, addresses: list):
                it = self.ldb.getIteratorChainstateDB()
                required_hash160_b_list = [pubkey_address.address2hash(address) for address in addresses]
                for required_h160 in required_hash160_b_list:
                        print('required_h160 = %s' % (bytes.decode(binascii.hexlify(required_h160))))
                ret_dict = {}
                while True:
                        try:
                                key = next(it)
                        except StopIteration:
                                break
                        prefix = key[0:1]
                        if prefix == b'C':
                                out_index, pos = leveldb_class.b128_varint_decode(key[33:])
                                txn_hash_big_endian_b = key[1:33]
                                txn_hash_little_endian = bytes.decode(binascii.hexlify(key[1:33][::-1]))
                                jsonobj = self.ldb.getChainstateData(txn_hash_big_endian_b, out_index)
                                #print('chainstate data = %s' % jsonobj)
                                if jsonobj['script_type'] == 1 :
                                        size_hash = int(binascii.hexlify(jsonobj['script'][1:2]), 16)
                                        hash160_b = jsonobj['script'][2:2 + size_hash]
                                        print('script = %s' % bytes.decode(binascii.hexlify(jsonobj['script'])))
                                        print('amount = %d' % jsonobj['amount'])
                                        #print('hash160 = %s' % bytes.decode(binascii.hexlify(hash160_b)))
                                        #print('Is coinbase = %r' % jsonobj['is_coinbase'] == True)
                                        #print('In the list = %r' % hash160_b in required_hash160_b_list)
                                        recent_block_hash = self.ldb.getRecentBlockHash()
                                        recent_block_height = self.ldb.getBlockIndex(recent_block_hash)['height']
                                        block_height = jsonobj['height']
                                        block_depth = recent_block_height - block_height
                                        # coinbase transaction can be redeemed only after 100th confirmation
                                        if jsonobj['is_coinbase'] == True and block_depth < 100:
                                                continue
                                        if hash160_b in required_hash160_b_list:
                                                address = pubkey_address.sh2address(hash160_b, self.nettype)
                                                if address not in ret_dict:
                                                        ret_dict[address] = {}
                                                ret_dict[address][txn_hash_little_endian] = []
                                                ret_dict[address][txn_hash_little_endian].append({"out_index": out_index, "value": jsonobj['amount']})
                return ret_dict


if __name__ == '__main__':
        ldb = LevelDBAdapter('regtest')
        jsobobj = ldb.getRequiredTxnsForAmountInP2SH('2MxsKZXkDiaJw5LbHyzNGBGksM42MF7GXMh', 150)
        print('jsonobj = %s' % jsonobj)
