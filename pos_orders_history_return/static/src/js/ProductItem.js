odoo.define('pos_orders_history_return.ProductItem', function(require) {
    'use strict';
    //console.log("pos_orders_history_return.ProductItem");
    const { useState } = owl.hooks;
    const PosComponent = require('point_of_sale.PosComponent');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const ProductItem = require('point_of_sale.ProductItem');

    const ProductItemOrderReturn = (ProductItem) =>
        class extends ProductItem {
            get return_mode() {
                var order = this.env.pos.get_order();
                var return_mode = false;
                if (order && order.get_mode() === "return") {
                    return_mode = true;
                }
                //console.log("return_mode",return_mode);
                return return_mode
            }
            get price() {
                const formattedUnitPrice = this.env.pos.format_currency(
                    this.props.product.get_price(this.pricelist, 1),
                    'Product Price'
                );
                var order = this.env.pos.get_order();
                if (order && order.get_mode() === "return" && this.props.product.old_price && order.edit_return !== true) {
                    return this.env.pos.format_currency(this.props.product.old_price);
                }else if (this.props.product.to_weight) {
                    return `${formattedUnitPrice}/${
                        this.env.pos.units_by_id[this.props.product.uom_id[0]].name
                    }`;
                } else {
                    return formattedUnitPrice;
                }
            }

        };

    Registries.Component.extend(ProductItem, ProductItemOrderReturn);

    return ProductItem;
});    

