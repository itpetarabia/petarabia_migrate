odoo.define('pos_loyalty_ext.pos_loyalty', function (require) {
"use strict";

var models = require('point_of_sale.models');
var core = require('web.core');
var utils = require('web.utils');

var round_pr = utils.round_precision;

var _t = core._t;

models.load_fields('pos.payment.method','payment_method_loyal_ext');
models.load_fields('product.pricelist','pricelist_loyal_ext');


var _super = models.Order;
models.Order = models.Order.extend({

    export_as_JSON: function(){
        var json = _super.prototype.export_as_JSON.apply(this,arguments);
        json.spent_point = this.get_spent_points();
        json.won_point = this.get_won_points();
        return json;
    },

    /* inherit */
    get_won_points: function(){
        //console.log('get_won_points=',this)
        if (this.pricelist.pricelist_loyal_ext)
            return round_pr(0, 1);
        //exlcude payment method
        if (this.paymentlines.length && this.paymentlines.models.length)
        {
            for (var i = 0; i < this.paymentlines.models.length; i++)
            {
                if (this.paymentlines.models[i].payment_method.payment_method_loyal_ext && this.paymentlines.models[i].amount)
                    return round_pr(0, 1);
            }
        }
        //
        var json = _super.prototype.get_won_points.apply(this,arguments);
        return json;
    },


});

});
