import binascii
from neo.BigInteger import BigInteger
from neo.Fixed8 import Fixed8
from neo.Core.Helper import Helper
from neo.Core.Blockchain import Blockchain
from neo.Wallets.Coin import CoinState
from neo.Core.TX.Transaction import TransactionInput
from neo.UInt256 import UInt256
import json


def get_asset_attachments(params):

    to_remove = []
    neo_to_attach = None
    gas_to_attach = None

    for item in params:

        if type(item) is str:
            if '--attach-neo=' in item:
                to_remove.append(item)
                try:
                    neo_to_attach = Fixed8.TryParse(int(item.replace('--attach-neo=', '')))
                except Exception as e:
                    pass
            if '--attach-gas=' in item:
                to_remove.append(item)
                try:
                    gas_to_attach = Fixed8.FromDecimal(float(item.replace('--attach-gas=', '')))
                except Exception as e:
                    pass
    for item in to_remove:
        params.remove(item)


    return params, neo_to_attach, gas_to_attach


def get_asset_id(asset_str):
    assetId = None

    if asset_str.lower() == 'neo':
        assetId = Blockchain.Default().SystemShare().Hash
    elif asset_str.lower() == 'gas':
        assetId = Blockchain.Default().SystemCoin().Hash
    elif Blockchain.Default().GetAssetState(asset_str):
        assetId = Blockchain.Default().GetAssetState(asset_str).AssetId

    return assetId

def get_asset_amount(amount, assetId):

    f8amount = Fixed8.TryParse(amount)
    if f8amount is None:
        print("invalid amount format")

    elif f8amount.value % pow(10, 8 - Blockchain.Default().GetAssetState(assetId.ToBytes()).Precision) != 0:
        print("incorrect amount precision")
        return None

    return f8amount


def get_withdraw_from_watch_only(wallet, scripthash_from):
    withdraw_from_watch_only=0
    #check to see if contract address is in the wallet
    wallet_contract = wallet.GetContract(scripthash_from)

    #if it is not, check to see if it in the wallet watch_addr
    if wallet_contract is None:
        if scripthash_from in wallet._watch_only:
            withdraw_from_watch_only = CoinState.WatchOnly
            wallet_contract = scripthash_from

    if wallet_contract is None:
        print("please add this contract into your wallet before withdrawing from it")
        print("Use import watch_addr {ADDR}, then rebuild your wallet")
        return None

    return withdraw_from_watch_only

def get_from_addr(params):
    to_remove = []
    from_addr = None
    for item in params:
        if '--from-addr=' in item:
            to_remove.append(item)
            try:
                from_addr = item.replace('--from-addr=', '')
            except Exception as e:
                pass
    for item in to_remove:
        params.remove(item)


    return params, from_addr


def parse_param(p, ignore_int=False, prefer_hex=True):

#    print("parsing param: %s " % p)

#    pdb.set_trace()

    #first, we'll try to parse an array
    try:
        items = eval(p)
        if len(items) > 0 and type(items) is list:

            parsed = []
            for item in items:
                parsed.append(parse_param(item))
            return parsed

    except Exception as e:
#        print("couldnt eval items as array %s " % e)
        pass

    if not ignore_int:
        try:
            val = int(p)
            out = BigInteger(val)
            return out
        except Exception as e:
            pass

    try:
        val = eval(p)

        if type(val) is bytearray:
            return val.hex()

        return val
    except Exception as e:
        pass

    if type(p) is str:

        # check for address strings like 'ANE2ECgA6YAHR5Fh2BrSsiqTyGb5KaS19u' and
        # convert them to a bytearray
        if len(p) == 34 and p[0] == 'A':
            addr = Helper.AddrStrToScriptHash(p).Data
            return addr

        if prefer_hex:
            return binascii.hexlify( p.encode('utf-8'))
        else:
            return p.encode('utf-8')


    return p



def get_arg(arguments, index=0, convert_to_int=False, do_parse=False):
    try:
        arg = arguments[index]
        if convert_to_int:
            return int(arg)
        if do_parse:
            return parse_param(arg)
        return arg
    except Exception as e:
        pass
    return None


def parse_hold_vins(results):
    print("results!!! %s " % results)

    holds = results[0].GetByteArray()
    holdlen = len(holds)
    numholds = int(holdlen / 33)
    print("holds, holdlen, numholds %s %s " % (holds, numholds))
    vins = []
    for i in range(0, numholds):
        hstart = i * 33
        hend = hstart + 33
        item = holds[hstart:hend]

        vin_index = item[0]
        vin_tx_id = UInt256(data=item[1:])
        print("VIN INDEX, VIN TX ID: %s %s" % (vin_index, vin_tx_id))

        t_input = TransactionInput(prevHash=vin_tx_id, prevIndex=vin_index)

        print("found tinput: %s " % json.dumps(t_input.ToJson(), indent=4))

        vins.append(t_input)

    return vins