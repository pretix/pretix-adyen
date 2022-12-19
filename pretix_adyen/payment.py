from typing import Any, Dict, Union

import Adyen
import hashlib
import json
import logging
import re
from Adyen import AdyenError
from collections import OrderedDict
from decimal import Decimal
from django import forms
from django.contrib import messages
from django.core.cache import cache
from django.http import HttpRequest
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from pretix import __version__, settings
from pretix.base.decimal import round_decimal
from pretix.base.models import (
    Event, InvoiceAddress, Order, OrderPayment, OrderRefund,
)
from pretix.base.payment import BasePaymentProvider, PaymentException
from pretix.base.settings import SettingsSandbox
from pretix.helpers.http import get_client_ip
from pretix.helpers.urls import build_absolute_uri as build_global_uri
from pretix.multidomain.urlreverse import build_absolute_uri, eventreverse
from pretix.presale.views.cart import cart_session

from .apps import PluginApp

logger = logging.getLogger('pretix_adyen')


class AdyenSettingsHolder(BasePaymentProvider):
    identifier = 'adyen_settings'
    verbose_name = _('Adyen')
    payment_methods_settingsholder = []
    is_enabled = False
    is_meta = True

    def __init__(self, event: Event):
        super().__init__(event)
        self.settings = SettingsSandbox('payment', 'adyen', event)

    def settings_content_render(self, request):
        template = get_template('pretix_adyen/control_settings.html')
        ctx = {
            'webhook': build_global_uri('plugins:pretix_adyen:webhook'),
            'partnerid': 'e7e675cd-00b4-4ee5-8ebd-2e13bdd5cc78&v=aTrVy8cj'
        }
        return template.render(ctx)

    @property
    def settings_form_fields(self):
        fields = [
            ('test_merchant_account',
             forms.CharField(
                 label=_('Test Merchant Account'),
                 required=False,
             )),
            ('test_api_key',
             forms.CharField(
                 label=_('Test API Key'),
                 required=False,
                 help_text=_('Please refer to the documentation '
                             '<a href="https://docs.adyen.com/user-management/how-to-get-the-api-key">here</a> on how '
                             'to obtain your API-key.')
             )),
            ('test_hmac_key',
             forms.CharField(
                 label=_('Test HMAC Key'),
                 required=False,
                 help_text=_('Please refer to the documentation '
                             '<a href="https://docs.adyen.com/development-resources/notifications/verify-hmac-signatures#enable-hmac-signatures">here</a> '
                             'on how to obtain your HMAC key.')
             )),
            ('test_client_key',
             forms.CharField(
                 label=_('Test Client Key'),
                 required=False,
                 help_text=_('Please refer to the documentation '
                             '<a href="https://docs.adyen.com/development-resources/client-side-authentication/migrate-from-origin-key-to-client-key">here</a> '
                             'on how to obtain your Client key.')
             )),
            ('prod_merchant_account',
             forms.CharField(
                 label=_('Production Merchant Account'),
                 required=False,
             )),
            ('prod_api_key',
             forms.CharField(
                 label=_('Production API Key'),
                 required=False,
                 help_text=_('Please refer to the documentation '
                             '<a href="https://docs.adyen.com/user-management/how-to-get-the-api-key">here</a> on how '
                             'to obtain your API-key.')
             )),
            ('prod_hmac_key',
             forms.CharField(
                 label=_('Production HMAC Key'),
                 required=False,
                 help_text=_('Please refer to the documentation '
                             '<a href="https://docs.adyen.com/development-resources/notifications/verify-hmac-signatures#enable-hmac-signatures">here</a> '
                             'on how to obtain your HMAC key.')
             )),
            ('prod_client_key',
             forms.CharField(
                 label=_('Production Client Key'),
                 required=False,
                 help_text=_('Please refer to the documentation '
                             '<a href="https://docs.adyen.com/development-resources/client-side-authentication/migrate-from-origin-key-to-client-key">here</a> '
                             'on how to obtain your Client key.')
             )),
            ('prod_prefix',
             forms.CharField(
                 label=_('Production Endpoint Prefix'),
                 required=False,
                 help_text=_('Please refer to the documentation '
                             '<a href="https://docs.adyen.com/development-resources/live-endpoints">here</a> '
                             'on how to identify the Production Endpoint Prefix.<br />'
                             'If your production checkout endpoint is '
                             'https://[random]-[company name]-checkout-live.adyenpayments.com/, please use '
                             '<i>[random]-[company name]</i> as the prefix.')
             )),
            ('prod_env',
             forms.ChoiceField(
                 label=_('Production Environment'),
                 required=True,
                 choices=[
                     ('live', 'Europe'),
                     ('live-au', 'Australia'),
                     ('live-us', 'US')
                 ],
                 help_text=_('Please select the Adyen server closest to you.')
             )),
        ]
        d = OrderedDict(
            fields + self.payment_methods_settingsholder + list(super().settings_form_fields.items())
        )
        d.move_to_end('_enabled', last=False)
        return d


