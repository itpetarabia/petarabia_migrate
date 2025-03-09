odoo.define('pos_loyalty_customize.pos_loyalty', function (require) {
"use strict";

var models = require('point_of_sale.models');
var core = require('web.core');
var utils = require('web.utils');

var round_pr = utils.round_precision;
var QWeb     = core.qweb;
var round_di = utils.round_decimals;

var _t = core._t;

//models.load_fields('res.partner','loyalty_points');


var _super = models.Order;
var _super_posorderline = models.Orderline.prototype;

models.Orderline = models.Orderline.extend({

    can_be_merged_with: function(orderline){
        var res = _super_posorderline.can_be_merged_with.apply(this,arguments);
        var price = parseFloat(round_di(this.price || 0, this.pos.dp['Product Price']).toFixed(this.pos.dp['Product Price']));
        var order_line_price = orderline.get_product().get_price(orderline.order.pricelist, this.get_quantity());
        if(res == false && orderline.reward_id && this.reward_id && orderline.reward_id == this.reward_id && this.price == orderline.price
            && !utils.float_is_zero(price - order_line_price - orderline.get_price_extra(),this.pos.currency.decimals)){

            res = true;
            //force keep loyalty price (otherwise sin merge time they again calculte with product price)
            this.price_manually_set = true;
        }

       return res;
    }
});


models.Order = models.Order.extend({

    apply_reward: function(reward){
        var client = this.get_client();
        var product, product_price, order_total, spendable;
        var crounding;

        if (!client) {
            return;
        } else if (reward.reward_type === 'gift') {
            product = this.pos.db.get_product_by_id(reward.gift_product_id[0]);

            if (!product) {
                return;
            }

            this.add_product(product, {
                price: 0,
                quantity: 1,
                merge: false,
                extras: { reward_id: reward.id },
            });

        } else if (reward.reward_type === 'discount') {

            crounding = this.pos.currency.rounding;
            spendable = this.get_spendable_points();
            order_total = this.get_total_with_tax();
            var discount = 0;

            product = this.pos.db.get_product_by_id(reward.discount_product_id[0]);

            if (!product) {
                return;
            }

            if(reward.discount_type === "percentage") {
                if(reward.discount_apply_on === "on_order"){
                    discount += round_pr(order_total * (reward.discount_percentage / 100), crounding);
                }

                if(reward.discount_apply_on === "specific_products") {
                    for (var prod of reward.discount_specific_product_ids){
                        var specific_products = this.pos.db.get_product_by_id(prod);

                        if (!specific_products)
                            return;

                        for (var line of this.get_orderlines()){
                            if(line.product.id === specific_products.id)
                                discount += round_pr(line.get_price_with_tax() * (reward.discount_percentage / 100), crounding);
                        }
                    }
                }

                if(reward.discount_apply_on === "cheapest_product") {
                    var price;
                    for (var line of this.get_orderlines()){
                        if((!price || price > line.get_unit_price()) && line.product.id !== product.id) {
                            discount = round_pr(line.get_price_with_tax() * (reward.discount_percentage / 100), crounding);
                            price = line.get_unit_price();
                        }
                    }
                }
             }

            if(reward.discount_max_amount !== 0 && discount > reward.discount_max_amount)
                discount = reward.discount_max_amount;
            //console.log("add reward=",-reward.discount_fixed_amount)

            this.add_product(product, {
                price: (reward.discount_type === "percentage")? -discount: -reward.discount_fixed_amount,
                quantity: 1,
                //merge: false,
                extras: { reward_id: reward.id },
            });
        }
    },


});


});