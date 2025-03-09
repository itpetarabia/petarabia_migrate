odoo.define('voucher_pos.models', function (require) {
    "use strict";

var models = require('point_of_sale.models');
var OrderSuper = models.Order;
var PosModelSuper = models.PosModel;

var utils = require('web.utils');
var round_pr = utils.round_precision;

models.load_models([
    {
        model:  'gift.voucher.pos',
        fields: ['id', 'voucher_type', 'name', 'product_id', 'expiry_date', 'product_categ'],
        loaded: function(self, vouchers)
        {
            self.vouchers = vouchers;
        }
    },
    {
        model:  'gift.coupon.pos',
        fields: ['id', 'name', 'code', 'voucher', 'start_date',
                'end_date', 'partner_id', 'limit', 'total_avail', 'voucher_val', 'type'],
        loaded: function (self, coupons)
        {
            self.coupons = coupons;
        },
    },
    {
        model: 'partner.coupon.pos',
        fields: ['partner_id', 'coupon_pos', 'number_pos'],
        loaded: function (self, applied_coupon)
        {
            self.applied_coupon = applied_coupon;
        },
    }
]);


// PosModel is extended to store vouchers, & coupon details
    models.PosModel = models.PosModel.extend({
        initialize: function(session, attributes) {
            PosModelSuper.prototype.initialize.call(this, session, attributes)
            this.vouchers = [''];
            this.coupons = [];
            this.applied_coupon = [];
        },
    });



    models.Order = models.Order.extend({
        initialize: function(attributes,options){
            this.coupon = false;
            this.coupon_status = [];
            return OrderSuper.prototype.initialize.call(this, attributes,options);;
        },
        set_coupon_value: function (coupon) {
            this.coupon_status = coupon;
            return;
        },
        coupon_applied: function () {
            this.coupon = true;
            this.export_as_JSON();
            return;
        },
        check_voucher_validity: function () {
            //console.log('check_voucher_validity=');
            var self = this;
            var order = self.pos.get_order();
            var vouchers = self.pos.vouchers;
            var voucher = null;
            for (var i in vouchers){
                if(vouchers[i]['id'] == self.coupon_status.voucher[0]){
                    voucher = vouchers[i];
                    break;
                }
            }
            var flag ;
            if(voucher){
                switch(voucher.voucher_type){
                    case 'product': {
                        var lines = order.orderlines.models;
                        var products = {};
                        for (var p in lines){
                            products[lines[p].product.id] = null;
                        }
                        if(voucher.product_id[0] in products){
                            flag = true;
                        }
                        else
                            flag = false;
                        break;
                    }
                    case 'category':{
                        var lines = order.orderlines.models;
                        var category = {};
                        for (var p in lines){
                            if(lines[p].product.pos_categ_id){
                                category[lines[p].product.pos_categ_id[0]] = null;
                            }
                        }
                        if(voucher.product_categ[0] in category){
                            flag = true;
                        }
                        else
                            flag = false;
                        break;
                    }
                    case 'all': flag = true; break;
                    default: break;
                }
            }
            return flag;
        },
        export_as_JSON: function () {
            var self = OrderSuper.prototype.export_as_JSON.call(this);
            self.coupon = this.coupon;
            self.coupon_status = this.coupon_status;
            return self;
        },
        init_from_JSON: function(json) {
            this.coupon = json.coupon;
            this.coupon_status = json.coupon_status;
            OrderSuper.prototype.init_from_JSON.call(this, json);
        },
        //double check
        /*get_total_without_tax: function() {
            var res = OrderSuper.prototype.get_total_without_tax.call(this);
            var final_res = round_pr(this.orderlines.reduce((function(sum, orderLine) {
                return sum + (orderLine.get_unit_price() * orderLine.get_quantity() * (1.0 - (orderLine.get_discount() / 100.0)));
            }), 0), this.pos.currency.rounding);
            return final_res;
        },*/

    });



});
