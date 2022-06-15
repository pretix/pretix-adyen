'use strict';

var pretixadyen = {
    adyen: null,
    mountedcomponent: null,
    method: null,
    brand: null,

    'load': async function (method_brand) {
        if (pretixadyen.mountedcomponent !== null) {
            pretixadyen.unmountcomponent();
        }

        pretixadyen.method = this.get_method(method_brand);
        pretixadyen.brand = this.get_brand(method_brand);

        $('.adyen-container').closest("form").find(".checkout-button-row .btn-primary").prop("disabled", true);

        pretixadyen.adyen = await AdyenCheckout({
            locale: $.trim($("#adyen_locale").html()),
            environment: $.trim($("#adyen_environment").html()),
            clientKey: $.trim($("#adyen_clientKey").html()),
            paymentMethodsResponse: JSON.parse($.trim($("#adyen_paymentMethodsResponse").html())),
            onChange: function (state, component) {
                switch (pretixadyen.method) {
                    case 'scheme':
                        if (state.isValid) {
                            $("#adyen_paymentMethodData-" + pretixadyen.method).val(JSON.stringify(state.data));
                            $('.adyen-container').closest("form").find(".checkout-button-row .btn-primary").prop("disabled", false);
                        } else {
                            $("#adyen_paymentMethodData-" + pretixadyen.method).val('');
                        }
                        break;
                    default:
                        if (state.isValid) {
                            $("#adyen_paymentMethodData-" + method_brand).val(JSON.stringify(state.data));
                            $('.adyen-container').closest("form").find(".checkout-button-row .btn-primary").prop("disabled", false);
                        } else {
                            $("#adyen_paymentMethodData-" + method_brand).val('');
                        }
                }
            },
            onError: function (error) {
                console.log("onError", error);
            },
            onSubmit: function (state, component) {
                if (state.isValid) {
                    $("#adyen_paymentMethodData-" + method_brand).val(JSON.stringify(state.data));
                    $('.adyen-container').closest("form").find(".checkout-button-row .btn-primary").prop("disabled", false);
                    $('.adyen-container').closest("form").get(0).submit();
                }
            },
            onPaymentCompleted: function (result, component) {
                console.log("onPaymentCompleted", result, component);
            }
        });

        switch (pretixadyen.method) {
            case "scheme":
                pretixadyen.adyen.create(pretixadyen.method, {
                    hasHolderName: true,
                    holderNameRequired: true,
                }).mount("#adyen-component-" + pretixadyen.method);
                break;
            case "giftcard":
                pretixadyen.adyen.create(pretixadyen.method, {
                    brand: pretixadyen.brand
                }).mount("#adyen-component-" + method_brand);
                break;
            default:
                pretixadyen.adyen.create(pretixadyen.method).mount("#adyen-component-" + method_brand);
                break;
        }

        pretixadyen.mountedcomponent = method_brand;
    },

    'unmountcomponent': function() {
        $('#adyen-component-' + pretixadyen.mountedcomponent).empty();
        pretixadyen.mountedcomponent = null;
        pretixadyen.adyen = null;
        $('.adyen-container').closest("form").find(".checkout-button-row .btn-primary").prop("disabled", false);
    },

    'action': async function () {
        if (pretixadyen.adyen !== null) {
            return;
        }

        waitingDialog.show(gettext("Contacting your bank …"));

        pretixadyen.adyen = await AdyenCheckout({
            locale: $.trim($("#adyen_locale").html()),
            environment: $.trim($("#adyen_environment").html()),
            clientKey: $.trim($("#adyen_clientKey").html()),
            onAdditionalDetails: function (state, component) {
                $("#adyen_stateData").val(JSON.stringify(state.data));
                $('#scacontainer').hide();
                $('#continuebutton').removeClass('hidden');
                $('#continuebutton').closest("form").submit();
                waitingDialog.show(gettext("Contacting your bank …"));
            }
        });

        let action = JSON.parse($("#adyen_action").val());
        pretixadyen.adyen.createFromAction(action).mount('#scacontainer');
        waitingDialog.hide();
    },

    'get_method': function (method_brand) {
        return method_brand.split("__")[0]
    },

    'get_brand': function (method_brand) {
        method_brand = method_brand.split("__")
        return method_brand[method_brand.length - 1]
    }
};

$(function () {
    if ($("#scacontainer").length) {
        pretixadyen.action();
    }

    if (!$(".adyen-container").length)
    return;

    $("input[name=payment][value^='adyen_']").change(function () {
        let method_brand = $(this).val().replace('adyen_', '');
        pretixadyen.load(method_brand);
    });

    $("input[name=payment]").not("[value^='adyen_']").change(function () {
        pretixadyen.unmountcomponent();
    });

    if ($("input[name=payment][value^='adyen_']").is(':checked') || $(".payment-redo-form").length) {
        let method_brand = $("input[name=payment][value^='adyen_']:checked").val().replace('adyen_', '');
        pretixadyen.load(method_brand);
    }
});

