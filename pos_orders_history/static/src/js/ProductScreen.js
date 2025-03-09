odoo.define('pos_order_history.ProductScreen', function(require) {
    'use strict';

    const { Gui } = require('point_of_sale.Gui');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');

    const PosHistoryProductScreen = ProductScreen =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                useListener('click-history', this._onClickHistory);
            }
            _onClickHistory() {
                this.showScreen('OrdersHistoryScreenWidget');
            }
        };

    Registries.Component.extend(ProductScreen, PosHistoryProductScreen);

    return ProductScreen;
});
