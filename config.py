import json

def init():
        jsonobj = {}

        jsonobj['Confirmation Target Block'] = int(input('Confirmation Target Block for fee estimation: '))

        jsonobj['Address Value Threshold'] = float(input('Address Value Threshold: '))

        with open('transfer_info.json', 'wt') as f_transfer_info:
                json.dump(jsonobj, f_transfer_info)

# To be called offline
def updateAddressConfig(jsonobj: dict, ldb_adapter):
        print('aaaa jsonobj[In-use Addresses] = %s' % jsonobj['In-use Addresses'])
        inuse_addresses = jsonobj['In-use Addresses'].keys()
        inuse_address_map = ldb_adapter.getRequiredTxnsInP2SH(inuse_addresses)

        if len(inuse_addresses_map) == 0:
                addresses = jsonobj['Addresses']
                inuse_address_map = ldb_adapter.getRequiredTxnsInP2SH(addresses)

        inuse_addresses_updated = inuse_address_map.keys()

        used_addresses = list(set(inuse_addresses) - set(inuse_addresses_updated))
        jsonobj['Used Addresses'] = used_addresses

        jsonobj['In-use Addresses'] = inuse_address_map
        unused_addresses = jsonobj['Unused Addresses']
        unused_addresses = list(set(unused_addresses) - set(inuse_addresses_updated))
        jsonobj['Unused Addresses'] = unused_addresses
