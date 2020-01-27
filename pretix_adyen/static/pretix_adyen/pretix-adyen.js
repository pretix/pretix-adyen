'use strict';

var pretixadyen = {
    adyen: null,
    mountedcomponent: null,
    schemebrand: 'card',

    'load': function (method) {
        if (pretixadyen.mountedcomponent !== null) {
            pretixadyen.unmountcomponent();
        }

        $('.adyen-container').closest("form").find(".checkout-button-row .btn-primary").prop("disabled", true);

        pretixadyen.adyen = new AdyenCheckout({
            locale: $.trim($("#adyen_locale").html()),
            environment: $.trim($("#adyen_environment").html()),
            originKey: $.trim($("#adyen_originKey").html()),
            paymentMethodsResponse: JSON.parse($("#adyen_paymentMethodsResponse-" + method).val()),
            onChange: function (state, component) {
                switch (method) {
                    case 'scheme':
                        if (state.isValid && pretixadyen.schemebrand != "card") {
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
            onBrand: function (brand) {
                pretixadyen.schemebrand = brand.brand;
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

    'action': function () {
        if (pretixadyen.adyen !== null) {
            return;
        }

        waitingDialog.show(gettext("Contacting your bank …"));

        pretixadyen.adyen = new AdyenCheckout({
            locale: $.trim($("#adyen_locale").html()),
            environment: $.trim($("#adyen_environment").html()),
            originKey: $.trim($("#adyen_originKey").html()),
            onAdditionalDetails: function(state, component) {
                $("#adyen_stateData").val(JSON.stringify(state.data));
                $('#scacontainer').hide();
                $('#continuebutton').removeClass('hidden');
                $('#continuebutton').closest("form").submit();
                waitingDialog.show(gettext("Contacting your bank …"));
            }
        });

        let action = JSON.parse($("#adyen_action").val());
        pretixadyen.adyen.createFromAction(action).mount('#scacontainer');
        $('#scacontainer iframe').load(function () {
            waitingDialog.hide();
        });
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

