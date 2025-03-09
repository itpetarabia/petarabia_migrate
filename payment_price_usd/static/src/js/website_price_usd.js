odoo.define('payment_price_usd.checkout', function (require) {
'use strict';

var core = require('web.core');
var publicWidget = require('web.public.widget');
require('website_sale_delivery.checkout');

var _t = core._t;

publicWidget.registry.websiteSaleDelivery.include({

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _handleCarrierUpdateResult: function (result) {
        this._super.apply(this, arguments);
        console.log("test after super", result)
        var $amountTotalUSD = $('#order_total_usd .monetary_field, #amount_total_summary.monetary_field');
        console.log("$amountTotalUSD old val=",$amountTotalUSD)
        if (result.status === true) {
           $amountTotalUSD.html(result.new_amount_total_usd);

        } else {
            $amountTotalUSD.html(result.new_amount_total_usd);

        }

    },

});
});
