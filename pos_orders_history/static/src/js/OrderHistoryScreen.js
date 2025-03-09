odoo.define('pos_orders_history.OrdersHistoryScreenWidget', function(require) {
    'use strict';

    const { debounce } = owl.utils;
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    var rpc = require('web.rpc');
    var core = require('web.core');
    var _t = core._t;
    var dom = require('web.dom');
    var QWeb = core.qweb;


    class OrdersHistoryScreenWidget extends PosComponent {
        constructor() {
            //console.log('constructor_000');
            super(...arguments);
            //this.orders_history_cache = dom;

            this.filters = [];
            this.selected_order = false;
            this._showOrderHistory();
            this.subscribe();


        }
        mounted() {
            this._showOrderHistory();

        }
        __showPosOrderHistory() {
            console.log("showPosOrderHistory-1");
            var self = this;
            var search_timeout = null;
            $(".searchbox input").on("keypress", function(event) {
                clearTimeout(search_timeout);
                var query = this.value;
                search_timeout = setTimeout(function() {
                    self.perform_search(query, event.which === 13);
                }, 70);
            });
            $('.searchbox .search-clear').click(function(){
                self.clear_search();
            });
            //self.update_history()
        }

        //auto_back: true,
        subscribe() {
            //console.log('subscribe_000');
            var subscriber = {
                context: this,
                callback: this.recieve_updates,
            };
            this.env.pos.add_subscriber(subscriber);
        }
        _showOrderHistory() {
            console.log('_showOrderHistory-1');
            var self = this;
            this.clear_list_widget();
            //console.log('_showOrderHistory-2');
            var orders = this.env.pos.db.get_sorted_orders_history(1000);
            //extra
            //this.env.pos.manual_update_order_history(1).then(function() {
            //    orders = this.env.pos.db.get_sorted_orders_history(1000);

            //});
            orders = this.env.pos.db.get_sorted_orders_history(1000);
            //console.log('_showOrderHistory-3');
            this.render_list(orders);
            //console.log('_showOrderHistory-4');
            $("#order_list_contents").delegate(".order-line td", "click", function(
                event
            ) {
                event.stopImmediatePropagation();
                if ($(this).hasClass("actions")) {
                    return false;
                }
                var parent = $(this).parent();
                self.line_select(event, parent, parseInt(parent.data("id"), 10));
            });
            //console.log('_showOrderHistory-5');
        }

        async load_order_by_barcode(barcode) {
            //console.log('load_order_by_barcode_000');
            var self = this;
            var flag_no_order = false
            rpc.query({
                model: "pos.order",
                method: "search_read",
                args: [[["pos_history_reference_uid", "=", barcode]]],
            }, {async: false}).then(
                function(o) {
                    if (o && o.length) {
                        self.env.pos.update_orders_history(o);
                        if (o instanceof Array) {
                            o = o[0];
                        }
                        self.env.pos
                            .get_order_history_lines_by_order_id(o.id)
                            .then(function(lines) {
                                self.env.pos.update_orders_history_lines(lines);
                                self.search_order_on_history(o);
                            });
                    } else {
                        flag_no_order = true;
                        self.print_msg_popup(flag_no_order);
                    }
                },
                function(err, event) {
                    event.preventDefault();
                    console.error(err);
                    //this.showPopup("ErrorPopup", {
                    //    title: this.env._t("Error: Could not find the Order"),
                    //    body: err.data,
                    //});
                    flag_no_order = true;
                    self.print_msg_popup(flag_no_order);
                }

            );
        }
        async confirm_barcode(barcode) {
            //console.log('confirm_barcode_000',barcode);
            var self = this;
            if (barcode) {
                await this.load_order_by_barcode(barcode);
            } else {
                await this.showPopup("ErrorPopup", {
                    title: this.env._t("No Barcode"),

                });
            }
        }
        print_msg_popup(flag_no_order) {
            //console.log("print_msg_popup11",flag_no_order);
            if(flag_no_order == true) {
                this.showPopup("ErrorPopup", {
                    title: this.env._t("Error: Could not find the Order"),
                    body: this.env._t("There is no order with this barcode."),
                });
            }
        }
        clear_list_widget() {
            //console.log('clear_list_widget_000');
            $(".order-line").removeClass("active");
            $(".order-line").removeClass("highlight");
            $(".line-element-container").addClass("line-element-hidden");
        }
        get showbutton() {
            return 'oe_hidden';
        }
        render_list(orders) {
            console.log('render_list-1');
            var contents = $("#order_list_contents");
            $("#order_list_contents").empty();
            contents.innerHTML = "";
            for (var i = 0, len = Math.min(orders.length, 1000); i < len; i++) {
                var order = orders[i];
                var orderline_html = QWeb.render("OrderHistory", {
                    widget: this,
                    order: order,
                });
                var orderline = document.createElement("tbody");

                var lines_table = document.createElement("tr");
                var $td = document.createElement("td");
                if (order.lines) {
                    $td.setAttribute("colspan", 7);
                }
                lines_table.classList.add("line-element-hidden");
                lines_table.classList.add("line-element-container");
                var line_data = this.get_order_line_data(order);
                var $table = this.render_lines_table(line_data);
                $td.append($table);
                lines_table.append($td);

                orderline.innerHTML = orderline_html;
                orderline = orderline.childNodes[1];

                contents.append(orderline);
                contents.append(lines_table);
            }
            //console.log('render_list-2');
        }
        change_filter(filter_name, filter) {
            //console.log('change_filter_000',filter);
            if (filter.hasClass("active")) {
                filter.removeClass("active");
                this.remove_active_filter(filter_name);
            } else {
                filter.addClass("active");
                this.set_active_filter(filter_name);
            }
            this.apply_filters();
        }
        remove_active_filter(name) {
            //console.log('remove_active_filter_000',this);
            this.filters.splice(this.filters.indexOf(name), 1);
        }
        set_active_filter(name) {
            //console.log('set_active_filter_000');
            this.filters.push(name);
        }
        apply_filters() {
            //console.log('apply_filters_000');
            var self = this;
            var orders = this.env.pos.db.get_sorted_orders_history(1000);
            this.filters.forEach(function(filter) {
                orders = self.get_orders_by_filter(filter, orders);
            });
            this.render_list(orders);
        }
        get_orders_by_filter(filter, orders) {
            //console.log('get_orders_by_filter_000',filter, orders);
            var self = this;
            //extra
            var today = new Date();
    		var dd = String(today.getDate()).padStart(2, '0');
    		var mm = String(today.getMonth()).padStart(2, '0'); //January is 0!
    		var yyyy = today.getFullYear();
    		today = new Date(yyyy,mm,dd);
    		var today_end = new Date(yyyy,mm,dd,23,59,59);

            if (filter === "user") {
                var cashier = this.env.pos.get_cashier();
                var user_id =
                    (cashier && cashier.user_id && cashier.user_id[0]) ||
                    this.env.pos.user.id;
                return orders.filter(function(order) {
                    return order.user_id[0] === user_id;
                });
            } else if (filter === "pos") {
                return orders.filter(function(order) {
                    return order.config_id[0] === self.env.pos.config.id;
                });
            } else if (filter === "table") {
                if (this.pos.table) {
                    return orders.filter(function(order) {
                        return order.table_id[0] === self.env.pos.table.id;
                    });
                }
                return orders.filter(function(order) {
                    return !order.table_id;
                });
            } else if (filter === "today") {
                return orders.filter(function(order) {
                	var order_date = new Date(order.date_order);
                	order_date.setHours(order_date.getHours() + 3 );
                    return order_date >= today && order_date <= today_end;
                });
            }

        }
        get_datetime_format(datetime) {
            //console.log('get_datetime_format_000');
            var d = new Date(datetime);
            return new Date(
                d.getTime() - d.getTimezoneOffset() * 60000
            ).toLocaleString();
        }
        clear_search() {
            //console.log('clear_search_000');
            var orders = this.env.pos.db.pos_orders_history;
            this.render_list(orders);
            $(".searchbox input")[0].value = "";
            $(".searchbox input").focus();
        }
        line_select(event, $line, id) {
            //console.log('line_select_000');
            $(".order-line")
                .not($line)
                .removeClass("active");
            $(".order-line")
                .not($line)
                .removeClass("highlight");
            $(".line-element-container").addClass("line-element-hidden");
            if ($line.hasClass("active")) {
                $line.removeClass("active");
                $line.removeClass("highlight");
                this.hide_order_details($line);
                this.selected_order = false;
            } else {
                $line.addClass("active");
                $line.addClass("highlight");
                this.show_order_details($line);
                // Var y = event.pageY - $line.parent().offset().top;
                this.selected_order = this.env.pos.db.orders_history_by_id[id];
            }
        }
        get_order_line_data(order) {
            //console.log('get_order_line_data_000');
            var self = this;
            return _.map(order.lines, function(id) {
                var line = self.env.pos.db.line_by_id[id];
                line.image = self.get_product_image_url(line.product_id[0]);
                return line;
            });
        }
        render_lines_table(data_lines) {
            //console.log('render_lines_table_000');
            var $table = document.createElement("table"),
                $header = this.render_header(),
                $tableData = this.render_product_lines(data_lines);

            $table.classList.add("lines-table");

            $table.appendChild($header);
            $table.appendChild($tableData);
            return $table;
        }
        get_product_image_url(product_id) {
            //console.log('get_product_image_url_000');
            return (
                window.location.origin +
                "/web/image?model=product.product&field=image_128&id=" +
                product_id
            );
        }
        render_header() {
            //console.log('render_header_000');
            var $header = document.createElement("thead");
            $header.innerHTML = QWeb.render("LinesHeader");
            return $header;
        }
        render_product_lines(data_lines) {
            //console.log('render_product_lines_000',data_lines);
            var $body = document.createElement("tbody"),
                lines = "",
                line_html = "";
            for (var i = 0, max = data_lines.length; i < max; i++) {
                line_html = QWeb.render("LineHistory", {
                    widget: this,
                    line: data_lines[i],
                });
                lines += line_html;
            }
            $body.innerHTML = lines;
            return $body;
        }
        hide_order_details($line) {
            //console.log('hide_order_details_000');
            $line.next().addClass("line-element-hidden");
        }
        show_order_details($line) {
            //console.log('show_order_details_000');
            $line.next().removeClass("line-element-hidden");
        }
        recieve_updates(action, ids) {
            console.log('recieve_updates-1');
            switch (action) {
                case "update":
                    this.update_list_items(ids);
                    break;
                default:
                    break;
            }
        }
        update_list_items(ids) {
            console.log('update_list_items-1');
            var self = this;
            _.each(ids, function(id) {
                var $el = $(".order-list").find("[data-id=" + id + "]");
                var data = self.env.pos.db.orders_history_by_id[id];
                var selected = false;
                if ($el.length === 0 || !data) {
                    return;
                }
                var new_el_html = QWeb.render("OrderHistory", {
                    widget: self,
                    order: data,
                });
                if ($el.hasClass("active")) {
                    selected = true;
                }
                var orderline = document.createElement("tbody");
                orderline.innerHTML = new_el_html;
                orderline = orderline.childNodes[1];
                $el.replaceWith(orderline);
                //self.orders_history_cache.clear_node(id);
                //self.orders_history_cache.cache_node(id, orderline);
                if (selected) {
                    orderline.classList.add("active", "highlight");
                }
            });
        }
        perform_search(query, associate_result) {
            //console.log('perform_search_000');
            var orders = false;
            if (query) {
                orders = this.env.pos.db.search_order(query);
                this.render_list(orders);
            } else {
                orders = this.env.pos.db.pos_orders_history;
                this.render_list(orders);
            }
        }
        search_order_on_history(order) {
            //console.log('search_order_on_history_000');
            this.__showPosOrderHistory();
            $(".searchbox input").val(order.pos_reference);
            $(".searchbox input").keypress();
        }
        back() {
            //console.log("backkkkk");
            //this.trigger('close-temp-screen');
            this.showScreen('ProductScreen');
        }
        user_filter(e) {
            //console.log("user_filtereeeeeee",e);
            e.stopImmediatePropagation();
            this.change_filter("user", $('#user-filter'));
        }
        pos_filter(e) {
            //console.log("pos_filtereeeeeee",e);
            e.stopImmediatePropagation();
            this.change_filter("pos", $('#pos-filter'));
        }
        today_filter(e) {
            //console.log("today_filtereeeeeee",e);
            e.stopImmediatePropagation();
            this.change_filter("today", $('#today-filter'));

        }
        async scan_barcode(e) {
            //console.log("scan_barcodeeeeeee",e);
            const { confirmed, payload: newName } = await this.showPopup('TextInputPopup', {
                title: this.env._t('Enter or Scan barcode'),
            });
            if (confirmed) {
                await this.confirm_barcode(newName);
            }
            //this.env.pos.barcode_reader.restore_callbacks();

        }
        update_history(e) {
            console.log("update_history-1");
            var self = this;
            var orders = this.env.pos.db.pos_orders_history;
            //self.env.pos.manual_update_order_history().then(function() {
            //    orders = self.pos.db.get_sorted_orders_history(1000);
            //    self.render_list(orders);
            //});

            //self.env.pos.manual_update_order_history();
            self.env.pos.get_order_histories(1000).then(function(orders) {
                self.env.pos.update_orders_history(orders);
                self.env.pos.get_order_lines(_.pluck(orders, 'id')).then(function(lines){
                    self.env.pos.update_orders_history_lines(lines);
                });
                self._showOrderHistory();
            });

            //orders = self.env.pos.db.get_sorted_orders_history(1000);
            //this.render_list(orders);
            $('#pos-filter').removeClass("active");
            $('#user-filter').removeClass("active");
            $('#today-filter').removeClass("active");
            this.clear_search();
            this.showPopup("ErrorPopup", {
                title: this.env._t("Update List:"),
                body: this.env._t("Process completed"),
            });

        }


    }
    OrdersHistoryScreenWidget.template = 'OrdersHistoryScreenWidget';

    Registries.Component.add(OrdersHistoryScreenWidget);

    return OrdersHistoryScreenWidget;
});
/*
odoo.define('pos_order_history.OrdersHistoryButton', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class OrdersHistoryButton extends PosComponent {
        constructor() {
            //console.log("OrdersHistoryButton-constructor");
            super(...arguments);
            useListener('click', this.onClick);
        }

        onClick() {
            //console.log("OrdersHistoryButton-onClick");
            //await this.showTempScreen('OrdersHistoryScreenWidget');
            this.showScreen('OrdersHistoryScreenWidget');

        }
    }
    OrdersHistoryButton.template = 'OrdersHistoryButton';

    ProductScreen.addControlButton({
        component: OrdersHistoryButton,
        condition: function() {
            return this.env.pos.config.orders_history;
        },
    });

    Registries.Component.add(OrdersHistoryButton);

    return OrdersHistoryButton;
});
*/