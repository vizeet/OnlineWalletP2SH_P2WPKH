import json

def init():
        jsonobj = json.load(open('transfer_info.json', 'wt'))

        jsonobj['Confirmation Target Block'] = int(input('Confirmation Target Block for fee estimation: '))

        jsonobj['Address Value Threshold'] = float(input('Address Value Threshold: '))

        json.dump(jsonobj, open('transfer_info.json', 'wt'))

# To be called offline
def updateAddressConfig(jsonobj: dict, ldb_adapter):
        inuse_addresses = jsonobj['In-use Addresses'].keys()
        inuse_address_map = ldb_adapter_g.getRequiredTxnsInP2SH(inuse_addresses)

        if len(inuse_addresses_map) == 0:
                addresses = jsonobj['Addresses']
                inuse_address_map = ldb_adapter_g.getRequiredTxnsInP2SH(addresses)

        inuse_addresses_updated = inuse_address_map.keys()

        used_addresses = list(set(inuse_addresses) - set(inuse_addresses_updated))
        jsonobj['Used Addresses'] = used_addresses

        jsonobj['In-use Addresses'] = inuse_address_map
        unused_addresses = jsonobj['Unused Addresses']
        unused_addresses = list(set(unused_addresses) - set(inuse_addresses_updated))
        jsonobj['Unused Addresses'] = unused_addresses
