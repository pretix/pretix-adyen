from django import forms
from django.utils.translation import gettext_lazy as _

from pretix_adyen.payment import AdyenMethod, AdyenSettingsHolder

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
    }, {
        'method': 'giftcard__auriga',
        'provider': 'nets',
        'public_name': _('Auriga'),
        'verbose_name': _('Auriga'),
    }, {
        'method': 'giftcard__babygiftcard',
        'provider': 'intersolve',
        'public_name': _('Baby Gift Card'),
        'verbose_name': _('Baby Gift Card'),
    }, {
        'method': 'giftcard__bloemengiftcard',
        'provider': 'intersolve',
        'public_name': _('Bloemen Giftcard'),
        'verbose_name': _('Bloemen Giftcard'),
    }, {
        'method': 'giftcard__cashcomgiftcard',
        'provider': 'nets',
        'public_name': _('Cashcom'),
        'verbose_name': _('Cashcom'),
    }, {
        'method': 'giftcard__eagleeye_voucher',
        'provider': 'fis',
        'public_name': _('Eagle Eye'),
        'verbose_name': _('Eagle Eye'),
    }, {
        'method': 'giftcard__entercard',
        'provider': 'nets',
        'public_name': _('EnterCard'),
        'verbose_name': _('EnterCard'),
    }, {
        'method': 'giftcard__expertgiftcard',
        'provider': 'intersolve',
        'public_name': _('Expert Cadeaukaart'),
        'verbose_name': _('Expert Cadeaukaart'),
    }, {
        'method': 'giftcard__fashioncheque',
        'provider': 'intersolve',
        'public_name': _('Fashiocheque'),
        'verbose_name': _('Fashiocheque'),
    }, {
        'method': 'giftcard__fijncadeau',
        'provider': 'intersolve',
        'public_name': _('FijnCadeau'),
        'verbose_name': _('FijnCadeau'),
    }, {
        'method': 'giftcard__valuelink',
        'provider': 'fiserv',
        'public_name': _('Fiserv (formerly ValueLink)'),
        'verbose_name': _('Fiserv (formerly ValueLink)'),
    }, {
        'method': 'giftcard__fleuropbloemenbon',
        'provider': 'intersolve',
        'public_name': _('Fleurop Bloemenbon'),
        'verbose_name': _('Fleurop Bloemenbon'),
    }, {
        'method': 'giftcard__fonqgiftcard',
        'provider': 'intersolve',
        'public_name': _('Fonq Giftcard'),
        'verbose_name': _('Fonq Giftcard'),
    }, {
        'method': 'giftcard__gallgall',
        'provider': 'intersolve',
        'public_name': _('Gall & Gall'),
        'verbose_name': _('Gall & Gall'),
    }, {
        'method': 'giftcard__givex',
        'provider': 'givex',
        'public_name': _('Givex'),
        'verbose_name': _('Givex'),
    }, {
        'method': 'giftcard__hallmarkcard',
        'provider': 'fis',
        'public_name': _('Hallmark'),
        'verbose_name': _('Hallmark'),
    }, {
        'method': 'giftcard__igive',
        'provider': 'nets',
        'public_name': _('iGive'),
        'verbose_name': _('iGive'),
    }, {
        'method': 'giftcard__ikano',
        'provider': 'nets',
        'public_name': _('ikano'),
        'verbose_name': _('Ikano'),
    }, {
        'method': 'giftcard__kadowereld',
        'provider': 'intersolve',
        'public_name': _('Kado Werekeld'),
        'verbose_name': _('Kado Werekeld'),
    }, {
        'method': 'giftcard__kidscadeau',
        'provider': 'intersolve',
        'public_name': _('Kids Cadeau'),
        'verbose_name': _('Kids Cadeau'),
    }, {
        'method': 'giftcard__kindpas',
        'provider': 'intersolve',
        'public_name': _('Kindpas'),
        'verbose_name': _('Kindpas'),
    }, {
        'method': 'giftcard__leisurecard',
        'provider': 'intersolve',
        'public_name': _('Leisure Voucher'),
        'verbose_name': _('Leisure Voucher'),
    }, {
        'method': 'giftcard__nationalebioscoopbon',
        'provider': 'intersolve',
        'public_name': _('Nationale Bioscoopbon'),
        'verbose_name': _('Nationale Bioscoopbon'),
    }, {
        'method': 'giftcard__netscard',
        'provider': 'nets',
        'public_name': _('Netscard'),
        'verbose_name': _('Netscard'),
    }, {
        'method': 'giftcard__oberthur',
        'provider': 'nets',
        'public_name': _('Oberthur'),
        'verbose_name': _('Oberthur'),
    }, {
        'method': 'giftcard__pathegiftcard',
        'provider': 'nets',
        'public_name': _('Pathe Giftcard'),
        'verbose_name': _('Pathe Giftcard'),
    }, {
        'method': 'giftcard__payex',
        'provider': 'nets',
        'public_name': _('PayEx'),
        'verbose_name': _('PayEx'),
    }, {
        'method': 'giftcard__podiumcard',
        'provider': 'intersolve',
        'public_name': _('Podium Card'),
        'verbose_name': _('Podium Card'),
    }, {
        'method': 'giftcard__resursgiftcard',
        'provider': 'nets',
        'public_name': _('Resurs Gift Card'),
        'verbose_name': _('Resurs Gift Card'),
    }, {
        'method': 'giftcard__rotterdampas',
        'provider': 'intersolve',
        'public_name': _('Rotterdampas'),
        'verbose_name': _('Rotterdampas'),
    }, {
        'method': 'giftcard__genericgiftcard',
        'provider': 'intersolve',
        'public_name': _('Savvy'),
        'verbose_name': _('Savvy'),
    }, {
        'method': 'giftcard__schoolspullenpas',
        'provider': 'intersolve',
        'public_name': _('Schoolspullenpas'),
        'verbose_name': _('Schoolspullenpas'),
    }, {
        'method': 'giftcard__sparnord',
        'provider': 'nets',
        'public_name': _('Spar Nord'),
        'verbose_name': _('Spar Nord'),
    }, {
        'method': 'giftcard__sparebank',
        'provider': 'nets',
        'public_name': _('SpareBank'),
        'verbose_name': _('SpareBank'),
    }, {
        'method': 'giftcard__svs',
        'provider': 'svs',
        'public_name': _('Stored Value Solutions (SVS)'),
        'verbose_name': _('Stored Value Solutions (SVS)'),
    }, {
        'method': 'giftcard__universalgiftcard',
        'provider': 'nets',
        'public_name': _('Universal Gift Card'),
        'verbose_name': _('Universal Gift Card'),
    }, {
        'method': 'giftcard__vvvcadeaubon',
        'provider': 'intersolve',
        'public_name': _('VVV Cadeaubon'),
        'verbose_name': _('VVV Cadeaubon'),
    }, {
        'method': 'giftcard__vvvgiftcard',
        'provider': 'intersolve',
        'public_name': _('VVV Giftcard'),
        'verbose_name': _('VVV Giftcard'),
    }, {
        'method': 'giftcard__webshopgiftcard',
        'provider': 'intersolve',
        'public_name': _('Webshop Giftcard'),
        'verbose_name': _('Webshop Giftcard'),
    }, {
        'method': 'giftcard__winkelcheque',
        'provider': 'intersolve',
        'public_name': _('Winkel Cheque'),
        'verbose_name': _('Winkel Cheque'),
    }, {
        'method': 'giftcard__winterkledingpas',
        'provider': 'intersolve',
        'public_name': _('Winterkledingpas'),
        'verbose_name': _('Winterkledingpas'),
    }, {
        'method': 'giftcard__xponcard',
        'provider': 'nets',
        'public_name': _('XPonCard'),
        'verbose_name': _('XPonCard'),
    }, {
        'method': 'giftcard__yourgift',
        'provider': 'intersolve',
        'public_name': _('Your Gift'),
        'verbose_name': _('Your Gift'),
    }, {
        'method': 'giftcard__prosodie_illicado',
        'provider': 'prosodie',
        'public_name': _('Illicado'),
        'verbose_name': _('Illicado'),
    }, {
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
]


def get_payment_method_classes(payment_methods, baseclass, settingsholder):
    settingsholder.payment_methods_settingsholder = []
    for m in payment_methods:
        settingsholder.payment_methods_settingsholder.append(
            ('method_{}'.format(m['method']),
             forms.BooleanField(
                    label='{} {}'.format(
                        '<span class="fa fa-gift"></span>' if m['method'].split('__')[0] == 'giftcard' else '',
                        m['verbose_name']
                    ),
                    help_text=m['help_text'] if 'help_text' in m else '',
                    required=False,
            ))
        )

        if 'extra_settings_fields' in m:
            settingsholder.payment_methods_settingsholder += m['extra_settings_fields']

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
