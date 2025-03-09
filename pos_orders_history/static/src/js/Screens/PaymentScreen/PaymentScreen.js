odoo.define('pos_order_history.PaymentScreen', function(require) {
    'use strict';

    const { parse } = require('web.field_utils');
    const PosComponent = require('point_of_sale.PosComponent');
    const { useErrorHandlers } = require('point_of_sale.custom_hooks');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const { onChangeOrder } = require('point_of_sale.custom_hooks');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const core = require("web.core");
    var QWeb = core.qweb;
    var models = require("point_of_sale.models");

    const PosOrderHistoryPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {

            async _finalizeValidation() {
                console.log("finalize_validation123w")
                await super._finalizeValidation();
                this.env.pos.manual_update_order_history(1);


            }
        };

    Registries.Component.extend(PaymentScreen, PosOrderHistoryPaymentScreen);

    return PaymentScreen;
});

