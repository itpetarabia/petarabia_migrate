odoo.define('pos_orders_history_return.OrdersHistoryScreenWidget', function(require) {
    'use strict';
    const { debounce } = owl.utils;
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const OrdersHistoryScreenWidget = require('pos_orders_history.OrdersHistoryScreenWidget');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var _t = core._t;
    var dom = require('web.dom');
    var QWeb = core.qweb;
    var models = require("pos_orders_history.models");

    const OrdersHistoryScreenWidgetReturn = (OrdersHistoryScreenWidget) =>
        class extends OrdersHistoryScreenWidget {
            constructor() {
                super(...arguments);

            }
            mounted() {
                //this._super();
                this._showOrderHistory();
                super.mounted(...arguments);

                if (this.env.pos.config.return_orders) {
                    this.set_return_action();
                }


            }
            rtn_filter(e) {
                ////console.log("user_filtereeeeeee",e);
                e.stopImmediatePropagation();
                this.change_filter("rtn", $('#rtn-filter'));
            }
            set_return_action() {
                ////console.log("set_return_action",this);
                var self = this;
                var $return_button = $(".button-return");
                $return_button.removeClass("oe_hidden");
                $return_button.unbind("click");
                //$('.btn_edit_return_add').addClass('highlight');
                //$('.btn_edit_return_add').removeClass('oe_hidden');
                //$('.btn_edit_return_take').addClass('oe_hidden');
                $return_button.click(function(e) {
                    var parent = $(this).parents(".order-line");
                    var id = parseInt(parent.data("id"), 10);
                    $('.btn_edit_return_add').addClass('highlight');
                    $('.btn_edit_return_add').removeClass('oe_hidden');
                    $('.btn_edit_return_take').addClass('oe_hidden');
                    //console.log('iddddd',id);
                    self.click_return_order_by_id(id);


                    //self.trigger('close-temp-screen');
                });
            }
            /*
            load_order_by_barcode(barcode) {
                if (this.env.pos.config.return_orders) {
                    var self = this;
                    rpc.query({
                        model: "pos.order",
                        method: "search_read",
                        args: [[["pos_history_reference_uid", "=", barcode]]],
                    }).then(
                        function(o) {
                            if (o && o.length) {
                                self.env.pos.update_orders_history(o);
                                o.forEach(function(exist_order) {
                                    self.env.pos
                                        .get_order_history_lines_by_order_id(exist_order.id)
                                        .done(function(lines) {
                                            self.env.pos.update_orders_history_lines(lines);
                                            if (!exist_order.returned_order) {
                                                self.search_order_on_history(exist_order);
                                            }
                                        });
                                });
                            } else {
                                this.showPopup("ErrorPopup", {
                                    title: this.env._t("Error: Could not find the Order"),
                                    body: this.env._t("There is no order with this barcode."),
                                });
                            }
                        },
                        function(err, event) {
                            event.preventDefault();
                            console.error(err);
                            this.showPopup("ErrorPopup", {
                                title: this.env._t("Error: Could not find the Order"),
                                body: err.data,
                            });

                        }
                    );
                } else {
                    this._super(barcode);
                }
            }
            */
            render_list(orders) {
                var self = this;
                if (!this.env.pos.config.show_returned_orders) {
                    orders = orders.filter(function(order) {
                        return order.returned_order !== true;
                    });
                }
                //self._super(orders);
                super.render_list(...arguments);

                if (this.env.pos.config.return_orders) {
                    this.set_return_action();
                }
                //return super.render_list(...arguments);
            }
            ///
            /*renderElement() {
                //console.log("renderElement4444444");
                //this._super();
                var self = this;
                var order = this.env.pos.get_order();
                //console.log("order444444",order,order.get_mode());
                if (
                    order &&
                    (order.get_mode() === "return" ||
                        order.get_mode() === "return_without_receipt")
                ) {
                    var returned_orders = this.env.pos.get_returned_orders_by_pos_reference(
                        order.name
                    );
                    //console.log("returned_orders4444444",returned_orders);
                    // Add exist products
                    var products = [];
                    if (returned_orders && returned_orders.length) {
                        returned_orders.forEach(function(o) {
                            o.lines.forEach(function(line_id) {
                                var line = self.env.pos.db.line_by_id[line_id];
                                var product = self.env.pos.db.get_product_by_id(
                                    line.product_id[0]
                                );

                                var exist_product = _.find(products, function(r) {
                                    return r.id === product.id;
                                });
                                if (exist_product) {
                                    exist_product.max_return_qty += line.qty;
                                } else {
                                    product.max_return_qty = line.qty;
                                    if (line.price_unit !== product.price) {
                                        product.old_price = line.price_unit;
                                    }
                                    products.push(product);
                                }
                            });
                        });
                    }
                    // Update max qty for current return order
                    order.return_lines.forEach(function(line) {
                        var product = self.env.pos.db.get_product_by_id(line.product_id[0]);
                        var exist_product = _.find(products, function(r) {
                            return r.id === product.id;
                        });
                        if (exist_product) {
                            exist_product.max_return_qty += line.qty;
                        } else {
                            product.max_return_qty = line.qty;
                            if (line.price_unit !== product.price) {
                                product.old_price = line.price_unit;
                            }
                            products.push(product);
                        }
                    });
                    //if (products.length) {
                        //this.product_list_widget.set_product_list(products);
                        //this.get_product_order_history_return(products);
                    //    this.showScreen('ProductScreen');
                    //}
                }


            }*/
            ///



            click_return_order_by_id(id) {
                ////console.log("click_return_order_by_id",id,this);
                var self = this;
                var current_order = self.env.pos.get_order();
                var order = self.env.pos.db.orders_history_by_id[id];
                var uid =
                    order.pos_reference &&
                    order.pos_reference.match(/\d{1,}-\d{1,}-\d{1,}/g) &&
                    order.pos_reference.match(/\d{1,}-\d{1,}-\d{1,}/g)[0] ||
                    order.pos_reference.match(/\d{1,}-\d{1,}-[A-Z]\d{1,}/g)[0];
                var split_sequence_number = uid.split("-");
                var sequence_number =
                    split_sequence_number[split_sequence_number.length - 1];

                var orders = this.env.pos.get("orders").models;
                //console.log("orders=",orders)
                var exist_order = _.find(orders, function(o) {
                    return (
                        (
                            (o.uid === uid &&
                            Number(o.sequence_number) === Number(sequence_number))
                            ||
                            (o.returned_order_id === id)
                        )
                    );
                });
                if (exist_order && 1===1) {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("Warning"),
                        body: this.env._t("You have an unfinished return '" + exist_order.name + " 'of the order '" + order.pos_reference + " '. Please complete the return of the order and try again."),
                    });
                    return false;
                }

                var lines = [];
                order.lines.forEach(function(line_id) {
                    lines.push(self.env.pos.db.line_by_id[line_id]);
                });
                //extra
                var all_returned = true;
                //
                //var product_list_widget = this.env.pos.chrome.screens.products
                //    .product_list_widget;

                var products = [];
                //hided
                var current_products_qty_sum = 0;
                lines.forEach(function(line) {
                    var product = self.env.pos.db.get_product_by_id(line.product_id[0]);
                    ////console.log("product0000",product);
                    /*var exist_product = _.find(products, function(r) {
                        return r.id === product.id;
                    });
                    //console.log("exist_product",exist_product);
                    if (exist_product) {
                        exist_product.max_return_qty += line.qty;
                    } else {
                        product.max_return_qty = line.qty;
                        if (line.price_unit !== product.price) {
                            product.old_price = line.price_unit;
                        }
                    }*/
                    //if (product){
                    if (line.price_unit !== product.price) {
                        product.old_price = line.price_unit;
                    }
                    //hided
                    current_products_qty_sum += line.qty;
                    products.push(product);
                    //extra
                    if (line.qty > 0)
                        all_returned = false;
                    //
                    //}

                });
                //extra
                if (all_returned) {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("Nothing to return"),
                        body: this.env._t("This order is a fully returned one !"),
                    });
                    return false;
                }


                //
                //hided
                /*
                var returned_orders = this.env.pos.get_returned_orders_by_order(
                    order.pos_reference,order
                );
                console.log("returned_orders",returned_orders);
                var exist_products_qty_sum = 0;
                returned_orders.forEach(function(o) {
                    o.lines.forEach(function(line_id) {
                        var line = self.env.pos.db.line_by_id[line_id];
                        console.log("line",line);
                        exist_products_qty_sum += line.qty;
                    });
                });
                console.log("exist_products_qty_sum + current_products_qty_sum",exist_products_qty_sum,current_products_qty_sum);
                if (exist_products_qty_sum + current_products_qty_sum <= 0) {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("Nothing to return"),
                        body: this.env._t("All products have been returned."),
                    });
                    return false;
                }
                */


                //
                /*// Update max qty for current return order
                //console.log("orderoooo",order,current_order);
                current_order.return_lines.forEach(function(line) {
                    var product = self.env.pos.db.get_product_by_id(line.product_id[0]);
                    var exist_product = _.find(products, function(r) {
                        return r.id === product.id;
                    });
                    if (exist_product) {
                        exist_product.max_return_qty += line.qty;
                    } else {
                        product.max_return_qty = line.qty;
                        if (line.price_unit !== product.price) {
                            product.old_price = line.price_unit;
                        }
                        products.push(product);
                    }
                });*/



                if (products.length > 0)
                {
                    // Create new order for return
                    if (!exist_order)
                    {
                        var json = _.extend({}, order);
                        // extra
                        json.returned_order_id = order.id;
                        //
                        // hided
                        //json.uid = uid;
                        //json.sequence_number = Number(sequence_number);

                        //extra kpl
                        json.state = "draft";

                        json.lines = [];
                        json.statement_ids = [];
                        json.mode = "return";
                        json.return_lines = lines;
                        if (order.pricelist_id) {
                            json.pricelist_id = order.pricelist_id[0];
                        }else {
                            json.pricelist_id = this.env.pos.default_pricelist.id;
                        }
                        if (order.table_id) {
                            json.table_id = order.table_id[0];
                        }
                        // fkp extra 24 jun 2023
                        //console.log("json=",json)
                        if (json.partner_id)
                            json.partner_id = json.partner_id[0];
                        //
                        var options = _.extend({pos: this.env.pos}, {json: json});
                        order = new models.Order({}, options);
                        order.temporary = true;
                    }
                    else
                        order = exist_order;
                    var partner_id = order.partner_id || false;
                    var client = null;
                    if (partner_id) {
                        client = this.env.pos.db.get_partner_by_id(partner_id[0]);
                        if (!client) {
                            console.error(
                                "ERROR: trying to load a partner not available in the pos. order Return"
                            );
                        }
                    }
                    order.set_client(client);
                    //this.renderElement();
                    if (!exist_order)
                        this.env.pos.get("orders").add(order);
                    else
                    {
                        //to do
                        //order.set_screen_data({ name: 'ProductScreen' });
                        var curr_screen_name = order.get_screen_data();
                    }
                    //this.pos.gui.show_screen("products");
                    //self.gui.show_screen("products");
                    //this.showScreen('ProductScreen');

                    this.trigger('close-temp-screen');
                    if (order.table)
                    {
                        this.env.pos.set_table(order.table);
                    }
                    ////console.log("order0000",order,products);
                    this.env.pos.set_order(order);
                    //product_list_widget.set_product_list(products);
                    //this.pos.chrome.widget.order_selector.renderElement();
                    //this.trigger('click-product', products);
                }
                else {
                    //this.env.pos.gui.show_popup("error", _t("Order Is Empty"));
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("Order Is Empty")
                    });
                }

                //this.showScreen('ProductScreen');
                //this.currentOrder.finalize();
                //const { name, props } = this.nextScreen;
                ////console.log("name, props",name, props);
                //this.showScreen(name, props);
                //this.trigger('close-temp-screen');
            }

            get_orders_by_filter(filter, orders) {
                if (filter === "rtn") {
                    return orders.filter(function(order) {
                        return order.returned_order_id || order.returned_order;
                    });
                }
                //return this._super(filter, orders);
                return super.get_orders_by_filter(...arguments);
            }
            return_no_receipt(e) {
                var self = this;
                var options = _.extend({pos: self.env.pos}, {});
                var order = new models.Order({}, options);
                order.temporary = true;
                order.set_mode("return_without_receipt");
                order.return_lines = [];
                self.env.pos.get("orders").add(order);
                //self.pos.gui.back();
                this.trigger('close-temp-screen');
                self.env.pos.set_order(order);
            }

        };

    Registries.Component.extend(OrdersHistoryScreenWidget, OrdersHistoryScreenWidgetReturn);

    return OrdersHistoryScreenWidget;




});

/*

odoo.define('pos_orders_history_reprint.OrdersHistory', function(require) {
    'use strict';
    const { debounce } = owl.utils;
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const OrdersHistory = require('pos_orders_history.OrdersHistory');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var _t = core._t;
    var dom = require('web.dom');
    var QWeb = core.qweb;

    const OrdersHistoryReprint = (OrdersHistory) =>
        class extends OrdersHistory {
            constructor() {
                super(...arguments);
                //console.log("constructor_22222222");
                useListener('button-reprint', () => this.reprintPosOrder());

            }
            button_reprint() {
                //console.log("button_reprinttttttt");
            }
            async reprintPosOrder() {
                var self = this;
                //console.log("button_reprinttttttt00");
                this.showScreen('PrintReportScreen');
            }

        };

    Registries.Component.extend(OrdersHistory, OrdersHistoryReprint);

    return OrdersHistory;
});
*/