odoo.define('pos_pro_cross_selling.Orderline', function(require) {
    'use strict';

    const Orderline = require('point_of_sale.Orderline');
    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    const { Gui } = require('point_of_sale.Gui');

    const PosCrossSellingOrderline = Orderline =>
        class extends Orderline {
            async cross_selling_button_add() {
                /*//this.trigger('numpad-click-input', { key: 'Backspace' });
                //this.trigger('numpad-click-input', { key: 'Backspace' });
                const product = this.props.line.product;
                const order = this.env.pos.get_order();
                var self = this;
                rpc.query({
                    model: 'pos.order.line',
                    method: 'get_cross_selling_products',
                    args: [[],product.id,order.pricelist.id],
                }).then(await function (result) {
                    if (result.length > 0) {
                        let { confirmed, payload } = Gui.showPopup('CrossProducts', {
                            product: result,
                            title: 'Cross Selling Products',
                        });

                    }
                });
                */
                this.props.line.set_cross_selling(true);

            }
            async cross_selling_button_remove() {
                this.props.line.set_cross_selling(false);
            }
        };

    Registries.Component.extend(Orderline, PosCrossSellingOrderline);

    return Orderline;
});
