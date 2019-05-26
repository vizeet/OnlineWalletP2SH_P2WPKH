from utility_adapters import bitcoin_secp256k1
from utility_adapters import bitcoin_base58
from utility_adapters.bitcoin_secp256k1 import P
import binascii
import hashlib
from utility_adapters import hash_utils
from utils import base58
from ecdsa import SigningKey, SECP256k1

# uncompressed public key has b'\x04' prefix
def compressPubkey(pubkey: bytes):
        x_b = pubkey[1:33]
        y_b = pubkey[33:65]
        if (y_b[31] & 0x01) == 0: # even
                compressed_pubkey = b'\x02' + x_b
        else:
                compressed_pubkey = b'\x03' + x_b
        return compressed_pubkey

def privkeyHex2pubkey(privkey_s: str):
        compress = False
        if len(privkey_s) == 66:
                privkey_s = privkey_s[0:64]
                compress = True
        privkey_i = int(privkey_s, 16)
        return privkey2pubkey(privkey_i, compress)

#def privkey2pubkey(privkey: int, compress = True):
#        bitcoin_sec256k1 = bitcoin_secp256k1.BitcoinSec256k1()
#        pubkey = bitcoin_sec256k1.privkey2pubkey(privkey)
##        full_pubkey = b'\x04' + binascii.unhexlify(str('%064x' % pubkey[0])) + binascii.unhexlify(str('%064x' % pubkey[1]))
#        pubkey = binascii.unhexlify('04%064x%064x' % (pubkey[0],pubkey[1]))
#        if compress == True:
#                pubkey = compressPubkey(pubkey)
#        return pubkey

def privkey2pubkey(privkey: int, compress = True):
        privkey_s = '%064x' % privkey
        if privkey_s.__len__() % 2 == 1:
                privkey_s = "0{}".format(privkey_s)

        privkey_b = binascii.unhexlify(privkey_s)
        sk = SigningKey.from_string(privkey_b, curve=SECP256k1)
        vk = sk.get_verifying_key()

        pubkey_b = b'\x04' + vk.to_string()
        if compress == True:
                pubkey_b = compressPubkey(pubkey_b)

        return pubkey_b

def privkey2Wif(privkey: int, nettype: str, compress = True):
        wif = bitcoin_base58.encodeWifPrivkey(privkey, nettype, compress)
        return wif

def privkeyWif2Hex(privkey: str):
        nettype, prefix, privkey_s, for_compressed_pubkey = bitcoin_base58.decodeWifPrivkey(privkey)
        if privkey_s.__len__() % 2 == 1:
                privkey_s = "0{}".format(privkey_s)
        return privkey_s

def privkeyWif2pubkey(privkey: str):
        privkey_s = privkeyWif2Hex(privkey)
        pubkey = privkeyHex2pubkey(privkey_s)
        return pubkey

def pkh2address(pkh: bytes, nettype: str):
        address = bitcoin_base58.forAddress(pkh, nettype, False)
        return address

def sh2address(sh: bytes, nettype: str):
        address = bitcoin_base58.forAddress(sh, nettype, True)
        return address

def pkh2addressLTC(pkh: bytes):
        address = litecoin_base58.forAddress(pkh, "mainnet", False)
        return address

def pubkey2address(pubkey: bytes):
        pkh = hash_utils.hash160(pubkey)
        print('pkh = %s' % bytes.decode(binascii.hexlify(pkh)))
        address = pkh2address(pkh)
        return address

def pubkey2addressLTC(pubkey: bytes):
        pkh = hash_utils.hash160(pubkey)
        print('pkh = %s' % bytes.decode(binascii.hexlify(pkh)))
        address = pkh2addressLTC(pkh)
        return address

def address2hash(address: str):
        is_segwit = (address[0:3] == 'bc1' or address[0:3] == 'tb1' or address[0:5] == 'bcrt1')
        if is_segwit:
                hrp, h_list = bech32.bech32_decode(address)
                witver, h_list = bech32.decode(hrp, address)
                print('h_list = %s' % h_list)
                h_b = bytes(h_list)
        else:
                #h_b = base58.base58checkDecode(privkey_wif)
                print('IIIIII address = %s' % address)
                h_b = base58.base58checkDecode(address)
        return h_b
