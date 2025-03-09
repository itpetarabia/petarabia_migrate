odoo.define('pos_restrict_pricelist.SetPricelistButton', function (require) {
"use strict";

    const SetPricelistButton = require('point_of_sale.SetPricelistButton');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

   const PosSetPricelistButton = SetPricelistButton =>
        class extends SetPricelistButton {

        async onClick() {
            const cashier = this.env.pos.get_cashier();
            console.log("cashier", cashier)
            if (cashier.role == "cashier") {
            await this.showPopup("ErrorPopup", {
                            title: this.env._t("Warning"),
                            body: this.env._t(
                                "Cashier Not Allowed To Change the Customer Pricelist" ),

                        });
                        return;
            }
             await super.onClick();
        }
    };

   Registries.Component.extend(SetPricelistButton, PosSetPricelistButton);


    return SetPricelistButton;

});
