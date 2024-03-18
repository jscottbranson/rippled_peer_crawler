import base64
import hashlib

def to_base58(v):
    __b58chars = 'rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz'
    __b58base = len(__b58chars)

    long_value = 0
    for (i, c) in enumerate(v[::-1]):
        long_value += (256 ** i) * c

    result = ''
    while long_value >= __b58base:
        div, mod = divmod(long_value, __b58base)
        result = __b58chars[mod] + result
        long_value = div
    result = __b58chars[long_value] + result

    nPad = 0
    for c in v:
        if c == 0:
            nPad += 1
        else:
            break

    return (__b58chars[0] * nPad) + result

def normalize_public_key(public_key):
    try:
        x = base64.b64decode(public_key)
        vdata = bytes([28]) + x
        h = hashlib.sha256(hashlib.sha256(vdata).digest()).digest()
        key = vdata + h[0:4]
        return to_base58(key)
    except Exception as e:
        print(f"Error normalizing public key: {e}")
        return public_key

print(normalize_public_key("At2o0P4ZW4rpdFurtpo3Eh1ROva+Xm6U0EOmf/5348t4"))
