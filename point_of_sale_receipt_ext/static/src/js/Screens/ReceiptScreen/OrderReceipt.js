odoo.define("point_of_sale_receipt_ext.OrderReceipt", function (require) {
    "use strict";
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const OrderReceiptExtended = (OrderReceipt) =>
        class extends OrderReceipt {
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

        };
    Registries.Component.extend(OrderReceipt, OrderReceiptExtended);

    //OrderReceipt.template = 'OrderReceiptExtended';

    //Registries.Component.add(OrderReceipt);

    return OrderReceipt;

});
