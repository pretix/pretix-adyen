from django.urls import include, path

from .views import ReturnView, ScaView, webhook

event_patterns = [
    path('adyen/', include([
        path('return/<str:order>/<str:hash>/<int:payment>/', ReturnView.as_view(), name='return'),
        path('sca/<str:order>/<str:hash>/<int:payment>/', ScaView.as_view(), name='sca'),
    ])),
]


urlpatterns = [
    path('_adyen/webhook/', webhook, name='webhook'),
]
