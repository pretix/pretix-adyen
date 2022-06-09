from django import forms
from django.utils.translation import gettext_lazy as _

from pretix_adyen.payment import AdyenMethod, AdyenSettingsHolder, AdyenPOSRefund

# Commented-out payment methods likely still need extra /payments handling
payment_methods = [
    {
        'method': 'scheme',
        'public_name': _('Credit Card'),
        'verbose_name': _('Credit Card'),
    },
    # {
    #     'method': 'facilypay_3x',
    #     'public_name': _('3 Oney installments'),
    #     'verbose_name': _('3 Oney installments'),
    #     'help_text': _('Only available in France and Spain'),
    # }, {
    #     'method': 'facilypay_4x',
    #     'public_name': _('4 Oney installments'),
    #     'verbose_name': _('4 Oney installments'),
    #     'help_text': _('Only available in France and Spain'),
    # }, {
    #     'method': 'facilypay_6x',
    #     'public_name': _('6 Oney installments'),
    #     'verbose_name': _('6 Oney installments'),
    #     'help_text': _('Only available in Spain'),
    # }, {
    #     'method': 'facilypay_10x',
    #     'public_name': _('10 Oney installments'),
    #     'verbose_name': _('10 Oney installments'),
    #     'help_text': _('Only available in Spain'),
    # }, {
    #     'method': 'facilypay_12x',
    #     'public_name': _('12 Oney installments'),
    #     'verbose_name': _('12 Oney installments'),
    #     'help_text': _('Only available in Spain'),
    # }, {
    #     'method': 'ach',
    #     'public_name': _('ACH Direct Debit'),
    #     'verbose_name': _('Direct Debit'),
    # }, {
    #     'method': 'affirm',
    #     'public_name': _('Affirm'),
    #     'verbose_name': _('Affirm'),
    # }, {
    #     'method': 'cellulant',
    #     'public_name': _('E-Wallets & Online Banking'),
    #     'verbose_name': _('African E-Wallets & Online Banking'),
    # }, {
    #     'method': 'afterpaytouch',
    #     'public_name': _('Afterpay'),
    #     'verbose_name': _('Afterpay'),
    # },
    {
       'method': 'alipay',
       'public_name': _('AliPay'),
       'verbose_name': _('AliPay'),
    }, {
       'method': 'alipay_hk',
       'public_name': _('AliPay HK'),
       'verbose_name': _('AliPay HK'),
    },
    # {
    #     'method': 'amazonpay',
    #     'public_name': _('Amazon Pay'),
    #     'verbose_name': _('Amazon Pay'),
    # }, {
    #     'method': 'applepay',
    #     'public_name': _('Apple Pay'),
    #     'verbose_name': _('Apple Pay'),
    # }, {
    #     'method': 'atome',
    #     'public_name': _('Atome'),
    #     'verbose_name': _('Atome'),
    # }, {
    #     'method': 'directdebit_GB',
    #     'public_name': _('BACS Direct Debit'),
    #     'verbose_name': _('BACS Direct Debit'),
    # },
    {
        'method': 'bcmc',
        'public_name': _('Bancontact Card'),
        'verbose_name': _('Bancontact Card'),
    }, {
        'method': 'bcmc_mobile',
        'public_name': _('Bancontact Mobile'),
        'verbose_name': _('Bancontact Mobile'),
    },
    # {
    #     'method': 'benefit',
    #     'public_name': _('Benefit'),
    #     'verbose_name': _('Benefit'),
    # }, {
    #     'method': 'blik',
    #     'public_name': _('Blik'),
    #     'verbose_name': _('Blik'),
    # }, {
    #     'method': 'boletobancario',
    #     'public_name': _('Boleto Bancário'),
    #     'verbose_name': _('Boleto Bancário'),
    # }, {
    #     'method': 'clearpay',
    #     'public_name': _('Clearpay'),
    #     'verbose_name': _('Clearpay'),
    # },
    {
        'method': 'dana',
        'public_name': _('DANA'),
        'verbose_name': _('DANA'),
    }, {
        'method': 'eps',
        'public_name': _('EPS'),
        'verbose_name': _('EPS'),
    },
    # {
    #     'method': 'fawry',
    #     'public_name': _('Fawry'),
    #     'verbose_name': _('Fawry'),
    # },
    {
        'method': 'gcash',
        'public_name': _('GCash'),
        'verbose_name': _('GCash'),
    },
    # {
    #     'method': 'giftcard',
    #     'public_name': _('Gift card'),
    #     'verbose_name': _('Gift card'),
    # },
    {
        'method': 'giropay',
        'public_name': _('giropay'),
        'verbose_name': _('giropay'),
    },
    # {
    #     'method': 'googlepay',
    #     'public_name': _('Google Pay'),
    #     'verbose_name': _('Google Pay'),
    # }, {
    #     'method': 'gopay_wallet',
    #     'public_name': _('GoPay'),
    #     'verbose_name': _('GoPay'),
    # }, {
    #     'method': 'grabpay_SG',
    #     'public_name': _('GrabPay'),
    #     'verbose_name': _('GrabPay'),
    # },
    {
        'method': 'ideal',
        'public_name': _('iDEAL'),
        'verbose_name': _('iDEAL'),
    }, {
        'method': 'doku_alfamart',
        'public_name': _('Alfamart'),
        'verbose_name': _('Alfamart'),
        'help_text': _('Bank transfers and convenience store payments in Indonesia'),
    }, {
        'method': 'doku_permata_lite_atm',
        'public_name': _('Bank Transfer (Permata)'),
        'verbose_name': _('Bank Transfer (Permata)'),
        'help_text': _('Bank transfers and convenience store payments in Indonesia'),
    }, {
        'method': 'doku_bca_va',
        'public_name': _('BCA Bank Transfer'),
        'verbose_name': _('BCA Bank Transfer'),
        'help_text': _('Bank transfers and convenience store payments in Indonesia'),
    }, {
        'method': 'doku_bni_va',
        'public_name': _('BNI VA'),
        'verbose_name': _('BNI VA'),
        'help_text': _('Bank transfers and convenience store payments in Indonesia'),
    }, {
        'method': 'doku_bri_va',
        'public_name': _('BRI VA'),
        'verbose_name': _('BRI VA'),
        'help_text': _('Bank transfers and convenience store payments in Indonesia'),
    }, {
        'method': 'doku_cimb_va',
        'public_name': _('CIMB VA'),
        'verbose_name': _('CIMB VA'),
        'help_text': _('Bank transfers and convenience store payments in Indonesia'),
    }, {
        'method': 'doku_danamon_va',
        'public_name': _('Danamon VA'),
        'verbose_name': _('Danamon VA'),
        'help_text': _('Bank transfers and convenience store payments in Indonesia'),
    }, {
        'method': 'doku_indomaret',
        'public_name': _('Indomaret'),
        'verbose_name': _('Indomaret'),
        'help_text': _('Bank transfers and convenience store payments in Indonesia'),
    }, {
        'method': 'doku_mandiri_va',
        'public_name': _('Mandiri VA'),
        'verbose_name': _('Mandiri VA'),
        'help_text': _('Bank transfers and convenience store payments in Indonesia'),
    }, {
        'method': 'econtext_stores',
        'public_name': _('7-Eleven'),
        'verbose_name': _('7-Eleven'),
        'help_text': _('Japanese Convienience Stores'),
    }, {
        'method': 'econtext_stores',
        'public_name': _('Lawson, Mini Stop, Family Mart, Seicomart'),
        'verbose_name': _('Lawson, Mini Stop, Family Mart, Seicomart'),
        'help_text': _('Japanese Convienience Stores'),
    }, {
        'method': 'kakaopay',
        'public_name': _('KakoPay'),
        'verbose_name': _('KakoPay'),
    },
    # {
    #     'method': 'klarna',
    #     'public_name': _('Klarna'),
    #     'verbose_name': _('Klarna'),
    # }, {
    #     'method': 'knet',
    #     'public_name': _('KNET'),
    #     'verbose_name': _('KNET'),
    # }, {
    #     'method': 'MB Way',
    #     'public_name': _('mbway'),
    #     'verbose_name': _('mbway'),
    # }, {
    #     'method': 'mobilepay',
    #     'public_name': _('MobilePay'),
    #     'verbose_name': _('MobilePay'),
    # },
    {
        'method': 'momo_Pay',
        'public_name': _('MoMo Pay'),
        'verbose_name': _('MoMo Pay'),
    }, {
        'method': 'multibanco',
        'public_name': _('Multibanco'),
        'verbose_name': _('Multibanco'),
    },
    # {
    #     'method': 'naps',
    #     'public_name': _('NAPS'),
    #     'verbose_name': _('NAPS'),
    # }, {
    #     'method': 'omannet',
    #     'public_name': _('OmanNet'),
    #     'verbose_name': _('OmanNet'),
    # }, {
    #     'method': 'ebanking_FI',
    #     'public_name': _('Online Banking'),
    #     'verbose_name': _('Online Banking (Finland)'),
    # },
    {
        'method': 'billdesk_online',
        'public_name': _('Online Banking'),
        'verbose_name': _('Online Banking (India)'),
    }, {
        'method': 'molpay_ebanking_fpx_MY',
        'public_name': _('FPX Online Banking'),
        'verbose_name': _('FPX Online Banking (Malaysia)'),
    }, {
        'method': 'dotpay',
        'public_name': _('Online Banking'),
        'verbose_name': _('Online Banking (Poland)'),
    }, {
        'method': 'molpay_ebanking_TH',
        'public_name': _('Online Banking'),
        'verbose_name': _('Online Banking (Thailand)'),
    }, {
        'method': 'momo_atm',
        'public_name': _('Online Banking'),
        'verbose_name': _('Online Banking (Vietnam)'),
    }, {
        'method': 'oxxo',
        'public_name': _('OXXO'),
        'verbose_name': _('OXXO'),
    },
    # {
    #     'method': 'paybright',
    #     'public_name': _('PayBright'),
    #     'verbose_name': _('PayBright'),
    # },
    {
        'method': 'paypal',
        'public_name': _('PayPal'),
        'verbose_name': _('PayPal'),
    }, {
        'method': 'paytm',
        'public_name': _('Paytm'),
        'verbose_name': _('Paytm'),
    },
    # {
    #     'method': 'pix',
    #     'public_name': _('Pix'),
    #     'verbose_name': _('Pix'),
    # }, {
    #     'method': 'ratepay',
    #     'public_name': _('Ratepay'),
    #     'verbose_name': _('Ratepay'),
    # }, {
    #     'method': 'samsungpay',
    #     'public_name': _('Samsung Pay'),
    #     'verbose_name': _('Samsung Pay'),
    # },
    {
        'method': 'sepadirectdebit',
        'public_name': _('SEPA Direct Debit'),
        'verbose_name': _('SEPA Direct Debit'),
    }, {
        'method': 'directEbanking',
        'public_name': _('SOFORT'),
        'verbose_name': _('SOFORT'),
    }, {
        'method': 'swish',
        'public_name': _('Swish'),
        'verbose_name': _('Swish'),
    }, {
        'method': 'trustly',
        'public_name': _('Trustly'),
        'verbose_name': _('Trustly'),
    }, {
        'method': 'twint',
        'public_name': _('Twint'),
        'verbose_name': _('Twint'),
    }, {
        'method': 'vipps',
        'public_name': _('Vipps'),
        'verbose_name': _('Vipps'),
    }, {
        'method': 'billdesk_wallet',
        'public_name': _('Wallets'),
        'verbose_name': _('Wallets (India)'),
    }, {
        'method': 'wechatpayQR',
        'public_name': _('WeChat Pay'),
        'verbose_name': _('WeChat Pay QR'),
    },
    # {
    #     'method': 'zip',
    #     'public_name': _('Zip'),
    #     'verbose_name': _('Zip'),
    # }
    {
        'method': 'posrefund',
        'public_name': _('POS Refund'),
        'verbose_name': _('POS Refund'),
        'baseclass': AdyenPOSRefund
    }
]


def get_payment_method_classes(payment_methods, baseclass, settingsholder):
    settingsholder.payment_methods_settingsholder = []
    for m in payment_methods:
        if m['method'] == 'posrefund':
            continue

        settingsholder.payment_methods_settingsholder.append(
            ('method_{}'.format(m['method']),
             forms.BooleanField(
                    label=m['verbose_name'],
                    help_text=m['help_text'] if 'help_text' in m else '',
                    required=False,
            ))
        )

    return [settingsholder] + [
        type(
            f'Adyen{"".join(m["public_name"].split())}', (m['baseclass'] if 'baseclass' in m else baseclass,), {
                'identifier': 'adyen_{payment_method}'.format(
                    payment_method=m['method'],
                ),
                'verbose_name': _('{payment_method} via Adyen').format(
                    payment_method=m['verbose_name']
                ),
                'public_name': m['public_name'],
                'method': m['method'],
            })
        for m in payment_methods
    ]


payment_method_classes = get_payment_method_classes(payment_methods, AdyenMethod, AdyenSettingsHolder)