class AdyenMethod(BasePaymentProvider):
    identifier = ''
    method = ''

    def __init__(self, event: Event):
        super().__init__(event)
        self.settings = SettingsSandbox('payment', 'adyen', event)

    @property
    def test_mode_message(self):
        if self.settings.test_merchant_account and self.settings.test_api_key:
            return mark_safe(
                _('The Adyen plugin is operating in test mode. You can use one of <a {args}>many test '
                  'cards</a> to perform a transaction. No money will actually be transferred.').format(
                    args='href="https://docs.adyen.com/development-resources/test-cards/test-card-numbers" '
                         'target="_blank"'
                )
            )
        return None

    @property
    def settings_form_fields(self):
        return {}

    @property
    def is_enabled(self) -> bool:
        return self.settings.get('_enabled', as_type=bool) and self.settings.get('method_{}'.format(self.method),
                                                                                 as_type=bool)

    def payment_refund_supported(self, payment: OrderPayment) -> bool:
        return True

    def payment_partial_refund_supported(self, payment: OrderPayment) -> bool:
        return True

    def payment_prepare(self, request, payment):
        return self.checkout_prepare(request, None)

    def checkout_prepare(self, request: HttpRequest, cart: Dict[str, Any]) -> Union[bool, str]:
        payment_method_data = request.POST.get('{}-{}'.format('adyen_paymentMethodData', self.method), '')
        request.session['{}-{}'.format('payment_adyen_paymentMethodData', self.method)] = payment_method_data

        if payment_method_data == '':
            messages.warning(request, _('You may need to enable JavaScript for Adyen payments.'))
            return False
        return True

    def payment_is_valid_session(self, request):
        return request.session.get('{}-{}'.format('payment_adyen_paymentMethodData', self.method), '') != ''

    def _amount_to_decimal(self, cents):
        places = settings.CURRENCY_PLACES.get(self.event.currency, 2)
        return round_decimal(float(cents) / (10 ** places), self.event.currency)

    def _decimal_to_int(self, amount):
        places = settings.CURRENCY_PLACES.get(self.event.currency, 2)
        return int(amount * 10 ** places)

    def _get_amount(self, payment):
        return self._decimal_to_int(payment.amount)

    def statement_descriptor(self, payment, length=22):
        return '{event}-{code} {eventname}'.format(
            event=self.event.slug.upper(),
            code=payment.order.code,
            eventname=re.sub('[^a-zA-Z0-9 ]', '', str(self.event.name))
        )[:length]

    @property
    def api_kwargs(self):
        kwargs = {
            'merchantAccount': self.settings.test_merchant_account if self.event.testmode
            else self.settings.prod_merchant_account,
            'applicationInfo': {
                'merchantApplication': {
                    'name': 'pretix-adyen',
                    'version': PluginApp.PretixPluginMeta.version,
                },
                'externalPlatform': {
                    'name': 'pretix',
                    'version': __version__,
                    'integrator': settings.PRETIX_INSTANCE_NAME,
                }
            }
        }

        return kwargs

    def _init_api(self, env=None):
        self.adyen = Adyen.Adyen()
        self.adyen.client.xapikey = self.settings.test_api_key if self.event.testmode else self.settings.prod_api_key
        # API-calls go only to -live in prod - not to -live-au or -live-us like in the frontend.
        self.adyen.client.platform = env if env else 'test' if self.event.testmode else 'live'
        self.adyen.client.live_endpoint_prefix = self.settings.prod_prefix

    def checkout_confirm_render(self, request) -> str:
        template = get_template('pretix_adyen/checkout_payment_confirm.html')
        ctx = {'request': request, 'event': self.event, 'settings': self.settings, 'provider': self}
        return template.render(ctx)

    def payment_can_retry(self, payment):
        return self._is_still_available(order=payment.order)

    def _charge_source(self, request, source, payment):
        pass

    def payment_pending_render(self, request, payment) -> str:
        if payment.info:
            payment_info = json.loads(payment.info)
        else:
            payment_info = None
        template = get_template('pretix_adyen/pending.html')
        ctx = {
            'request': request,
            'event': self.event,
            'settings': self.settings,
            'provider': self,
            'order': payment.order,
            'payment': payment,
            'payment_info': payment_info,
            'payment_hash': hashlib.sha1(payment.order.secret.lower().encode()).hexdigest()
        }
        return template.render(ctx)

    def api_payment_details(self, payment: OrderPayment):
        return {
            "id": payment.info_data.get("id", None),
            "payment_method": payment.info_data.get("payment_method", None)
        }

    def payment_control_render(self, request, payment) -> str:
        if payment.info:
            payment_info = json.loads(payment.info)
            if 'amount' in payment_info:
                payment_info['amount']['value'] /= 10 ** settings.CURRENCY_PLACES.get(self.event.currency, 2)
        else:
            payment_info = None
        template = get_template('pretix_adyen/control.html')
        ctx = {
            'request': request,
            'event': self.event,
            'settings': self.settings,
            'payment_info': payment_info,
            'payment': payment,
            'method': self.method,
            'provider': self,
        }
        return template.render(ctx)

    def refund_control_render(self, request, payment) -> str:
        if payment.info:
            payment_info = json.loads(payment.info)
            if 'amount' in payment_info:
                payment_info['amount']['value'] /= 10 ** settings.CURRENCY_PLACES.get(self.event.currency, 2)
        else:
            payment_info = None
        template = get_template('pretix_adyen/control.html')
        ctx = {
            'request': request,
            'event': self.event,
            'settings': self.settings,
            'payment_info': payment_info,
            'payment': payment,
            'method': self.method,
            'provider': self,
        }
        return template.render(ctx)

    def execute_refund(self, refund: OrderRefund):
        self._init_api()

        payment_info = refund.payment.info_data

        if not payment_info:
            raise PaymentException(_('No payment information found.'))

        rqdata = {
            'modificationAmount': {
                'value': self._get_amount(refund),
                'currency': self.event.currency,
            },
            'originalReference': payment_info['pspReference'],
            'merchantOrderReference': '{event}-{code}'.format(event=self.event.slug.upper(), code=refund.order.code),
            'reference': '{event}-{code}-R-{payment}'.format(event=self.event.slug.upper(), code=refund.order.code, payment=refund.local_id),
            'shopperStatement': self.statement_descriptor(refund),
            'captureDelayHours': 0,
            **self.api_kwargs
        }

        try:
            result = self.adyen.payment.refund(rqdata)
        except AdyenError as e:
            logger.exception('AdyenError: %s' % str(e))
            return

        refund.info = json.dumps(result.message)
        refund.state = OrderRefund.REFUND_STATE_TRANSIT
        refund.save()
        refund.order.log_action('pretix.event.order.refund.created', {
            'local_id': refund.local_id,
            'provider': refund.provider,
        })

    def execute_payment(self, request: HttpRequest, payment: OrderPayment):
        self._init_api()
        try:
            payment_method_data = json.loads(request.session['{}-{}'.format('payment_adyen_paymentMethodData', self.method)])

            rqdata = {
                'amount': {
                    'value': self._get_amount(payment),
                    'currency': self.event.currency,
                },
                'merchantOrderReference': '{event}-{code}'.format(event=self.event.slug.upper(), code=payment.order.code),
                'reference': '{event}-{code}-P-{payment}'.format(event=self.event.slug.upper(), code=payment.order.code, payment=payment.local_id),
                'shopperStatement': self.statement_descriptor(payment),
                'paymentMethod': payment_method_data['paymentMethod'],
                'returnUrl': build_absolute_uri(self.event, 'plugins:pretix_adyen:return', kwargs={
                    'order': payment.order.code,
                    'payment': payment.pk,
                    'hash': hashlib.sha1(payment.order.secret.lower().encode()).hexdigest(),
                }),
                'channel': 'Web',
                'origin': settings.SITE_URL,
                'captureDelayHours': 0,
                'shopperInteraction': 'Ecommerce',
                **self.api_kwargs
            }

            if self.method == "scheme":
                rqdata['additionalData'] = {
                    'allow3DS2': 'true'
                }
                rqdata['browserInfo'] = payment_method_data['browserInfo']
                rqdata['shopperIP'] = get_client_ip(request)

            try:
                result = self.adyen.checkout.payments(rqdata)
            except AdyenError as e:
                logger.exception('Adyen error: %s' % str(e))
                payment.state = OrderPayment.PAYMENT_STATE_FAILED
                payment.info = json.dumps({
                    'refusalReason': json.loads(e.raw_response or {}).get('message', '')
                })
                payment.save()
                payment.order.log_action('pretix.event.order.payment.failed', {
                    'local_id': payment.local_id,
                    'provider': payment.provider,
                    'message': json.loads(e.raw_response or {}).get('message', '')
                })
                raise PaymentException(_('We had trouble communicating with Adyen. Please try again and get in touch '
                                         'with us if this problem persists.'))

            if 'action' in result.message:
                payment.info = json.dumps(result.message)
                payment.state = OrderPayment.PAYMENT_STATE_CREATED
                payment.save()
                payment.order.log_action('pretix.event.order.payment.started', {
                    'local_id': payment.local_id,
                    'provider': payment.provider
                })
                return build_absolute_uri(self.event, 'plugins:pretix_adyen:sca', kwargs={
                    'order': payment.order.code,
                    'payment': payment.pk,
                    'hash': hashlib.sha1(payment.order.secret.lower().encode()).hexdigest(),
                })

            else:
                payment.info = json.dumps(result.message)
                payment.save()
                self._handle_resultcode(payment)
        finally:
            del request.session['{}-{}'.format('payment_adyen_paymentMethodData', self.method)]

    def _handle_resultcode(self, payment: OrderPayment):
        payment_info = json.loads(payment.info)

        if payment_info['resultCode'] in [
            'AuthenticationFinished',
            'ChallengeShopper',
            'IdentifyShopper',
            'PresentToShopper',
            'Received',
            'RedirectShopper',
        ]:
            # At this point, the payment has already been created - so no need to set the status or log it again
            # payment.state = OrderPayment.PAYMENT_STATE_CREATED
            pass
        elif payment_info['resultCode'] in ['Error', 'Refused']:
            payment.state = OrderPayment.PAYMENT_STATE_FAILED
            payment.save(update_fields=['state'])
            payment.order.log_action('pretix.event.order.payment.failed', {
                'local_id': payment.local_id,
                'provider': payment.provider
            })
        elif payment_info['resultCode'] == 'Cancelled':
            payment.state = OrderPayment.PAYMENT_STATE_CANCELED
            payment.save(update_fields=['state'])
            payment.order.log_action('pretix.event.order.payment.canceled', {
                'local_id': payment.local_id,
                'provider': payment.provider
            })
        elif payment_info['resultCode'] == 'Pending':
            payment.state = OrderPayment.PAYMENT_STATE_PENDING
            payment.save(update_fields=['state'])
            # Nothing we can log here...
        elif payment_info['resultCode'] == 'Authorised':
            payment.confirm()

        return payment.state

    def _handle_action(self, request: HttpRequest, payment: OrderPayment, statedata=None, payload=None, redirectResult=None, md=None, pares=None):
        self._init_api()

        payment_info = json.loads(payment.info)

        try:
            if statedata:
                result = self.adyen.checkout.payments_details(json.loads(statedata))
            elif payload:
                result = self.adyen.checkout.payments_details({
                    'paymentData': payment_info['paymentData'],
                    'details': {
                        'payload': payload,
                    },
                })
            elif redirectResult:
                result = self.adyen.checkout.payments_details({
                    'details': {
                        'redirectResult': redirectResult,
                    },
                })
            elif md and pares:
                result = self.adyen.checkout.payments_details({
                    'paymentData': payment_info['paymentData'],
                    'details': {
                        'MD': md,
                        'PaRes': pares,
                    },
                })
            else:
                messages.error(request, _('Sorry, there was an error in the payment process.'))
                return eventreverse(self.event, 'presale:event.order', kwargs={
                    'order': payment.order.code,
                    'secret': payment.order.secret
                })
        except AdyenError as e:
            logger.exception('AdyenError: %s' % str(e))
            messages.error(request, _('Sorry, there was an error in the payment process.'))
            return eventreverse(self.event, 'presale:event.order', kwargs={
                'order': payment.order.code,
                'secret': payment.order.secret
            })

        payment.info = json.dumps(result.message)
        payment.save(update_fields=['info'])

        if 'action' in result.message:
            return build_absolute_uri(self.event, 'plugins:pretix_adyen:sca', kwargs={
                'order': payment.order.code,
                'payment': payment.pk,
                'hash': hashlib.sha1(payment.order.secret.lower().encode()).hexdigest(),
            })
        else:
            state = self._handle_resultcode(payment)
            return eventreverse(self.event, 'presale:event.order', kwargs={
                'order': payment.order.code,
                'secret': payment.order.secret
            }) + ('?paid=yes' if state in [OrderPayment.PAYMENT_STATE_CONFIRMED, OrderPayment.PAYMENT_STATE_PENDING] else '')

    def is_allowed(self, request: HttpRequest, total: Decimal = None) -> bool:
        global_allowed = super().is_allowed(request, total)

        if request.event.testmode:
            local_allowed = request.event.settings.payment_adyen_test_merchant_account \
                and request.event.settings.payment_adyen_test_api_key \
                and request.event.settings.payment_adyen_test_hmac_key \
                and request.event.settings.payment_adyen_test_client_key
        else:
            local_allowed = request.event.settings.payment_adyen_prod_merchant_account \
                and request.event.settings.payment_adyen_prod_api_key \
                and request.event.settings.payment_adyen_prod_hmac_key \
                and request.event.settings.payment_adyen_prod_client_key \
                and request.event.settings.payment_adyen_prod_prefix

        if global_allowed and local_allowed:
            self._init_api()

            def get_invoice_address():
                if not hasattr(request, '_checkout_flow_invoice_address'):
                    cs = cart_session(request)
                    iapk = cs.get('invoice_address')
                    if not iapk:
                        request._checkout_flow_invoice_address = InvoiceAddress()
                    else:
                        try:
                            request._checkout_flow_invoice_address = InvoiceAddress.objects.get(pk=iapk,
                                                                                                order__isnull=True)
                        except InvoiceAddress.DoesNotExist:
                            request._checkout_flow_invoice_address = InvoiceAddress()
                return request._checkout_flow_invoice_address

            rqdata = {
                'amount': {
                    'value': self._decimal_to_int(total),
                    'currency': self.event.currency
                },
                'channel': 'Web',
                **self.api_kwargs
            }

            ia = get_invoice_address()
            if ia.country:
                rqdata['countryCode'] = str(ia.country)

            self.payment_methods_hash = self._get_payment_methods_hash(rqdata)
            self._get_payment_methods(rqdata)
            return self._is_allowed_payment_method()

        return False

    def order_change_allowed(self, order: Order) -> bool:
        global_allowed = super().order_change_allowed(order)

        if order.event.testmode:
            local_allowed = order.event.settings.payment_adyen_test_merchant_account \
                and order.event.settings.payment_adyen_test_api_key \
                and order.event.settings.payment_adyen_test_hmac_key \
                and order.event.settings.payment_adyen_test_client_key
        else:
            local_allowed = order.event.settings.payment_adyen_prod_merchant_account \
                and order.event.settings.payment_adyen_prod_api_key \
                and order.event.settings.payment_adyen_prod_hmac_key \
                and order.event.settings.payment_adyen_prod_client_key \
                and order.event.settings.payment_adyen_prod_prefix

        if global_allowed and local_allowed:
            self._init_api()

            rqdata = {
                'amount': {
                    'value': self._decimal_to_int(order.total),
                    'currency': self.event.currency
                },
                'channel': 'Web',
                **self.api_kwargs
            }

            if order.invoice_address.country:
                rqdata['countryCode'] = str(order.invoice_address.country)

            self.payment_methods_hash = self._get_payment_methods_hash(rqdata)
            self._get_payment_methods(rqdata)
            return self._is_allowed_payment_method()
        return False

    def _get_payment_methods_hash(self, rqdata):
        return hashlib.sha256(json.dumps(rqdata).encode()).hexdigest()

    def _get_payment_methods(self, rqdata):
        checksum = self._get_payment_methods_hash(rqdata)
        payment_methods = cache.get(f'adyen_payment_methods_{checksum}')
        if not payment_methods:
            try:
                response = self.adyen.checkout.payment_methods(rqdata)
                data = json.dumps(response.message)
                cache.set(
                    f'adyen_payment_methods_{checksum}',
                    data,
                    60
                )
                payment_methods = data
            except AdyenError as e:
                logger.exception('AdyenError: %s' % str(e))
                return False

        return payment_methods

    def _is_allowed_payment_method(self):
        method_brand = self.method.split("__")
        method = method_brand[0]
        brand = method_brand[-1]

        # Some methods take the form of method__brand such as giftcard__svs.
        # In this case, we do not only need to check if the method is allowed (there can be one or more
        # giftcard-methods returned by Adyen), but also if the specific brand is mentioned.
        if any(
                d.get('type', None) == method and d.get('brand', method) == brand for d in json.loads(
                    cache.get(f'adyen_payment_methods_{self.payment_methods_hash}')
                )['paymentMethods']
        ):
            return True

        return False

    def payment_form_render(self, request, total) -> str:
        template = get_template('pretix_adyen/checkout_payment_form.html')

        request.session['adyen_payment_methods_hash'] = self.payment_methods_hash

        ctx = {
            'method': self.method,
        }

        return template.render(ctx)
