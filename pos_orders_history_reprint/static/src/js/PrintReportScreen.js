
odoo.define('pos_orders_history_reprint.PrintReportScreen', function (require) {
    'use strict';

    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');

    const PrintReportScreen = (ReceiptScreen) => {
        class PrintReportScreen extends ReceiptScreen {
            mounted() {
                console.log("thisdddd",this);


            }
            confirm() {
                console.log("thisssss",this);
                //this.props.resolve({ confirmed: true, payload: null });
                //this.trigger('close-temp-screen');
                this.showScreen('OrdersHistoryScreenWidget');
            }
        }
        PrintReportScreen.template = 'PrintReportScreen';
        return PrintReportScreen;
    };

    Registries.Component.addByExtending(PrintReportScreen, ReceiptScreen);

    return PrintReportScreen;
});

