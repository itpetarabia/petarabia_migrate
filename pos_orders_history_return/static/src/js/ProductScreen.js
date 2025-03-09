odoo.define('pos_orders_history_return.ProductScreen', function(require) {
    'use strict';

    const { Gui } = require('point_of_sale.Gui');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const ProductScreenOrderReturn = ProductScreen =>
        class extends ProductScreen {
            async _onClickCustomer() {
                if (!this.currentOrder.returned_order_id){
                    // IMPROVEMENT: This code snippet is very similar to selectClient of PaymentScreen.
                    const currentClient = this.currentOrder.get_client();
                    //console.log("currentClient",currentClient);
                    //this.showScreen('ClientListScreen');
                    const { confirmed, payload: newClient } = await this.showTempScreen(
                        'ClientListScreen',
                        { client: currentClient }
                    );
                    //console.log('newClient',newClient);
                    if (confirmed) {
                        this.currentOrder.set_client(newClient);
                        this.currentOrder.updatePricelist(newClient);

                    }
                }

            }

        };

    Registries.Component.extend(ProductScreen, ProductScreenOrderReturn);

    return ProductScreen;
});
