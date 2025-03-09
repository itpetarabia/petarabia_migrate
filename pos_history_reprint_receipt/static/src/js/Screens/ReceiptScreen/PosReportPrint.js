odoo.define("pos_history_reprint_receipt.PosReportPrint", function (require) {
    "use strict";
    const Registries = require('point_of_sale.Registries');
    const PosReportPrint = require('pos_orders_history_reprint.PosReportPrint');
    const PosReportPrintExtended = (PosReportPrint) =>
        class extends PosReportPrint {
            get receiptFontSize()
            {
                var res =  `font-size:${this.env.pos.config.font_size_receipt || 14}px;`;
                //console.log('receiptFontSize=',res);
                return res;
            }
            get logoStyle()
            {
	 		    var res = `width:${this.env.pos.config.logo_width_receipt}px;height:${this.env.pos.config.logo_height_receipt}px;`;
                return res;
            }
            get logoUrl() {
                //console.log('logoUrl = ',this.env.pos);
                if (this.env.pos && this.env.pos.config.show_logo_receipt)
                {
                    if (this.env.pos.config.logo)
                        return `/web/image?model=pos.config&field=logo&id=${this.env.pos.config_id}&unique=1`;
                    else if (this.env.pos.company.logo)
                        return this.env.pos.company_logo_base64;
                    return false;
                }
                return false;
            }
            //replace function
            async report_all() {
                const order = this.env.pos.get_order();
                /////////
                var company_partner = this.env.pos.db.get_partner_by_id(this.env.pos.company.partner_id[0]);
                var contact_address_full = '';
                if (company_partner)
                    contact_address_full = company_partner.contact_address;

                /////////
                if (this.env.pos.config.iface_tax_included === 'total') {
                    var price_incl = true;
                } else {
                    var price_incl = false;
                }
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
                        contact_address_full: contact_address_full,
                        client: result.client,
                        client_phone: result.client_phone,
                        price_incl: price_incl,
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
                    console.log("env===>22", env);
                    return env
                });

                return saleDetails;
            }

        };
    Registries.Component.extend(PosReportPrint, PosReportPrintExtended);

    //OrderReceipt.template = 'OrderReceiptExtended';

    //Registries.Component.add(OrderReceipt);

    return PosReportPrint;

});
