'use strict';

var pretixadyen = {
    adyen: null,
    mountedcomponents: [],
    schemebrand: 'card',

    'load': function (method) {
        if (pretixadyen.mountedcomponents.includes(method)) {
            return;
        }
        pretixadyen.adyen = null;

        //$('.adyen-container').closest("form").find(".checkout-button-row .btn-primary").prop("disabled", true);

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
                        } else {
                            $("#adyen_paymentMethodData-" + method).val('');
                        }
                        break;
                    default:
                        if (state.isValid) {
                            $("#adyen_paymentMethodData-" + method).val(JSON.stringify(state.data));
                        } else {
                            $("#adyen_paymentMethodData-" + method).val('');
                        }
                }
            },
            // This is not supported on non-card components :(
            // onConfigSuccess: function () {
            //     $('.adyen-container').closest("form").find(".checkout-button-row .btn-primary").prop("disabled", false);
            // },
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

        pretixadyen.mountedcomponents.push(method);
    },

    'action': function () {
        if (pretixadyen.adyen !== null) {
            return;
        }

        pretixadyen.adyen = new AdyenCheckout({
            locale: $.trim($("#adyen_locale").html()),
            environment: $.trim($("#adyen_environment").html()),
            originKey: $.trim($("#adyen_originKey").html()),
            onAdditionalDetails: function(state, component) {
                $("#adyen_stateData").val(JSON.stringify(state.data));
                $('#scacontainer').hide();
                $('#continuebutton').removeClass('hidden');
                $('#continuebutton').closest("form").submit();
            }
        });

        let action = JSON.parse($("#adyen_action").val());
        pretixadyen.adyen.createFromAction(action).mount('#scacontainer');
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

    if ($("input[name=payment][value^='adyen_']").is(':checked') || $(".payment-redo-form").length) {
        let method = $("input[name=payment][value^='adyen_']:checked").val().replace('adyen_', '');
        pretixadyen.load(method);
    }
});

