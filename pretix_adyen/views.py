import hashlib
import json
import logging

from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_scopes import scopes_disabled
from pretix.base.models import Order, OrderPayment, OrderRefund
from pretix.multidomain.urlreverse import eventreverse

from .utils import is_valid_hmac

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
@scopes_disabled()
def webhook(request, *args, **kwargs):
    event_json = json.loads(request.body.decode('utf-8'))

    if 'notificationItems' in event_json:
        for notification_item in event_json['notificationItems']:
            notification_item = notification_item['NotificationRequestItem']
            reference = notification_item['merchantReference'].rsplit('-', 3)
            try:
                if reference[2] == 'R':
                    refund = OrderRefund.objects.get(
                        order__event__slug__iexact=reference[0],
                        order__code=reference[1],
                        local_id=reference[3]
                    )

                    if event_json['live'] == 'true':
                        hmac = refund.order.event.settings.payment_adyen_prod_hmac_key
                    else:
                        hmac = refund.order.event.settings.payment_adyen_test_hmac_key

                    if is_valid_hmac(notification_item, hmac):
                        refund.order.log_action('pretix_adyen.adyen.event', data=notification_item)
                        refund.info = json.dumps(notification_item)
                        refund.save(update_fields=['info'])

                        if notification_item['success'] == 'true':  # Yes, seriously...
                            refund.done()
                        else:
                            refund.state = OrderRefund.REFUND_STATE_FAILED
                            refund.save(update_fields=['state'])
                            refund.order.log_action('pretix.event.order.refund.failed', {
                                'local_id': refund.local_id,
                                'provider': refund.provider
                            })
                    else:
                        logger.exception('Webhook error: Could not verify HMAC. {}'.format(notification_item))
                elif reference[2] == 'P':
                    payment = OrderPayment.objects.get(
                        order__event__slug__iexact=reference[0],
                        order__code=reference[1],
                        local_id=reference[3]
                    )

                    if event_json['live'] == 'true':
                        hmac = payment.order.event.settings.payment_adyen_prod_hmac_key
                    else:
                        hmac = payment.order.event.settings.payment_adyen_test_hmac_key

                    if is_valid_hmac(notification_item, hmac):
                        payment.order.log_action('pretix_adyen.adyen.event', data=notification_item)
                        payment.info = json.dumps(notification_item)
                        payment.save(update_fields=['info'])

                        if notification_item['success'] == 'true':  # Yes, seriously...
                            payment.confirm()
                        else:
                            payment.state = OrderPayment.PAYMENT_STATE_FAILED
                            payment.save(update_fields=['state'])
                            payment.order.log_action('pretix.event.order.payment.failed', {
                                'local_id': payment.local_id,
                                'provider': payment.provider
                            })
                    else:
                        logger.exception('Webhook error: Could not verify HMAC. {}'.format(notification_item))
                else:
                    # logger.info('Ignoring webhook event. {}'.format(notification_item))
                    pass
            except (IndexError, OrderRefund.DoesNotExist, OrderPayment.DoesNotExist):
                # logger.info('Ignoring webhook - could not match order. {}'.format(notification_item))
                pass

    return HttpResponse('[accepted]', status=200)


class AdyenOrderView:
    def dispatch(self, request, *args, **kwargs):
        try:
            self.order = request.event.orders.get(code=kwargs['order'])
            if hashlib.sha1(self.order.secret.lower().encode()).hexdigest() != kwargs['hash'].lower():
                raise Http404('')
        except Order.DoesNotExist:
            # Do a hash comparison as well to harden timing attacks
            if 'abcdefghijklmnopq'.lower() == hashlib.sha1('abcdefghijklmnopq'.encode()).hexdigest():
                raise Http404('')
            else:
                raise Http404('')
        return super().dispatch(request, *args, **kwargs)

    @cached_property
    def payment(self):
        return get_object_or_404(self.order.payments,
                                 pk=self.kwargs['payment'],
                                 provider__startswith='adyen')

    @cached_property
    def pprov(self):
        return self.request.event.get_payment_providers()[self.payment.provider]

    def _redirect_to_order(self):
        return redirect(eventreverse(self.request.event, 'presale:event.order', kwargs={
            'order': self.order.code,
            'secret': self.order.secret
        }) + ('?paid=yes' if self.order.status == Order.STATUS_PAID else ''))


@method_decorator(xframe_options_exempt, 'dispatch')
class ScaView(AdyenOrderView, View):

    def get(self, request, *args, **kwargs):
        prov = self.pprov

        if self.payment.state in (OrderPayment.PAYMENT_STATE_CONFIRMED,
                                  OrderPayment.PAYMENT_STATE_CANCELED,
                                  OrderPayment.PAYMENT_STATE_FAILED):
            return self._redirect_to_order()

        payment_info = json.loads(self.payment.info)

        if 'action' in payment_info:
            ctx = {
                'order': self.order,
                'locale': self.order.locale,
                'environment': 'test' if self.order.testmode else prov.settings.prod_env,
                'originKey': prov._get_originKey('test' if self.order.testmode else prov.settings.prod_env),
                'action': json.dumps(payment_info['action'])
            }

            r = render(request, 'pretix_adyen/sca.html', ctx)
            r._csp_ignore = True
            return r
        else:
            return self._redirect_to_order()

    def post(self, request, *args, **kwargs):
        prov = self.pprov

        if self.payment.state in (OrderPayment.PAYMENT_STATE_CONFIRMED,
                                  OrderPayment.PAYMENT_STATE_CANCELED,
                                  OrderPayment.PAYMENT_STATE_FAILED):
            return self._redirect_to_order()

        if request.POST.get('adyen_stateData'):
            return redirect(prov._handle_action(request, self.payment, statedata=request.POST.get('adyen_stateData')))

        messages.error(self.request, _('Sorry, there was an error in the payment process.'))
        return self._redirect_to_order()


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(xframe_options_exempt, 'dispatch')
class ReturnView(AdyenOrderView, View):
    def get(self, request, *args, **kwargs):
        prov = self.pprov

        if self.payment.state in (OrderPayment.PAYMENT_STATE_CONFIRMED,
                                  OrderPayment.PAYMENT_STATE_CANCELED,
                                  OrderPayment.PAYMENT_STATE_FAILED):
            return self._redirect_to_order()

        if request.GET.get('payload'):
            return redirect(prov._handle_action(request, self.payment, payload=request.GET.get('payload')))

        messages.error(self.request, _('Sorry, there was an error in the payment process.'))
        return self._redirect_to_order()

    def post(self, request, *args, **kwargs):
        prov = self.pprov

        if self.payment.state in (OrderPayment.PAYMENT_STATE_CONFIRMED,
                                  OrderPayment.PAYMENT_STATE_CANCELED,
                                  OrderPayment.PAYMENT_STATE_FAILED):
            return self._redirect_to_order()

        if request.POST.get('MD') and request.POST.get('PaRes'):
            return redirect(
                prov._handle_action(request, self.payment, md=request.POST.get('MD'), pares=request.POST.get('PaRes'))
            )

        messages.error(self.request, _('Sorry, there was an error in the payment process.'))
        return self._redirect_to_order()
