odoo.define('pos_stock_alert_notif.DB', function (require) {
"use strict";
var core = require('web.core');
/* The PosDB holds reference to data that is either
 * - static: does not change between pos reloads
 * - persistent : must stay between reloads ( orders )
 */
var PosDB = require('point_of_sale.DB');
//not using
PosDB.include({
    add_products: function(products){
        this._super(products);
        var pos = this.pos;
        if (pos && pos.has_to_check_stock())
        {
            //copy from super
            if(!products instanceof Array)
            {
                products = [products];
            }
            var product_ids_to_update_avail_qty = [];
            for(var i = 0, len = products.length; i < len; i++){
                var product = products[i];
                //console.log("calling has_to_check_stock=",pos.has_to_check_stock(product))
                if (pos.has_to_check_stock(product))
                    product_ids_to_update_avail_qty.push(product.id);
            }
            //console.log("product_ids_to_update_avail_qty=",product_ids_to_update_avail_qty)
            if (product_ids_to_update_avail_qty)
                pos.load_available_qty(product_ids_to_update_avail_qty);
        }
    },
});

});