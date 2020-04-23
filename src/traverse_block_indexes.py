from block_parser import getBlock, sync_address_set, init_address_set
from leveldb_parser import getBlockIndex, getRecentBlockHash
import os
import mmap
import binascii
import datetime
import logging
import plyvel

logging.basicConfig(filename='addresses.log', filemode='w', level=logging.INFO)

def create_update_used_p2sh_address_list():
    block_db = plyvel.DB(os.getenv('BLOCK_INDEX_DB'), compression=None)
    chainstate_db = plyvel.DB(os.getenv('CHAINSTATE_DB'), compression=None)
    blocks_path = os.getenv('BLOCKS_PATH')

    initial_blockhash_bigendian_b = getRecentBlockHash(chainstate_db)
    chainstate_db.close()
    print('initial blockhash = %s' % bytes.decode(binascii.hexlify(initial_blockhash_bigendian_b[::-1])))
    prev_blockhash_bigendian_b = initial_blockhash_bigendian_b

    last_blockhash_bigendian_b = b''
    if os.path.exists('last_block.hash'):
        with open('last_block.hash', 'rb') as last_blockhash_f:
            last_blockhash_bigendian_b = last_blockhash_f.read()
    else:
        print('Generating used address list for the first time.. May take few hours to complete.')

    jsonobj = getBlockIndex(prev_blockhash_bigendian_b, block_db)
    index = (jsonobj['height'] - 500000) // 10000
    init_address_set(index)

    if initial_blockhash_bigendian_b == last_blockhash_bigendian_b:
        return

    while True:
        print('prev blockhash = %s' % bytes.decode(binascii.hexlify(prev_blockhash_bigendian_b[::-1])))
        if prev_blockhash_bigendian_b == last_blockhash_bigendian_b:
            print('last blockhash = %s' % bytes.decode(binascii.hexlify(last_blockhash_bigendian_b[::-1])))
            break

        jsonobj = getBlockIndex(prev_blockhash_bigendian_b, block_db)
        if 'data_pos' in jsonobj:
            block_filepath = os.path.join(blocks_path, 'blk%05d.dat' % jsonobj['n_file'])
            start = jsonobj['data_pos']
            print('height = %d' % jsonobj['height'])
        elif 'undo_pos' in jsonobj:
            block_filepath = os.path.join(blocks_path, 'rev%05d.dat' % jsonobj['n_file'])
            start = jsonobj['undo_pos']

        # load file to memory
        with open(block_filepath, 'rb') as block_file:
            with mmap.mmap(block_file.fileno(), 0, prot = mmap.PROT_READ, flags = mmap.MAP_PRIVATE) as mptr: #File is open read-only
                prev_blockhash_bigendian_b = getBlock(mptr, start)
            
        if jsonobj['height'] == 500000:
            break

        if jsonobj['height'] % 10000 == 0:
            index = (jsonobj['height'] - 500000) // 10000
            sync_address_set(index)

    block_db.close()

    block_file.close()

    index = (jsonobj['height'] - 500000) // 10000
    sync_address_set(index)

    with open('last_block.hash', 'wb') as last_blockhash_f:
        last_blockhash_f.write(initial_blockhash_bigendian_b)

if __name__ == '__main__':
    start_time = str(datetime.datetime.now())
    logging.info(start_time)
    create_update_used_p2sh_address_list()
    end_time = str(datetime.datetime.now())
    logging.info(end_time)
