odoo.define('pos_orders_history_reprint.PosReportPrint', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class PosReportPrint extends PosComponent {
        constructor() {
            super(...arguments);
            //this._receiptEnv = this.props.order.getOrderReceiptEnv();
            //this.session_data = {}
            //this.myValueFromRpc = {}
        }
        //get_order: function() {
        //    var order_id = this.gui.get_current_screen_param("order_id");
        //    return this.env.pos.db.orders_history_by_id[order_id];
        //}

        async willStart() {
            this.report_all = await this.report_all();
        }

        /*async report_all() {
            const order = this.env.pos.get_order();
            var env = {
                    widget:self,
                    company: order.pos.company,
                    pos: order.pos,
                    order: order,
                    };
            return env;
        }*/
        async report_all() {
            const order = this.env.pos.get_order();
            console.log("order11",order,this);
            const saleDetails = await this.rpc({
                model: 'report.point_of_sale.report_saledetails',
                method: 'get_pos_saleshistory',
                args: [false,false, this.env.pos.config_id,this.props.order],
            }).then(function(result){

                var env = {
                    disc_amount: result.disc_amount,
                    widget:self,
                    company: order.pos.company,
                    pos: order.pos,
                    products: result.products,
                    payments: result.payments,
                    order_line: result.order_line,
                    taxes: result.taxes,
                    total_amt_with_tax: result.total_amt_with_tax,
                    total_paid: result.total_paid,
                    date: (new Date()).toLocaleString(),
                    pos_name:result.pos_name,
                    cashier_name:result.cashier_name,
                    session_start:result.session_start,
                    session_end:result.session_end,
                    reference: result.reference,
                    amount_return: result.amount_return,
                    amount_round: result.amount_round,

                };
                var receipt_reference = result.uid;
                var pos_order_barcode = '';
                if(receipt_reference){
                    var img = new Image();
                    img.id = "test-order-barcode";
                    $(img).JsBarcode(receipt_reference.toString());
                    pos_order_barcode = $(img)[0] ? $(img)[0].src : false;
                    env['pos_order_barcode'] = pos_order_barcode;
                }
                console.log("env===>", env);
                return env
            });

            return saleDetails;
        }

    }
    
    PosReportPrint.template = 'PosReportPrint';

    Registries.Component.add(PosReportPrint);

    return PosReportPrint;
});



