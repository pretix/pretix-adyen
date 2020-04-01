import hashlib
import json
import logging
import re
from collections import OrderedDict
from decimal import Decimal
from typing import Any, Dict, Union

import Adyen
from Adyen import AdyenError
from django import forms
from django.contrib import messages
from django.http import HttpRequest
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from pretix import __version__, settings
from pretix.base.decimal import round_decimal
from pretix.base.models import Event, InvoiceAddress, OrderPayment, OrderRefund
from pretix.base.payment import BasePaymentProvider, PaymentException
from pretix.base.settings import SettingsSandbox
from pretix.helpers.urls import build_absolute_uri as build_global_uri
from pretix.multidomain.urlreverse import build_absolute_uri, eventreverse
from pretix.presale.views.cart import cart_session

from . import PluginApp

logger = logging.getLogger('pretix_adyen')


class AdyenSettingsHolder(BasePaymentProvider):
    identifier = 'adyen_settings'
    verbose_name = _('Adyen')
    is_enabled = False
    is_meta = True

    def __init__(self, event: Event):
        super().__init__(event)
        self.settings = SettingsSandbox('payment', 'adyen', event)

    def settings_content_render(self, request):
        return "<div class='alert alert-info'>%s<br /><code>%s</code></div>" % (
            _('Please configure a <a href="https://docs.adyen.com/development-resources/notifications">Notification '
              'Webhook</a> to the following endpoint in order to automatically cancel orders when charges are refunded '
              'externally and to process asynchronous payment methods like SOFORT.'),
            build_global_uri('plugins:pretix_adyen:webhook')
        )

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
            fields + [
                ('method_scheme',
                 forms.BooleanField(
                     label=_('Credit card payments'),
                     required=False,
                 )),
                ('method_giropay',
                 forms.BooleanField(
                     label=_('giropay'),
                     required=False,
                 )),
            ] + list(super().settings_form_fields.items())
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
        self.adyen = Adyen.Adyen(
            app_name='pretix',
            xapikey=self.settings.test_api_key if self.event.testmode else self.settings.prod_api_key,
            # API-calls go only to -live in prod - not to -live-au or -live-us like in the frontend.
            platform=env if env else 'test' if self.event.testmode else 'live',
            live_endpoint_prefix=self.settings.prod_prefix
        )

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

    def _get_originKey(self, env):
        originkeyenv = 'originkey_{}'.format(env)

        if not self.settings[originkeyenv]:
            if not (self.settings.test_api_key if self.event.testmode else self.settings.prod_api_key):
                return

            self._init_api(env)

            origin_domains = {
                'originDomains': [
                    settings.SITE_URL
                ]
            }

            try:
                result = self.adyen.checkout.origin_keys(origin_domains)
                self.settings[originkeyenv] = result.message['originKeys'][settings.SITE_URL]
            except AdyenError as e:
                logger.exception('AdyenError: %s' % str(e))

        return self.settings.get(originkeyenv, '')

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
                # Since we do not have the IP-address of the customer, we cannot pass rqdata['shopperIP'].

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

    def _handle_action(self, request: HttpRequest, payment: OrderPayment, statedata=None, payload=None, md=None, pares=None):
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
                and request.event.settings.payment_adyen_test_hmac_key
        else:
            local_allowed = request.event.settings.payment_adyen_prod_merchant_account \
                and request.event.settings.payment_adyen_prod_api_key \
                and request.event.settings.payment_adyen_prod_hmac_key \
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

            try:
                response = self.adyen.checkout.payment_methods(rqdata)
                if any(d.get('type', None) == self.method for d in response.message['paymentMethods']):
                    self.payment_methods = json.dumps(response.message)
                    return True
            except AdyenError as e:
                logger.exception('AdyenError: %s' % str(e))
                return False

        return False

    def payment_form_render(self, request, total) -> str:
        template = get_template('pretix_adyen/checkout_payment_form.html')

        if not hasattr(self, 'payment_methods'):
            self.is_allowed(request, total)

        ctx = {
            'method': self.method,
            'paymentMethodsResponse': self.payment_methods,
        }

        return template.render(ctx)


class AdyenScheme(AdyenMethod):
    identifier = 'adyen_scheme'
    verbose_name = _('Credit card via Adyen')
    public_name = _('Credit card')
    method = 'scheme'


class AdyenGiropay(AdyenMethod):
    identifier = 'adyen_giropay'
    verbose_name = _('giropay via Adyen')
    public_name = _('giropay')
    method = 'giropay'
