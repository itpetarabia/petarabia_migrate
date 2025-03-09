/* Copyright 2017-2018 Dinar Gabbasov <https://it-projects.info/team/GabbasovDinar>
 * Copyright 2018 Artem Losev
 * Copyright 2018 Kolushov Alexandr <https://it-projects.info/team/KolushovAlexandr>
 * License MIT (https://opensource.org/licenses/MIT). */
odoo.define("pos_orders_history.models", function(require) {
    "use strict";
    var models = require("point_of_sale.models");
    var rpc = require("web.rpc");

    var _super_pos_model = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function() {
            //console.log("initialize00000");
            _super_pos_model.initialize.apply(this, arguments);
            var self = this;
            this.ready.then(function() {
                self.bus.add_channel_callback(
                    "pos_orders_history",
                    self.on_orders_history_updates,
                    self
                );
            });
            this.subscribers = [];

        },
        add_subscriber: function(subscriber) {
            //console.log("add_subscriber000000");
            this.subscribers.push(subscriber);

        },



        //extra
        get_order_history_domain: function() {
            console.log("get_order_history_domain");
        	var self = this;
        	var domain = [];
        	/////var states = self.get_order_history_domain_states();
        	//if(!self.config.show_other_pos_orders)
            //{
            //	domain.push(['config_id','=',self.config.id]);
            //}
        	// State of orders
            var state = ["paid"];
            if (this.config.show_cancelled_orders) {
                state.push("cancel");
            }
            if (this.config.show_posted_orders) {
                state.push("done");
            }
            if(self.config.show_returned_orders == false)
        	{
            	domain.push(['returned_order','=',false]);
        	}
            // Number of orders
            if (this.config.load_orders_of_last_n_days) {
                var today = new Date();
                today.setHours(0, 0, 0, 0);
                // Load orders from the last date
                var last_date = new Date(
                    today.setDate(today.getDate() - this.config.number_of_days)
                ).toISOString();
                domain.push(["date_order", ">=", last_date]);
            }
            //console.log("state",state)
            domain.push(["state", "in", state]);
            return domain;
        },

        manual_update_order_history: function(limit=1000) {
            console.log("manual_update_order_history-1");
            var self = this;
            //var def = new $.Deferred();
            var def = new $.Deferred();
            //console.log("manual_update_order_history-2");
            this.get_order_histories(limit).then(function(orders) {
            	//console.log("Update orders = ",limit,orders);
                if (!orders) {
                    def.resolve();
                    return;
                }
                //console.log("manual_update_order_history-3");
                self.update_orders_history(orders);
                //console.log("manual_update_order_history-4",orders);
                self.get_order_lines(_.pluck(orders, 'id')).then(function(lines){
                    //console.log("manual_update_order_history-5");
                    self.update_orders_history_lines(lines);
                    //console.log("manual_update_order_history-6",def);
                    //def.resolve();
                });
                //console.log("manual_update_order_history-7");

            });
            //console.log("manual_update_order_history-8");
            return def;
        },
        get_order_histories: function(limit) {
            console.log("get_order_histories");
            var self = this;
        	var domain = function(self) {
            	var domain = self.get_order_history_domain();
            	return domain;
        	}
        	//console.log("get_order_histories-2",domain(this))
        	return rpc.query({
                model: 'pos.order',
                method: 'search_read',
                args: [domain(this),null,null,limit,null]
            });
        },

        get_order_lines: function(order_ids) {
        	console.log('get_order_lines');
            return rpc.query({
                model: 'pos.order.line',
                method: 'search_read',
                args: [[['order_id','in',order_ids]]]
            });
        },

        //


        on_orders_history_updates: function(message) {
            console.log("on_orders_history_updates-1");
            var self = this;
            //extra
        	//if(!self.config.show_other_pos_orders && message.config_id != self.config.id)
        	//	return;
        	//
            // State of orders
            var state = ["paid"];
            if (this.config.show_cancelled_orders) {
                state.push("cancel");
            }
            if (this.config.show_posted_orders) {
                state.push("done");
            }
            message.updated_orders.forEach(function(id) {
                self.get_order_history(id).then(function(order) {
                    if (order instanceof Array) {
                        order = order[0];
                    }
                    if (state.indexOf(order.state) !== -1) {
                        self.update_orders_history(order);
                    }
                });
                self.get_order_history_lines_by_order_id(id).then(function(lines) {
                    self.update_orders_history_lines(lines);
                });
            });
            //console.log("on_orders_history_updates-2");
        },
        get_order_history: function(id) {
            console.log("get_order_history-1",id);
            return rpc.query({
                model: "pos.order",
                method: "search_read",
                args: [[["id", "=", id]]],
            });
        },
        get_order_history_lines_by_order_id: function(id) {
            console.log("get_order_history_lines_by_order_id-1");
            return rpc.query({
                model: "pos.order.line",
                method: "search_read",
                args: [[["order_id", "=", id]]],
            });
        },
        update_orders_history: function(orders) {
            console.log("update_orders_history-1");
            var self = this,
                orders_to_update = [];
            if (!(orders instanceof Array)) {
                orders = [orders];
            }
            //console.log("update_orders_history-2");
            if (this.db.pos_orders_history.length !== 0) {
                _.each(orders, function(updated_order) {
                    var max = self.db.pos_orders_history.length;
                    for (var i = 0; i < max; i++) {
                        if (updated_order.id === self.db.pos_orders_history[i].id) {
                            self.db.pos_orders_history.splice(i, 1);
                            delete self.db.orders_history_by_id[updated_order.id];
                            orders_to_update.push(updated_order.id);
                            break;
                        }
                    }
                });
            }
            //console.log("update_orders_history-3");
            var all_orders = this.db.pos_orders_history.concat(orders);
            //console.log("update_orders_history-4",all_orders,orders);
            this.db.pos_orders_history = all_orders;
            //console.log("update_orders_history-5");
            this.db.sorted_orders_history(all_orders);
            //console.log("update_orders_history-6");
            all_orders.forEach(function(current_order) {
                self.db.orders_history_by_id[current_order.id] = current_order;
            });
            //console.log("update_orders_history-7");
            this.publish_db_updates(orders_to_update);
            //console.log("update_orders_history-8");
        },
        publish_db_updates: function(ids) {
            //console.log("publish_db_updates00000");
            _.each(this.subscribers, function(subscriber) {
                var callback = subscriber.callback,
                    context = subscriber.context;
                callback.call(context, "update", ids);
            });
        },
        update_orders_history_lines: function(lines) {
            console.log("update_orders_history_lines-1");
            var self = this;
            var all_lines = this.db.pos_orders_history_lines.concat(lines);
            //console.log("update_orders_history_lines-2");
            this.db.pos_orders_history_lines = all_lines;
            //console.log("update_orders_history_lines-3");
            all_lines.forEach(function(line) {
                self.db.line_by_id[line.id] = line;
            });
            //console.log("update_orders_history_lines-4");
        },
        get_date: function() {
            //console.log("get_date0000");
            var currentdate = new Date();
            var year = currentdate.getFullYear();
            var month = currentdate.getMonth() + 1;
            var day = currentdate.getDate();
            if (Math.floor(month / 10) === 0) {
                month = "0" + month;
            }
            if (Math.floor(day / 10) === 0) {
                day = "0" + day;
            }
            return year + "-" + month + "-" + day;
        },

    });

    var _super_order_model = models.Order.prototype;
    models.Order = models.Order.extend({
        set_mode: function(mode) {
            this.mode = mode;
        },
        get_mode: function() {
            return this.mode;
        },
        export_as_JSON: function() {
            var data = _super_order_model.export_as_JSON.apply(this, arguments);
            data.mode = this.mode;
            return data;
        },
        init_from_JSON: function(json) {
            this.mode = json.mode;
            _super_order_model.init_from_JSON.call(this, json);
        },
        getOrderReceiptEnv: function() {
            // Formerly get_receipt_render_env defined in ScreenWidget.
            var res = _super_order_model.getOrderReceiptEnv.call(this);
            if (this.pos.config.show_barcode_in_receipt) {
                var order = this.pos.get_order();
                var receipt_reference = order.uid;
                if(receipt_reference){
                    var img = new Image();
                    img.id = "test-order-barcode";
                    $(img).JsBarcode(receipt_reference.toString());
                    res.receipt['pos_order_barcode'] = $(img)[0] ? $(img)[0].src : false;
                }
            }
            return res;
        },
    });

    models.load_models({
        model: "pos.order",
        fields: [],
        domain: function(self) {
            var domain = [];

            // State of orders
            var state = ["paid"];
            if (self.config.show_cancelled_orders) {
                state.push("cancel");
            }
            if (self.config.show_posted_orders) {
                state.push("done");
            }

            domain.push(["state", "in", state]);

            // Number of orders
            if (self.config.load_orders_of_last_n_days) {
                var today = new Date();
                today.setHours(0, 0, 0, 0);
                // Load orders from the last date
                var last_date = new Date(
                    today.setDate(today.getDate() - self.config.number_of_days)
                ).toISOString();
                domain.push(["date_order", ">=", last_date]);
            }

            return domain;
        },
        condition: function(self) {
            return self.config.orders_history && !self.config.load_barcode_order_only;
        },
        loaded: function(self, orders) {
            self.update_orders_history(orders);
            self.order_ids = _.pluck(orders, "id");
        },
    });

    models.load_models({
        model: "pos.order.line",
        fields: [],
        domain: function(self) {
            return [["order_id", "in", self.order_ids]];
        },
        condition: function(self) {
            return self.config.orders_history && !self.config.load_barcode_order_only;
        },
        loaded: function(self, lines) {
            self.update_orders_history_lines(lines);
        },
    });

    return models;
});
