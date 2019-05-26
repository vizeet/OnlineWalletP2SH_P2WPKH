import json

def init():
        with open('transfer_info.json', 'rt') as f_transfer_info:
                jsonobj = json.load(f_transfer_info)

        jsonobj['Confirmation Target Block'] = int(input('Confirmation Target Block for fee estimation: '))

        jsonobj['Address Value Threshold'] = float(input('Address Value Threshold: '))

        with open('transfer_info.json', 'wt') as f_transfer_info:
                json.dump(jsonobj, f_transfer_info)

# To be called offline
def updateAddressConfig(ldb_adapter):
        with open('transfer_info.json', 'rt') as f_transfer_info:
                jsonobj = json.load(f_transfer_info)
        inuse_addresses = []
        inuse_addresses_map = {}
        addresses = jsonobj['Addresses']
        if 'In-use Addresses' in jsonobj and len(jsonobj['In-use Addresses']) > 0:
                inuse_addresses = jsonobj['In-use Addresses'].keys()
                inuse_address_map = ldb_adapter.getRequiredTxnsInP2SH(inuse_addresses)
                inuse_addresses_updated = inuse_address_map.keys()

                used_addresses = list(set(inuse_addresses) - set(inuse_addresses_updated))
                jsonobj['Used Addresses'].extend(used_addresses)
        else:
                inuse_address_map = ldb_adapter.getRequiredTxnsInP2SH(addresses)
                print('inuse_address_map = %s' % inuse_address_map)

                inuse_addresses_updated = inuse_address_map.keys()

        jsonobj['In-use Addresses'] = inuse_address_map
        if 'Unused Addresses' in jsonobj and jsonobj['Unused Addresses']:
                unused_addresses = jsonobj['Unused Addresses']
                unused_addresses = list(set(unused_addresses) - set(inuse_addresses_updated))
                jsonobj['Unused Addresses'] = unused_addresses
        else:
                unused_addresses = list(set(addresses) - set(inuse_addresses_updated))
                jsonobj['Unused Addresses'] = unused_addresses

        with open('transfer_info.json', 'wt') as f_transfer_info:
                json.dump(jsonobj, f_transfer_info)
