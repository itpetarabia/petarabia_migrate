/* Copyright 2018 Dinar Gabbasov <https://it-projects.info/team/GabbasovDinar>
 * Copyright 2019 Kolushov Alexandr <https://it-projects.info/team/KolushovAlexandr>
 * License MIT (https://opensource.org/licenses/MIT). */
odoo.define("pos_orders_history_return.models", function(require) {
    "use strict";

    var models = require("pos_orders_history.models");
    var field_utils = require("web.field_utils");
    var utils = require('web.utils');
    var round_di = utils.round_decimals;
    var core = require('web.core');
    var _t = core._t;
    const { Gui } = require('point_of_sale.Gui');

    models.PosModel = models.PosModel.extend({
        get_returned_orders_by_pos_reference: function(reference) {
            ////console.log("get_returned_orders_by_pos_reference",this);
            /* hided
            var all_orders = this.db.pos_orders_history;
            return all_orders.filter(function(order) {
                return order.returned_order && order.pos_reference === reference;
            });*/
            //extra
        	var all_orders = this.db.pos_orders_history;
            //current_order same as to new return order
        	var current_order = this.get_order();
        	if(current_order && current_order.returned_order_id)
            {
            	var to_return = all_orders.filter(function(order){
                	return order.returned_order_id && order.returned_order_id[0] == current_order.returned_order_id;
                });
            }
            else
        	{
        	    var to_return = all_orders.filter(function(order){
                	return order.returned_order && order.pos_reference.includes(reference);
                });
        	}
            return to_return;
        	//
        },
        get_returned_orders_by_order: function(reference,order) {
            ////console.log("get_returned_orders_by_order",this);
            var all_orders = this.db.pos_orders_history;
            //current_order same as to new return order
        	var current_order = order;
        	if(current_order)
            {
            	var to_return = all_orders.filter(function(order){
            	    //console.log("order.returned_order_id[0] == current_order.id",order.returned_order_id,current_order);
                	return order.returned_order_id && order.returned_order_id[0] == current_order.id;
                });
            }
            else
        	{
        	    var to_return = all_orders.filter(function(order){
                	return order.returned_order && order.pos_reference.includes(reference);
                });
        	}
            return to_return;
        	//
        },
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        get_edit_return: function() {
    		////console.log('get_edit_return=',this.edit_return);
            return this.edit_return;
        },
        add_product: function(product, options) {
            options = options || {};
            if (this.get_mode() === "return") {
                //extra
            	var order = this.pos.get_order();
            	//
                var current_return_qty = this.get_current_product_return_qty(product);
                //console.log("current_return_qty",current_return_qty,product.max_return_qty);
                if (product.max_return_qty - current_return_qty <= 0 ) {
                    Gui.showPopup('ConfirmPopup', {
                        title: 'Nothing to return',
                        body: 'This product is a fully returned one',
                    });
                }
                var residual_qty = product.max_return_qty - current_return_qty || 0;
                //extra fkp && order && order.edit_return != true
                if (residual_qty > 0.0001 && order && order.edit_return != true) {
                    var quantity = Math.min(
                        options.quantity || 1,
                        product.max_return_qty,
                        residual_qty
                    );
                    _super_order.add_product.apply(this, [
                        product,
                        _.extend(options || {}, {
                            quantity: field_utils.format.float(quantity, {
                                digits: [69, 3],
                            }),
                        }),
                    ]);
                    this.change_return_product_limit(product);
                }
                //extra
                else if(order && order.edit_return == true)
                {
                    _super_order.add_product.apply(this, arguments);
                    this.change_return_product_limit(product);
                }
                //
            } else {
                _super_order.add_product.apply(this, arguments);
            }
        },
        get_current_product_return_qty: function(product) {
            var orderlines = this.get_orderlines();
            var product_orderlines = orderlines.filter(function(line) {
                return line.product.id === product.id;
            });
            var qty = 0;
            product_orderlines.forEach(function(line) {
                qty += line.quantity;
            });
            if (qty < 0) {
                qty = -qty;
            }
            return qty;
        },
        change_return_product_limit: function(product) {
            if (this.get_mode() === "return_without_receipt") {
                return;
            }
            var el = $('article[data-product-id="' + product.id + '"] .max-return-qty');
            var qty = this.get_current_product_return_qty(product);

            el.html(
                field_utils.format.float(product.max_return_qty - qty, {
                    digits: [69, 3],
                })
            );
        },
        export_as_JSON: function() {
            var data = _super_order.export_as_JSON.apply(this, arguments);
            data.return_lines = this.return_lines;
            //extra
            data.returned_order_id = this.returned_order_id;
            //data.partner_id = this.get_client();
            ////console.log("export_as_JSON",this);
            //
            return data;
        },
        init_from_JSON: function(json) {
            //extra fkp
        	this.returned_order_id = json.returned_order_id;
        	if(json.mode != undefined && json.mode =='return' && !json.uid)
            {
            	//arguments - sequence_number,uid disabled in - models.js - click_return_order_by_id: function
            	json.sequence_number = this.pos.pos_session.sequence_number++;
            	this.sequence_number = json.sequence_number;
            	json.uid  = this.generate_unique_id();
            }
        	//
            this.return_lines = json.return_lines;
            _super_order.init_from_JSON.call(this, json);
        },
        //extra fkp
        get_returned_order_reference: function()
        {
        	var returned_order_reference = this.returned_order_id ? this.pos.db.orders_history_by_id[this.returned_order_id].pos_reference : null;
        	return returned_order_reference;
        },
        //
    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        initialize: function(attr, options) {
            //console.log("initialize-this",this);
            _super_orderline.initialize.apply(this, arguments);
            var order = this.pos.get_order();
            if (
                order &&
                order.get_mode() === "return" &&
                this.product.old_price &&
                this.price !== this.product.old_price
            ) {
                this.price = this.product.old_price
                this.set_unit_price(this.product.old_price);
                ////console.log("set_unit_price",this);
            }
        },
        set_quantity: function(quantity) {
            var order = this.pos.get_order();
            if (
                order &&
                order.get_mode() === "return_without_receipt" &&
                quantity !== "remove" &&
                quantity > 0
            ) {
                //hided
                //quantity = -quantity;
            	//extra fkp
            	if(order && order.edit_return != true)
            		quantity = -quantity;
                _super_orderline.set_quantity.call(this, quantity);
            } else if (
                order &&
                order.get_mode() === "return" &&
                quantity !== "remove"
            ) {
                var current_return_qty = this.order.get_current_product_return_qty(
                    this.product
                );
                if (this.quantity) {
                    current_return_qty += this.quantity;
                }
                //extra fkp && order.edit_return != true
                if (
                    quantity &&
                    current_return_qty + Number(quantity) <= this.product.max_return_qty && order.edit_return != true
                ) {
                    if (quantity > 0) {
                        quantity = -quantity;
                    }
                    _super_orderline.set_quantity.call(this, quantity);
                    order.change_return_product_limit(this.product);
                }
                //extra
                else if(order && order.edit_return == true)
            	{
                	_super_orderline.set_quantity.call(this, quantity);
                	order.change_return_product_limit(this.product);
            	}
                //
                else if (quantity === "") {
                    _super_orderline.set_quantity.call(this, quantity);
                    order.change_return_product_limit(this.product);
                }
            } else {
                _super_orderline.set_quantity.call(this, quantity);
            }
        },
        set_unit_price: function(price){
            ////console.log("set_unit_price",price);
            var order = this.pos.get_order();
            _super_orderline.set_unit_price.call(this, price);
            /*this.order.assert_editable();
            var parsed_price = !isNaN(price) ?
                price :
                isNaN(parseFloat(price)) ? 0 : field_utils.parse.float('' + price)*/
            if (order && order.get_mode() === "return" && this.product.old_price && order.edit_return !== true)
                this.price = round_di(this.product.old_price || 0, this.pos.dp['Product Price']);
                this.trigger('change',this);
        },
    });
});
