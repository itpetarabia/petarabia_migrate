/*odoo.define('pos_pro_cross_selling.product_addons', function (require) {
    "use strict";

    const Registries = require('point_of_sale.Registries');
    var rpc = require('web.rpc');
    const { Gui } = require('point_of_sale.Gui');
    const ProductScreen = require('point_of_sale.ProductScreen');
    // Class for pos products
    const PosProductAddons = ProductScreen => class extends ProductScreen {
        constructor() {
            super(...arguments);
        }
        async _clickProduct(event) {
            // Click Function for the products, It opens the pop up
            await super._clickProduct(...arguments)
            const product = event.detail;
            const order = this.currentOrder;
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

        }
    };
    Registries.Component.extend(ProductScreen, PosProductAddons);
    return ProductScreen;
});
*/