import plyvel
import os
import binascii
import json

BLOCK_HAVE_DATA          =    8
BLOCK_HAVE_UNDO          =   16

def b128_varint_decode(value: bytes, pos = 0):
    """
    Reads the weird format of VarInt present in src/serialize.h of bitcoin core
    and being used for storing data in the leveldb.
    This is not the VARINT format described for general bitcoin serialization
    use.
    """
    n = 0
    while True:
        data = value[pos]
        pos += 1
        n = (n << 7) | (data & 0x7f) # 1111111
        if data & 0x80 == 0: # each byte is greater than or equal to 0x80 except at the end
            return (n, pos)
        n += 1

def getObfuscationKey(chainstate_db):
        value = chainstate_db.get(b'\x0e\x00' + b'obfuscate_key')
        print('obfuscation key = %s' % value)
        obfuscation_key = value[1:]
        return obfuscation_key

def applyObfuscationKey(data: bytes, chainstate_db):
        obfuscation_key = getObfuscationKey(chainstate_db)
        new_val = bytes(data[index] ^ obfuscation_key[index % len(obfuscation_key)] for index in range(len(data)))
        return new_val

def getFullPubKeyFromCompressed(x_b: bytes):
        prefix = x_b[0:1]
        print('prefix = %s' % prefix)
        p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
        print('(p+1)/4 = %d' % ((p + 1) >> 2))
        x_b = x_b[1:33]
        x = int.from_bytes(x_b, byteorder='big')

        y_square = (pow(x, 3, p)  + 7) % p
        y_square_square_root = pow(y_square, ((p+1) >> 2), p)
        if (prefix == b"\x02" and y_square_square_root & 1) or (prefix == b"\x03" and not y_square_square_root & 1):
            y = (-y_square_square_root) % p
        else:
            y = y_square_square_root

        y_b = y.to_bytes(32, 'big')
        full_pubkey_b = b''.join([b'\x04', x_b, y_b])
        return full_pubkey_b

def uncompressScript(script_type: int, script_data: bytes):
        if script_type == 0:
                script = bytes([
                        0x76, # OP_DUP
                        0xa9, # OP_HASH160
                        20 # size
                        ]) + script_data + bytes([
                        0x88, # OP_EQUALVERIFY
                        0xac # OP_CHECKSIG
                        ])
        elif script_type == 1:
                script = bytes([
                        0xa9, # OP_HASH160
                        20 # size
                        ]) + script_data + bytes([
                        0x87, # OP_EQUAL
                        ])
        elif script_type in [2, 3]:
                script = bytes([
                        33, # size
                        script_type
                        ]) + script_data + bytes([
                        0xac # OP_CHECKSIG
                        ])
        elif script_type in [4, 5]: # script_type = 4 means y is odd and script_type = 5 means y is even in compressed pubkey
                compressed_pubkey = bytes([script_type - 2]) + script_data
                pubkey = getFullPubKeyFromCompressed(compressed_pubkey)
                script = bytes([
                        65 # size
                        ]) + pubkey + bytes([
                        0xac # OP_CHECKSIG
                        ])
        else: 
                script = script_data
 
        return script

def getBlockIndex(block_hash_bigendian: bytes, block_db):
        key = b'b' + block_hash_bigendian
#        print(key)
        value = block_db.get(key)
        jsonobj = {}
        jsonobj['version'], pos = b128_varint_decode(value)
        jsonobj['height'], pos = b128_varint_decode(value, pos)
        jsonobj['status'], pos = b128_varint_decode(value, pos)
        jsonobj['txn_count'], pos = b128_varint_decode(value, pos)
        if jsonobj['status'] & (BLOCK_HAVE_DATA | BLOCK_HAVE_UNDO):
                jsonobj['n_file'], pos = b128_varint_decode(value, pos)
        if jsonobj['status'] & BLOCK_HAVE_DATA:
                jsonobj['data_pos'], pos = b128_varint_decode(value, pos)
        if jsonobj['status'] & BLOCK_HAVE_UNDO:
                jsonobj['undo_pos'], pos = b128_varint_decode(value, pos)
        return jsonobj

def getRecentBlockHash(chainstate_db):
        key = b'B'
#        print(key)
        block_hash_b = chainstate_db.get(key)
        block_hash_b = applyObfuscationKey(block_hash_b, chainstate_db)
        return block_hash_b

