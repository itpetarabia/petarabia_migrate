odoo.define('pos_orders_history_reprint.OrdersHistoryScreenWidget', function(require) {
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

    const OrdersHistoryScreenWidgetReprint = (OrdersHistoryScreenWidget) =>
        class extends OrdersHistoryScreenWidget {
            constructor() {
                //console.log("constructor_11111111123");
                super(...arguments);

            }
            mounted() {
                //console.log("mounted222222");
                //this._showOrderHistory();
                super.mounted(...arguments);
                this._showOrderHistory();
                if (this.env.pos.config.reprint_orders) {
                    this.set_reprint_action();
                }

            }
            set_reprint_action() {
                //console.log("set_reprint_action",this);
                var self = this;
                var $reprint_button = $(".button-reprint");
                $reprint_button.removeClass("oe_hidden");
                $reprint_button.unbind("click");
                $reprint_button.click(function(e) {
                    //console.log("set_reprint_action000",e,self);
                    var order = self.env.pos.get_order()
                    var parent = $(this).parents(".order-line");
                    var id = parseInt(parent.data("id"), 10);
                    //console.log("idddd",id,order);
                    //self.showTempScreen('PrintReportScreen');
                    //self.showTempScreen('PrintReportScreen', { order_id: id });
                    self.showScreen('PrintReportScreen', { order_id: id });

                });
            }

            render_list(orders) {
                var self = this;
                super.render_list(...arguments);

                if (this.env.pos.config.reprint_orders) {
                    this.set_reprint_action();
                }

            }
            get showbutton() {
                return this.env.pos.reprint_orders !== false ? '' : 'oe_hidden';
            }
        };

    Registries.Component.extend(OrdersHistoryScreenWidget, OrdersHistoryScreenWidgetReprint);

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
                console.log("constructor_22222222");
                useListener('button-reprint', () => this.reprintPosOrder());

            }
            button_reprint() {
                console.log("button_reprinttttttt");
            }
            async reprintPosOrder() {
                var self = this;
                console.log("button_reprinttttttt00");
                this.showScreen('PrintReportScreen');
            }

        };

    Registries.Component.extend(OrdersHistory, OrdersHistoryReprint);

    return OrdersHistory;
});
*/