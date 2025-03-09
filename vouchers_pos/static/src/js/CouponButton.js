odoo.define('voucher_pos.CouponButton', function(require) {
'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class CouponButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        async onClick() {

            await this.showPopup('CouponPopup');

        }

    }
    CouponButton.template = 'CouponButton';

    ProductScreen.addControlButton({
        component: CouponButton,
        condition: function() {
            return 1==1;
        },
    });

    Registries.Component.add(CouponButton);

    return CouponButton;
});
