'use strict';

var pretixadyen = {
    adyen: null,
    mountedcomponent: null,

    'load': async function (method) {
        if (pretixadyen.mountedcomponent !== null) {
            pretixadyen.unmountcomponent();
        }

        $('.adyen-container').closest("form").find(".checkout-button-row .btn-primary").prop("disabled", true);

        pretixadyen.adyen = await AdyenCheckout({
            locale: $.trim($("#adyen_locale").html()),
            environment: $.trim($("#adyen_environment").html()),
            clientKey: $.trim($("#adyen_clientKey").html()),
            paymentMethodsResponse: JSON.parse($("#adyen_paymentMethodsResponse-" + method).val()),
            onChange: function (state, component) {
                switch (method) {
                    case 'scheme':
                        if (state.isValid) {
                            $("#adyen_paymentMethodData-" + method).val(JSON.stringify(state.data));
                            $('.adyen-container').closest("form").find(".checkout-button-row .btn-primary").prop("disabled", false);
                        } else {
                            $("#adyen_paymentMethodData-" + method).val('');
                        }
                        break;
                    default:
                        if (state.isValid) {
                            $("#adyen_paymentMethodData-" + method).val(JSON.stringify(state.data));
                            $('.adyen-container').closest("form").find(".checkout-button-row .btn-primary").prop("disabled", false);
                        } else {
                            $("#adyen_paymentMethodData-" + method).val('');
                        }
                }
            },
            onError: function (error) {
                console.log("onError", error);
            },
            onSubmit: function (state, component) {
                if (state.isValid) {
                    $("#adyen_paymentMethodData-" + method).val(JSON.stringify(state.data));
                    $('.adyen-container').closest("form").find(".checkout-button-row .btn-primary").prop("disabled", false);
                    $('.adyen-container').closest("form").get(0).submit();
                }
            },
            onPaymentCompleted: function (result, component) {
                console.log("onPaymentCompleted", result, component);
            }
        });

        switch (method) {
            case "scheme":
                pretixadyen.adyen.create(method, {
                    hasHolderName: true,
                    holderNameRequired: true,
                }).mount("#adyen-component-" + method);
                break;
            default:
                pretixadyen.adyen.create(method).mount("#adyen-component-" + method);
                break;
        }

        pretixadyen.mountedcomponent = method;
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
    }
};

$(function () {
    if ($("#scacontainer").length) {
        pretixadyen.action();
    }

    if (!$(".adyen-container").length)
    return;

    $("input[name=payment][value^='adyen_']").change(function () {
        let method = $(this).val().replace('adyen_', '');
        pretixadyen.load(method);
    });

    $("input[name=payment]").not("[value^='adyen_']").change(function () {
        pretixadyen.unmountcomponent();
    });

    if ($("input[name=payment][value^='adyen_']").is(':checked') || $(".payment-redo-form").length) {
        let method = $("input[name=payment][value^='adyen_']:checked").val().replace('adyen_', '');
        pretixadyen.load(method);
    }
});

