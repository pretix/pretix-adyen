import json

from django.dispatch import receiver
from django.http import HttpRequest, HttpResponse
from django.template.loader import get_template
from django.urls import resolve
from django.utils.translation import gettext_lazy as _
from pretix.base.middleware import _merge_csp, _parse_csp, _render_csp
from pretix.base.signals import logentry_display, register_payment_providers
from pretix.presale.signals import html_head, process_response
from pretix_adyen.payment import AdyenSettingsHolder


@receiver(register_payment_providers, dispatch_uid="payment_adyen")
def register_payment_provider(sender, **kwargs):
    from .payment import (
        AdyenSettingsHolder, AdyenScheme, AdyenGiropay
    )

    return [AdyenSettingsHolder, AdyenScheme, AdyenGiropay]


@receiver(html_head, dispatch_uid="payment_adyen_html_head")
def html_head_presale(sender, request=None, **kwargs):
    from .payment import AdyenMethod

    provider = AdyenMethod(sender)
    url = resolve(request.path_info)
    if provider.settings.get('_enabled', as_type=bool) and ("checkout" in url.url_name or "order.pay" in url.url_name):
        template = get_template('pretix_adyen/presale_head.html')
        ctx = {
            'locale': request.LANGUAGE_CODE,
            'environment': 'test' if sender.testmode else provider.settings.prod_env,
            'originKey': provider._get_originKey('test' if provider.event.testmode else provider.settings.prod_env),
        }
        return template.render(ctx)
    else:
        return ""


@receiver(signal=process_response, dispatch_uid="payment_adyen_middleware_resp")
def signal_process_response(sender, request: HttpRequest, response: HttpResponse, **kwargs):
    provider = AdyenSettingsHolder(sender)
    url = resolve(request.path_info)

    if provider.settings.get('_enabled', as_type=bool) and ("checkout" in url.url_name or "order.pay" in url.url_name):
        if 'Content-Security-Policy' in response:
            h = _parse_csp(response['Content-Security-Policy'])
        else:
            h = {}

        sources = ['frame-src', 'style-src', 'script-src', 'img-src', 'connect-src']

        env = 'test' if sender.testmode else provider.settings.prod_env

        csps = {src: ['https://checkoutshopper-{}.adyen.com'.format(env)] for src in sources}

        # Adyen unfortunately applies styles through their script-src
        # Also, the unsafe-inline needs to specified within single quotes!
        csps['style-src'].append("'unsafe-inline'")

        _merge_csp(h, csps)

        if h:
            response['Content-Security-Policy'] = _render_csp(h)
    return response


@receiver(signal=logentry_display, dispatch_uid="adyen_logentry_display")
def pretixcontrol_logentry_display(sender, logentry, **kwargs):
    if logentry.action_type != 'pretix_adyen.adyen.event':
        return

    data = json.loads(logentry.data)
    outcome = data.get('success', None)
    reason = data.get('reason', None)

    if outcome == 'true':
        outcome = 'successful.'
    else:
        outcome = 'unsuccessful.'

    if reason:
        outcome = '{} ({})'.format(outcome, reason)

    return _('Adyen reported an event: {} {}').format(data.get('eventCode'), outcome)
