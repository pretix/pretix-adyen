from django.utils.translation import gettext_lazy

try:
    from pretix.base.plugins import PluginConfig
except ImportError:
    raise RuntimeError("Please use pretix 2.7 or above to run this plugin!")

__version__ = "1.1.2"


class PluginApp(PluginConfig):
    name = 'pretix_adyen'
    verbose_name = 'Adyen payments for pretix'

    class PretixPluginMeta:
        name = 'Adyen'
        author = 'Martin Gross'
        description = gettext_lazy('Accept payments through Adyen, a global payment service provider offering a '
                                   'multitude of different payment methods.')
        visible = True
        picture = 'pretix_adyen/adyen_logo.svg'
        category = 'PAYMENT'
        version = __version__
        compatibility = "pretix>=2.7.0"

    def ready(self):
        from . import signals  # NOQA


default_app_config = 'pretix_adyen.PluginApp'
