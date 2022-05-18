from django import forms
from django.utils.translation import gettext_lazy as _

from pretix_adyen.payment import AdyenMethod, AdyenSettingsHolder

payment_methods = [
    {
        'method': 'scheme',
        'public_name': _('Credit Card'),
        'verbose_name': _('Credit Card'),
    }, {
        'method': 'giropay',
        'public_name': _('giropay'),
        'verbose_name': _('giropay'),
    }, {
        'method': 'ideal',
        'public_name': _('iDEAL'),
        'verbose_name': _('iDEAL'),
    }, {
        'method': 'directEbanking',
        'public_name': _('SOFORT'),
        'verbose_name': _('SOFORT'),
    }, {
        'method': 'wechatpayQR',
        'public_name': _('WeChat Pay'),
        'verbose_name': _('WeChat Pay QR'),
    }, {
        'method': 'alipay',
        'public_name': _('AliPay'),
        'verbose_name': _('AliPay'),
    }, {
        'method': 'alipay_hk',
        'public_name': _('AliPay HK'),
        'verbose_name': _('AliPay HK'),
    },
]


def get_payment_method_classes(payment_methods, baseclass, settingsholder):
    settingsholder.payment_methods_settingsholder = []
    for m in payment_methods:
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
