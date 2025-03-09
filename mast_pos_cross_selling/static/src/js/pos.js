odoo.define('pos_pro_cross_selling.pos', function (require) {
"use strict";

const { Gui } = require('point_of_sale.Gui');
var models = require('point_of_sale.models');
var rpc = require('web.rpc');
var session = require('web.session');
var core = require('web.core');
var utils = require('web.utils');

var _t = core._t;
var round_di = utils.round_decimals;
/*
var _super_posmodel = models.PosModel.prototype;
models.PosModel = models.PosModel.extend({
    
});
*/
models.load_fields('product.product', 'accessory_product_ids');
/*
var _super_order = models.Order.prototype;
models.Order = models.Order.extend({
    //@Override
    add_product: function(product, options){
        var self = this;
        var res = _super_order.add_product.call(self, product, options);
        if (product) {
            let line = self.get_selected_orderline();
            if (options.is_cs){
                //line.is_cross_selling = true;
                line.set_cross_selling(options.is_cs)
            }
        }

        return res;


    },

});
*/

var orderline_super = models.Orderline.prototype;
models.Orderline = models.Orderline.extend({
    initialize: function(attr,options){
        orderline_super.initialize.call(this, attr,options);
        this.is_cross_selling = false;
        if (options.json){
            this.csStr = options.json.csStr;
        }else{
            this.csStr = '';
        }

    },
    init_from_JSON: function(json) {
        orderline_super.init_from_JSON.call(this, json);
        this.set_cross_selling(json.is_cross_selling);
        //this.csStr = json.csStr || '';
        //this.is_cross_selling = json.is_cross_selling || false;



    },
    /*clone: function(){
        var orderline = orderline_super.clone.call(this);
        orderline.is_cross_selling = this.is_cross_selling;
        return orderline;
    },*/
    export_as_JSON: function() {
        var json = orderline_super.export_as_JSON.apply(this,arguments);
        json.is_cross_selling = this.get_cross_selling();
        json.csStr = this.get_cross_selling_str();
        return json;
    },


    set_cross_selling: function(cs){
        if (cs == true) {
            this.cross_selling = true;
            this.csStr = 'Cross Selling Product';
        }
        else {
            this.cross_selling = false;
            this.csStr = '';
        }
        this.trigger('change',this);
    },

    get_cross_selling: function(){
        return this.cross_selling;
    },
    get_cross_selling_str: function(){
        return this.csStr;
    },

});

});
