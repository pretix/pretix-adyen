from django.conf.urls import url
from django.urls import include

from .views import ReturnView, ScaView, webhook

event_patterns = [
    url(r'^adyen/', include([
        url(r'^return/(?P<order>[^/]+)/(?P<hash>[^/]+)/(?P<payment>[0-9]+)/$', ReturnView.as_view(), name='return'),
        url(r'^sca/(?P<order>[^/]+)/(?P<hash>[^/]+)/(?P<payment>[0-9]+)/$', ScaView.as_view(), name='sca'),
    ])),
]


urlpatterns = [
    url(r'^_adyen/webhook/$', webhook, name='webhook'),
]
