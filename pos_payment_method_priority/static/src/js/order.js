odoo.define('pos_pm_order_by_priority.custom', function (require) {
    "use strict";
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const pos_model = require('point_of_sale.models');

    pos_model.load_fields("pos.payment.method", ["priority"]);
    const UpdatedPaymentScreen = PaymentScreen =>
        class extends PaymentScreen {
            constructor() {
                super(...arguments);
                var payment_methods = this.env.pos.payment_methods.filter(method => this.env.pos.config.payment_method_ids.includes(method.id));
                this.payment_methods_from_config = payment_methods.sort(function (a, b) {
                                                                        return a.priority - b.priority;
                                                                        });
            }
        };
    Registries.Component.extend(PaymentScreen, UpdatedPaymentScreen);



});

// odoo.define('pos_demo.custom', function (require) {
//     "use strict";
//     const PosComponent = require('point_of_sale.PosComponent');
//     const ProductScreen = require('point_of_sale.ProductScreen');
//     const Registries = require('point_of_sale.Registries');

//     return PosLastOrderButton;
// });
