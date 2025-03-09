odoo.define('pos_fixed_discount.models', function (require) {
"use strict";
console.log("pos_fixed_discount.models");
var rpc = require('web.rpc');
var models = require('point_of_sale.models');

const { Context } = owl;
var PosDB = require('point_of_sale.DB');
var devices = require('point_of_sale.devices');
var concurrency = require('web.concurrency');
var config = require('web.config');
var core = require('web.core');
var field_utils = require('web.field_utils');
var time = require('web.time');
var utils = require('web.utils');

var QWeb = core.qweb;
var _t = core._t;
var Mutex = concurrency.Mutex;
var round_di = utils.round_decimals;
var round_pr = utils.round_precision;

var exports = {};



var _super_posorderline = models.Orderline.prototype;

models.Orderline = models.Orderline.extend({
    initialize: function(attr,options){
        _super_posorderline.initialize.call(this, attr,options);
        this.discount_fixed = 0;

    },
    init_from_JSON: function(json) {
        _super_posorderline.init_from_JSON.call(this, json);
        if(json.discount_fixed > 0) {
         this.set_discount_fixed(json.discount_fixed);
        }
        else {
         this.set_discount(json.discount);
        }
    },
    clone: function(){
        var orderline = _super_posorderline.clone.call(this);
        orderline.discount_fixed = this.discount_fixed;
        return orderline;
    },
    // sets a discount amount
    set_discount_fixed: function(discount){
        this.discount_fixed = discount;
        this.discount = 0.0;
        this.discountStr = 'fixed' ;
        this.trigger('change',this);
    },
    // returns the discount amount
    get_discount_fixed: function(){
        console.log("get_discount_fixed")
        return this.discount_fixed;
    },

    // sets a discount [0,100]%
    set_discount: function(discount){
        _super_posorderline.set_discount.call(this, discount);
        this.discount_fixed = 0.0;
        //var disc = Math.min(Math.max(parseFloat(discount) || 0, 0),100);
        //this.discount = disc;
        //this.discountStr = '' + disc;
        this.trigger('change',this);
    },

    // when we add an new orderline we want to merge it with the last line to see reduce the number of items
    // in the orderline. This returns true if it makes sense to merge the two
    can_be_merged_with: function(orderline){
        /*
        var price = parseFloat(round_di(this.price || 0, this.pos.dp['Product Price']).toFixed(this.pos.dp['Product Price']));
        var order_line_price = orderline.get_product().get_price(orderline.order.pricelist, this.get_quantity());
        order_line_price = orderline.compute_fixed_price(order_line_price);
        if( this.get_product().id !== orderline.get_product().id){    //only orderline of the same product can be merged
            return false;
        }else if(!this.get_unit() || !this.get_unit().is_pos_groupable){
            return false;
        }else if(this.get_discount() > 0){             // we don't merge discounted orderlines
            return false;
        }else if(this.get_discount_fixed() > 0){             // we don't merge discounted orderlines
            return false;
        }else if(!utils.float_is_zero(price - order_line_price - orderline.get_price_extra(),
                    this.pos.currency.decimals)){
            return false;
        }else if(this.product.tracking == 'lot' && (this.pos.picking_type.use_create_lots || this.pos.picking_type.use_existing_lots)) {
            return false;
        }else if (this.description !== orderline.description) {
            return false;
        }else{
            return true;
        }
        */
        //fkp
        var res = _super_posorderline.can_be_merged_with.apply(this,arguments);
        if(this.get_discount() > 0)
            res = false;
        if(this.get_discount_fixed() > 0)
            res = false;
        return res;
    },

    export_as_JSON: function() {
        var pack_lot_ids = [];
        if (this.has_product_lot){
            this.pack_lot_lines.each(_.bind( function(item) {
                return pack_lot_ids.push([0, 0, item.export_as_JSON()]);
            }, this));
        }
        return {
            qty: this.get_quantity(),
            price_unit: this.get_unit_price(),
            price_subtotal: this.get_price_without_tax(),
            price_subtotal_incl: this.get_price_with_tax(),
            discount: this.get_discount(),
            discount_fixed: this.get_discount_fixed(),
            product_id: this.get_product().id,
            tax_ids: [[6, false, _.map(this.get_applicable_taxes(), function(tax){ return tax.id; })]],
            id: this.id,
            pack_lot_ids: pack_lot_ids,
            description: this.description,
            full_product_name: this.get_full_product_name(),
            price_extra: this.get_price_extra(),
        };
    },
    //used to create a json of the ticket, to be sent to the printer
    export_for_printing: function(){
        return {
            id: this.id,
            quantity:           this.get_quantity(),
            unit_name:          this.get_unit().name,
            price:              this.get_unit_display_price(),
            discount:           this.get_discount(),
            discount_fixed:     this.get_discount_fixed(),
            product_name:       this.get_product().display_name,
            product_name_wrapped: this.generate_wrapped_product_name(),
            price_lst:          this.get_lst_price(),
            display_discount_policy:    this.display_discount_policy(),
            price_display_one:  this.get_display_price_one(),
            price_display :     this.get_display_price(),
            price_with_tax :    this.get_price_with_tax(),
            price_without_tax:  this.get_price_without_tax(),
            price_with_tax_before_discount:  this.get_price_with_tax_before_discount(),
            tax:                this.get_tax(),
            product_description:      this.get_product().description,
            product_description_sale: this.get_product().description_sale,
        };
    },

    get_base_price:    function(){
        var rounding = this.pos.currency.rounding;
        if(this.discount_fixed !== 0){
            return round_pr(this.get_unit_price() * this.get_quantity() - this.get_discount_fixed(), rounding);
            }
        return round_pr(this.get_unit_price() * this.get_quantity() * (1 - this.get_discount()/100), rounding);
    },

    get_display_price_one: function(){
        var rounding = this.pos.currency.rounding;
        var price_unit = this.get_unit_price();
        if (this.pos.config.iface_tax_included !== 'total') {
            if(this.discount_fixed !== 0){
                return round_pr(price_unit - this.get_discount_fixed(), rounding);
            }
            return round_pr(price_unit * (1.0 - (this.get_discount() / 100.0)), rounding);

        } else {
            var product =  this.get_product();
            var taxes_ids = product.taxes_id;
            var taxes =  this.pos.taxes;
            var product_taxes = [];

            _(taxes_ids).each(function(el){
                product_taxes.push(_.detect(taxes, function(t){
                    return t.id === el;
                }));
            });

            var all_taxes = this.compute_all(product_taxes, price_unit, 1, this.pos.currency.rounding);
            if(this.discount_fixed !== 0){
                return round_pr(all_taxes.total_included - this.get_discount_fixed(), rounding);
            }
            return round_pr(all_taxes.total_included * (1 - this.get_discount()/100), rounding);

        }
    },

    get_all_prices: function(){
        //_super_posorderline.get_all_prices.call(this);
        var self = this;
        if(this.discount_fixed > 0)
        {
            //var price_unit = this.get_unit_price() * this.get_quantity() - this.get_discount_fixed();
            var price_unit = this.get_unit_price() - this.get_discount_fixed() / this.get_quantity();
        }
        else {
            var price_unit = this.get_unit_price() * (1.0 - (this.get_discount() / 100.0));
        }
        var taxtotal = 0;

        var product =  this.get_product();
        var taxes =  this.pos.taxes;
        var taxes_ids = _.filter(product.taxes_id, t => t in this.pos.taxes_by_id);
        var taxdetail = {};
        var product_taxes = [];

        _(taxes_ids).each(function(el){
            var tax = _.detect(taxes, function(t){
                return t.id === el;
            });
            product_taxes.push.apply(product_taxes, self._map_tax_fiscal_position(tax));
        });
        product_taxes = _.uniq(product_taxes, function(tax) { return tax.id; });

        var all_taxes = this.compute_all(product_taxes, price_unit, this.get_quantity(), this.pos.currency.rounding);
        var all_taxes_before_discount = this.compute_all(product_taxes, this.get_unit_price(), this.get_quantity(), this.pos.currency.rounding);
        _(all_taxes.taxes).each(function(tax) {
            taxtotal += tax.amount;
            taxdetail[tax.id] = tax.amount;
        });

        return {
            "priceWithTax": all_taxes.total_included,
            "priceWithoutTax": all_taxes.total_excluded,
            "priceSumTaxVoid": all_taxes.total_void,
            "priceWithTaxBeforeDiscount": all_taxes_before_discount.total_included,
            "tax": taxtotal,
            "taxDetails": taxdetail,
        };
    },



    
});

//end
});