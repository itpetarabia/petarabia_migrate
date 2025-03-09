odoo.define('pos_fixed_discount.ProductScreen', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useBarcodeReader } = require('point_of_sale.custom_hooks');

    const PosFixedDiscProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);

            }
            _setValue(val) {
                console.log("PosFixedDiscProductScreen");
                if (this.currentOrder.get_selected_orderline()) {
                    if (this.state.numpadMode === 'quantity') {
                        this.currentOrder.get_selected_orderline().set_quantity(val);
                    } else if (this.state.numpadMode === 'discount') {
                        this.currentOrder.get_selected_orderline().set_discount(val);
                    } else if (this.state.numpadMode === 'price') {
                        var selected_orderline = this.currentOrder.get_selected_orderline();
                        selected_orderline.price_manually_set = true;
                        selected_orderline.set_unit_price(val);
                    } else if (this.state.numpadMode === 'discount_fixed'){
                        this.currentOrder.get_selected_orderline().set_discount_fixed(val);
                    }
                    if (this.env.pos.config.iface_customer_facing_display) {
                        this.env.pos.send_current_order_to_customer_facing_display();
                    }
                }
            }

        };

    Registries.Component.extend(ProductScreen, PosFixedDiscProductScreen);

    return ProductScreen;
});
