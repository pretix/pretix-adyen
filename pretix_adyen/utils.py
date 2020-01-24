from __future__ import absolute_import, division, unicode_literals

import base64
import binascii
import hashlib
import hmac


def generate_hpp_sig(dict_object, hmac_key):
    if not isinstance(dict_object, dict):
        raise ValueError("Must Provide dictionary object")

    def escape_val(val):
        if isinstance(val, int):
            return str(val)
        elif isinstance(val, str):
            return val.replace('\\', '\\\\').replace(':', '\\:')
        return val

    hmac_key = binascii.a2b_hex(hmac_key)

    signing_string = ':'.join([
        escape_val(dict_object.get('pspReference', '')),
        escape_val(dict_object.get('originalReference', '')),
        escape_val(dict_object.get('merchantAccountCode', '')),
        escape_val(dict_object.get('merchantReference', '')),
        escape_val(dict_object.get('amount', {}).get('value', '')),
        escape_val(dict_object.get('amount', {}).get('currency', '')),
        escape_val(dict_object.get('eventCode', '')),
        escape_val(dict_object.get('success', '')),
    ])

    hm = hmac.new(hmac_key, signing_string.encode('utf-8'), hashlib.sha256)
    return base64.b64encode(hm.digest())


def is_valid_hmac(dict_object, hmac_key):
    if 'additionalData' in dict_object:
        if dict_object['additionalData']['hmacSignature'] == "":
            raise ValueError("Must Provide hmacSignature in additionalData")
        else:
            expected_sign = dict_object['additionalData']['hmacSignature']
            del dict_object['additionalData']
            merchant_sign = generate_hpp_sig(dict_object, hmac_key)
            merchant_sign_str = merchant_sign.decode("utf-8")
            return merchant_sign_str == expected_sign
