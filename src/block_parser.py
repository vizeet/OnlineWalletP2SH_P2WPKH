import os
import binascii
import mmap
import bitcoin_base58
import pickle

def getCount(mptr: mmap):
        mptr_read = mptr.read(1)
        txn_size = int(binascii.hexlify(mptr_read), 16)

        if txn_size < 0xfd:
                return txn_size
        elif txn_size == 0xfd:
                mptr_read = mptr.read(2)
                txn_size = int(binascii.hexlify(mptr_read[::-1]), 16)
                return txn_size
        elif txn_size == 0xfe:
                mptr_read = mptr.read(4)
                txn_size = int(binascii.hexlify(mptr_read[::-1]), 16)
                return txn_size
        else:
                mptr_read = mptr.read(8)
                txn_size = int(binascii.hexlify(mptr_read[::-1]), 16)
                return txn_size

def getPrevBlockHeaderHash(mptr: mmap, start: int):
        seek = start + 4 ## ignore block version
        mptr.seek(seek)
        prev_block_hash = mptr.read(32)
        return prev_block_hash

def getTransactionCount(mptr: mmap):
        txn_count = getCount(mptr)
        return txn_count

address_set_g = set()

def init_address_set(index: int):
    global address_set_g
    filename = 'address_' + str(index) + '.set'
    if os.path.exists(filename):
        with open(filename, 'rb') as address_set_f:
            address_set_g = pickle.load(address_set_f)
    print('index = %d' % index)
#    print(address_set_g)

def get_address_set():
    global address_set_g
    return address_set_g

def update_address_set(address: str):
    global address_set_g
    address_set_g.add(address)

def sync_address_set(index: int):
    global address_set_g
    with open('address_' + str(index) + '.set', 'wb') as address_set_f:
        pickle.dump(get_address_set(), address_set_f)
    del address_set_g
    address_set_g = set()
    print('index = %d' % index)


def getCoinbaseTransaction(mptr: mmap):
        mptr.read(4)
        input_count = getCount(mptr)
        is_segwit = False
        if input_count == 0:
                # post segwit
                is_segwit = bool(mptr.read(1))
                input_count = getCount(mptr)

        for index in range(input_count):
                mptr.read(36)
                coinbase_data_size = getCount(mptr)
                mptr.read(coinbase_data_size + 4)

        out_count = getCount(mptr)
        for index in range(out_count):
                mptr.read(8)
                scriptpubkey_size = getCount(mptr)
                mptr_read = mptr.read(scriptpubkey_size)
                if isP2SH(mptr_read):
                        update_address_set(getAddressFromP2SH(mptr_read))
        if is_segwit == True:
                for index in range(input_count):
                        witness_count = getCount(mptr)
                        for inner_index in range(witness_count):
                                txn_witness_size = getCount(mptr)
                                mptr.read(txn_witness_size)
        mptr.read(4)

def isP2SH(script_pub_key: bytes):
        if len(script_pub_key) == 23 and script_pub_key[:2] == bytes([0xa9, 0x14]) and script_pub_key[-1:] == bytes([0x87]):
                return True
        return False

def getAddressFromP2SH(script: bytes):
        sh = script[2:22]
        address = bitcoin_base58.forAddress(sh, False, True) # Mainnet, P2SH
        return address

def getTransaction(mptr: mmap):
        mptr.read(4)
        input_count = getCount(mptr)
        is_segwit = False
        if input_count == 0:
                # post segwit
                is_segwit = bool(mptr.read(1))
                input_count = getCount(mptr)

        for index in range(input_count):
                mptr.read(36)
                scriptsig_size = getCount(mptr)
                mptr.read(scriptsig_size + 4)
        out_count = getCount(mptr)
        for index in range(out_count):
                mptr.read(8)
                scriptpubkey_size = getCount(mptr)
                mptr_read = mptr.read(scriptpubkey_size)
                if isP2SH(mptr_read):
                        update_address_set(getAddressFromP2SH(mptr_read))

        if is_segwit == True:
                for index in range(input_count):
                        witness_count = getCount(mptr)
                        for inner_index in range(witness_count):
                                txn_witness_size = getCount(mptr)
                                mptr.read(txn_witness_size)
        mptr.read(4)

def getBlock(mptr: mmap, start: int):
        prev_block_header_hash = getPrevBlockHeaderHash(mptr, start)

        start += 80
        mptr.seek(start) ## skip block header
        txn_count = getTransactionCount(mptr)
#        print('transaction count = %d' % txn_count)
#        logging.debug('transaction count = %d' % txn_count)

        getCoinbaseTransaction(mptr)
        for index in range(1, txn_count):
                getTransaction(mptr)

        return prev_block_header_hash

