odoo.define('pos_stock_alert_notif.models', function (require) {
    "use strict";

var models = require('point_of_sale.models');
var posmodel_super = models.PosModel.prototype;
const NumberBuffer = require('point_of_sale.NumberBuffer');
var { Gui } = require('point_of_sale.Gui');
var core = require('web.core');
var _t = core._t;
var utils = require('web.utils');
var field_utils = require('web.field_utils');
var round_di = utils.round_decimals;
var round_pr = utils.round_precision;

models.load_fields("product.product", ['type']);
/*
models.load_models([{
    model: 'stock.production.lot',
    label: 'Lots/Serial Numbers',
    condition: function (self) { return self.has_to_check_stock() && !self.config.load_stock_background },
    domain: function(self){
        return [['product_id.type','=','product'],['product_id.available_in_pos','=',true]
        //,['product_id','in',Object.keys(self.db.product_by_id).map(Number)]
        ];
    },
    fields: ['name','id','product_id'],
    loaded: function(self,lines){
        _.each(lines, function(line){
            if (self.lots_by_product_id[line.product_id[0]] === undefined)
                self.lots_by_product_id[line.product_id[0]] = [];
            self.lots_by_product_id[line.product_id[0]].push(line);
            self.lots_by_id[line.id] = line;

        });
        ////////////////console.log.log((("self.lots_by_product_id=",self.lots_by_product_id)
    },
}],{'before': 'product.product'});
*/
/*
models.Product = models.Product.extend({
    format_float_value: function(val) {
        var value = parseFloat(val);
        value = field_utils.format.float(value, {digits: [69, 3]});
        return String(parseFloat(value));
    },
    rounded_qty: function() {
        return this.format_float_value(this.qty_available);
    },
});
*/
models.PosModel = models.PosModel.extend({
    initialize: function (attributes) {
        this.lots_by_product_id= {};
        this.lots_by_id = {};
        return posmodel_super.initialize.call(this, attributes);
    },
    has_to_check_stock: function()
    {
        if (this.config.default_location_src_id.length > 0 && this.config.out_stock_alert)
            return true;
        return false;
    },
    get_product_lot_id_by_name: function (product,lot_name)
    {
        var lot_id = false;
        for (var i = 0; i < (this.lots_by_product_id[product.id] || []).length; i++)
        {
            var lot_det = this.lots_by_product_id[product.id][i]
            if (lot_det.name === lot_name)
            {
                lot_id = lot_det.id;
                break;
            }
        }
        return lot_id;
    },
    has_to_check_product_stock: function (product)
    {
        if (product.type === 'product' && this.has_to_check_stock())
            return true;
        return false;
    },
    validate_product_stock: async function(product, qty_info_args={},operation='',extras={})
    {
        var self = this;
        var order = self.get_order();
        var qty_info = order.get_product_total_qty(qty_info_args);
        if ((qty_info.total_qty || 0) > 0 && product && this.has_to_check_product_stock(product) && 1===1)
        {
            //product = self.db.get_product_by_id(product.id)
            var decimals = this.dp['Product Unit of Measure'],
            unit = product.get_unit(), lot_name,lot_name_display, qty_available, qty_required, qty_availableStr, qty_requiredStr,
            rounding, out_stock_msg;
            //try to update stock
            var fetch_stock_lot_ids = [];
            var fetch_stock_lot_names = [];
            for (let k in qty_info)
            {
                if (k !== 'total_qty')
                {
                    //case of lot or unknown lots
                    if (String(k).includes('mt_unk_lot'))
                        fetch_stock_lot_names.push(String(k).split('mt_unk_lot_')[1] || '');
                    else
                        fetch_stock_lot_ids.push(k);
                }
            }
            ////console.log.log("fetch_stock_lot_ids=",fetch_stock_lot_ids)
            var fetch_stock = true;
            if (fetch_stock_lot_ids.length > 0 || fetch_stock_lot_names.length > 0)
                fetch_stock = await self.load_and_update_stock([product.id],self.config.default_location_src_id[0],fetch_stock_lot_ids,fetch_stock_lot_names,true);
            else
                fetch_stock = await self.load_and_update_stock([product.id],self.config.default_location_src_id[0],fetch_stock_lot_ids,fetch_stock_lot_names,false);
            //console.log("fetch_stock=",fetch_stock)
            //recompute qty info
            qty_info = order.get_product_total_qty(qty_info_args);
            //
            for (let k in qty_info)
            {
                if (k === 'total_qty')
                {
                    if (product.tracking !== 'none')
                        continue;
                    qty_available = product.qty_available_list.qty_available || 0;
                }
                else
                {
                    qty_available = product.qty_available_list[k] || 0;
                }
                qty_required = qty_info[k];
                qty_available = field_utils.parse.float('' + qty_available) || 0;
                qty_required = field_utils.parse.float('' + qty_required) || 0;
                lot_name = 'Nil';
                lot_name_display = 'Nil';
                if (k !== 'total_qty' && !String(k).includes('mt_unk_lot'))
                {
                    lot_name = this.lots_by_id[k] && this.lots_by_id[k].name || lot_name_display;
                    lot_name_display = lot_name;
                }
                else if (String(k).includes('mt_unk_lot'))
                {
                    lot_name_display = (String(k).split('mt_unk_lot_')[1] || '');
                    if (fetch_stock)
                        lot_name_display += " (Unavailable in system)";
                    lot_name = String(k).split('mt_unk_lot_')[1] || '';
                }
                if(unit)
                {
                    if (unit.rounding)
                    {
                        rounding = Math.max(unit.rounding, Math.pow(10, -decimals));
                        qty_available = round_pr(qty_available, rounding);
                        qty_availableStr = field_utils.format.float(qty_available, {digits: [69, decimals]});
                        qty_required = round_pr(qty_required, rounding);
                        qty_requiredStr = field_utils.format.float(qty_required, {digits: [69, decimals]});
                    }
                    else
                    {
                        qty_available = round_pr(qty_available, 1);
                        qty_availableStr = qty_available.toFixed(0);
                        qty_required = round_pr(qty_required, 1);
                        qty_requiredStr = qty_required.toFixed(0);
                    }
                }
                else
                {
                    qty_availableStr = '' + qty_available;
                    qty_requiredStr = '' + qty_required;
                }
                //
                if (qty_available < qty_required)
                {
                    //////////console.log.log((("out of stock=",operation)
                    out_stock_msg = "Product : "+ product.display_name +" /mt_br/Barcode : "+ (product.barcode || 'Nil') + "/mt_br/Lot / Serial : "+ lot_name_display +"/mt_br/ " +"Available Qty : "+ qty_availableStr +"/mt_br/Selling Qty : "+qty_requiredStr;
                    if (!fetch_stock)
                        out_stock_msg += "/mt_br//mt_br/Failed to fetch stock. Please check your connection !"
                    const { confirmed } = await Gui.showPopup('ConfirmPopup', {
                        confirmText: 'Force Add',
                        custom:true,
                        title: this.env._t('You do not have enough stock !! '),
                        body: this.env._t(
                            out_stock_msg
                        ),
                    });
                    if (confirmed)
                    {
                        //do nothing
                        /*
                        if (extras.order_line)
                        {
                            extras.order_line.is_from_setPackLotLines = false;
                            extras.order_line.old_pack_lots = {};
                        }
                        */
                    }
                    else
                    {
                        //console.log.log("force addeddd preventeddddd=",extras,operation)
                        //cancel button clicked
                        if (operation === 'add_product')
                        {
                            if (extras.order_line)
                            {
                                //order_line_old_qty -> merge case
                                if (extras.order_line_old_qty !== undefined)
                                {
                                    extras.order_line.dont_call_validate_product_stock = true;
                                    extras.order_line.set_quantity(extras.order_line_old_qty);
                                    extras.order_line.dont_call_validate_product_stock = false;
                                }
                                else
                                    order.remove_orderline(extras.order_line);
                            }
                        }
                        if (operation === 'set_qty')
                        {
                            if (extras.order_line)
                            {
                                //revert qty updated
                                if (extras.order_line_old_qty !== undefined && product.tracking !== 'serial')
                                {
                                    //NumberBuffer= {buffer: '101'}
                                    //////console.log.log(parseFloat('1211'),extras.order_line_old_qty)
                                    NumberBuffer.set(String(extras.order_line_old_qty));
                                    extras.order_line.dont_call_validate_product_stock = true;
                                    extras.order_line.set_quantity(extras.order_line_old_qty);
                                    extras.order_line.dont_call_validate_product_stock = false;
                                }
                                if (extras.order_line && extras.order_line.is_from_setPackLotLines)
                                {
                                    var non_stock_lot_lines = [];
                                    for (let lotLine of extras.order_line.pack_lot_lines.models)
                                    {
                                        //console.log.log("lotLine.get_lot_name()=",lotLine.get_lot_name(),lot_name)
                                        if (lotLine.get_lot_name() === lot_name)
                                        {
                                            non_stock_lot_lines.push(lotLine);
                                            //break;
                                        }
                                    }
                                    //console.log.log("non_stock_lot_lines=",non_stock_lot_lines)
                                    if (non_stock_lot_lines.length > 0)
                                    {
                                        for (let non_stock_lot_line of non_stock_lot_lines)
                                        {
                                            //existing lots_line
                                            if (extras.order_line.old_pack_lots[non_stock_lot_line.cid])
                                            {
                                                //revert the lot_name to old
                                                non_stock_lot_line.set({ lot_name: extras.order_line.old_pack_lots[non_stock_lot_line.cid] });
                                                //remove lot if no change (ie, clicking ok without change in name of lotline)
                                                if (lot_name === non_stock_lot_line.get_lot_name())
                                                    non_stock_lot_line.remove();
                                            }
                                            //new lot line case
                                            else
                                                non_stock_lot_line.remove();
                                        }
                                        //if serial tracking ,, revert the qty back
                                        if (product.tracking === 'serial')
                                        {
                                            extras.order_line.dont_call_validate_product_stock = true;
                                            //extras.order_line.set_quantity(extras.order_line_old_qty);
                                            extras.order_line.pack_lot_lines.set_quantity_by_lot();
                                            extras.order_line.dont_call_validate_product_stock = false;
                                        }
                                        //case set qty calling through setpacklotlines .. add_product case
                                        //if no more lot ,, delete entire order line
                                        if (extras.order_line.pack_lot_lines.models.length === 0)
                                            order.remove_orderline(extras.order_line);
                                    }
                                }
                            }

                        }
                    }
                //break
                }
            }
            ////////////console.log.log((("validate_product_stock for loop endedddddd")
        }
        if (extras.order_line)
        {
            extras.order_line.is_from_setPackLotLines = false;
            extras.order_line.old_pack_lots = {};
        }
        return true;
    },
    set_out_stock_info_order: function(order)
    {
        ////////////////console.log.log((("validate_product_stock=",operation)
        var self = this, out_stock_list = [];
        if (self.has_to_check_stock())
        {
            var product_used = [], decimals = self.dp['Product Unit of Measure'],
            product, qty_info, unit, qty_available, qty_required, rounding, out_stock_det;
            order.orderlines.each(function(line)
            {
                product = line.get_product();
                if (!product_used.includes(product.id))
                {
                    product_used.push(product.id);
                    if (self.has_to_check_product_stock(product) && product.qty_available_list !== undefined)
                    {
                        unit = product.get_unit();
                        qty_info = order.get_product_total_qty({'product':product});
                        for (let k in qty_info)
                        {
                            if (k === 'total_qty')
                            {
                                if (product.tracking !== 'none')
                                    continue;
                                qty_available = product.qty_available_list.qty_available || 0;
                            }
                            else
                                qty_available = product.qty_available_list[k] || 0;
                            qty_required = qty_info[k];
                            ////////////////console.log.log((("qty_available,req_qty=",qty_available,req_qty)
                            qty_available = field_utils.parse.float('' + qty_available) || 0;
                            qty_required = field_utils.parse.float('' + qty_required) || 0;
                            if (unit)
                            {
                                if (unit.rounding)
                                {
                                    rounding = Math.max(unit.rounding, Math.pow(10, -decimals));
                                    qty_available = round_pr(qty_available, rounding);
                                    qty_required = round_pr(qty_required, rounding);
                                }
                                else
                                {
                                    qty_available = round_pr(qty_available, 1);
                                    qty_required = round_pr(qty_required, 1);
                                }
                            }
                            //
                            if (qty_available < qty_required)
                            {
                                out_stock_det = {
                                    'product_id':product.id,
                                    'qty_available':qty_available,
                                    'qty_required': qty_required,
                                    'lot_name':''
                                    };
                                if (k !== 'total_qty' && !String(k).includes('mt_unk_lot'))
                                    out_stock_det['lot_id'] = k;
                                else if (String(k).includes('mt_unk_lot'))
                                    out_stock_det['lot_name'] = String(k).split('mt_unk_lot_')[1] || '';
                                out_stock_list.push(out_stock_det);
                            }
                        }
                    }
                }
            });
        }
        order.set_out_stock_list(out_stock_list);
    },
    push_single_order: function (order, opts)
    {
        if (this.has_to_check_stock())
        {
            this.set_out_stock_info_order(order);
            this.update_product_stock_from_order_lines(order);
        }
        return posmodel_super.push_single_order.apply(this, arguments);
    },
    push_and_invoice_order: function (order)
    {
        if (this.has_to_check_stock())
        {
            this.set_out_stock_info_order(order);
            this.update_product_stock_from_order_lines(order);
        }
        return posmodel_super.push_and_invoice_order.apply(this, arguments);
    },
    update_product_stock_from_order_lines: function(order)
    {
        var self = this;
        if (this.has_to_check_stock() && order.products_stock_updated !== true)
        {
            var product, lot_name, lot_id;
            order.orderlines.each(function(line) {
                product = line.get_product();
                if (self.has_to_check_product_stock(product) && product.qty_available_list !== undefined)
                {
                    //self.db.get_product_by_id(product.id).qty_available = product.qty_available - line.get_quantity();
                    ////////////////console.log.log((("line.pack_lot_lines.models=",line.pack_lot_lines.models)
                    for (let lotLine of line.pack_lot_lines.models || [])
                    {
                        lot_name = lotLine.get_lot_name();
                        if (lot_name)
                        {
                           lot_id = self.get_product_lot_id_by_name(product,lot_name);
                           if (lot_id)
                           {
                              if (product.qty_available_list[lot_id] !== undefined)
                              {
                                  if (product.tracking === 'serial')
                                     product.qty_available_list[lot_id] -= 1;
                                  else if (product.tracking === 'lot')
                                     product.qty_available_list[lot_id] -= line.get_quantity();
                              }
                           }
                        }
                    }
                    if (product.qty_available_list.qty_available !== undefined)
                        product.qty_available_list.qty_available -= line.get_quantity();
                }
            });
            order.products_stock_updated = true;
        }

    },
    /*
    get_product_model: function() {
        return _.find(this.models, function(model) {
            return model.model === "product.product";
        });
    },
    */
    add_product_qty: async function(products) {
        ////////////////console.log.log((("add_product_qty=",products)
        var self = this;
        _.each(products, function(p) {
            var product = self.db.get_product_by_id(p.id);
            if (product && self.has_to_check_product_stock(product) && 1==2)
            {
                var lot_id = p.lot_id || false;
                if (product.qty_available_list === undefined)
                    product.qty_available_list = {};
                var to_update = {};
                if (lot_id)
                    to_update[lot_id] = p.qty_available;
                else
                    to_update.qty_available = p.qty_available;
                _.extend(product.qty_available_list, to_update);
            }
        });
    },
    /*
    set_product_qty_available: function(product, qty) {
        product.qty_available = qty;
        this.refresh_qty_available(product);
    },
    */
    //not using
    validate_order_stock: function(order)
    {
        var res = true;
        var self = this;
        if (!self.config.allow_negative_stock_location  && order) {
            order.get_orderlines().forEach(function (orderline) {
                var product = orderline.product;
                if (product && self.has_to_check_product_stock(product))
                {
                    var total_qty = order.get_product_total_qty(product);
                    if (!self.validate_product_stock(product, total_qty))
                    {
                        res = false;
                        return res;
                    }
                }
            });
        }
        return res;
    },
    /*
    load_available_qty: async function(product_ids)
    {
        var self = this;
        if (self.has_to_check_stock() && product_ids.length > 0 && 1==2)
        {

            var product_product_model = self.get_product_model();
            var contt = _.extend(product_product_model.context, {
                    location: self.config.default_location_src_id[0],

                });

            //let which = ['product_only','product_with_lot'];
            var records = self.rpc({
                model: 'product.product',
                method: "search_read",
                args: [],
                fields: ["qty_available", "type"],
                domain: [['id','in',product_ids]],//product_product_model.domain,
                //context: _.extend(product_product_model.context, {
                //    location: self.config.default_location_src_id[0],
                //}),
                context: {location: self.config.default_location_src_id[0]}
            });
            records.then(function (products) {
                self.add_product_qty(products);
            });
            //with lots

            var rpc_vals = {
                model: 'product.product',
                method: "get_pos_product_qty_available",
                args: [product_ids,self.lots_by_product_id,self.config.default_location_src_id[0]],
                //fields: ["qty_available", "type"],
                //domain: [['id','=',product_ids[prod_ind]]],//product_product_model.domain,
                //context: _.extend(product_product_model.context, {
                //    location: self.config.default_location_src_id[0],
                //}),
                //context: {location: self.config.default_location_src_id[0],
                //lot_id: lots[lot_ind].id
                };

            self.rpc(rpc_vals)
            .then(function (stock_info) {
                ////////////////console.log.log((("products loaded lot 121=",stock_info)
                self.add_product_qty(stock_info);
                ////////////////console.log.log((("after update qty=",self.db.product_by_id)
                /*
                if (self.db.add_partners(partners)) {   // check if the partners we got were real updates
                    resolve();
                } else {
                    reject(new Error('Failed in updating partners.'));
                }

            });
        }
    },
    */
    after_load_server_data: async function()
    {
        var self = this;
        var res = await posmodel_super.after_load_server_data.call(this);
        if((self.config.stock_load_background || 1===1) && self.has_to_check_stock())
                self.loadStockBackground();
        return res;
        /*
        return posmodel_super.after_load_server_data.apply(self, arguments).then(function () {
            ////////////////console.log.log((("may be after_load_server_data  - finished")
            if((self.config.stock_load_background || 1===1) && self.has_to_check_stock())
                self.loadStockBackground();
        */
            /*
            if (self.config.allow_negative_stock_location === false
            && self.config.default_location_src_id)
                self.load_available_qty();
            */
        //});
    },
    loadStockBackground: async function() {
        var self = this;
        var all_product_ids = [], p_ids,
        limited_stock = self.config.limited_stock || 300, while_count = 0;
        for (let product_id in self.db.product_by_id)
        {
            if (self.db.product_by_id[product_id].type === 'product')
                all_product_ids.push(product_id);
        }
        //////////////console.log.log((('loadStockBackground=',)
        const product_ids_ordered = await self.rpc({
            model: 'pos.config',
            method: 'get_most_selling_products_ordered',
            args: [self.config_id, all_product_ids],
        });
        p_ids = product_ids_ordered.slice(0, limited_stock);
        while (p_ids.length > 0)
        {
            await self.load_and_update_stock(p_ids, self.config.default_location_src_id[0])
            while_count += 1;
            p_ids = product_ids_ordered.slice(while_count * limited_stock, (while_count*limited_stock) + limited_stock);
        }
    },
    update_product_stock: async function(products_stock_by_id)
    {
        var self = this,
        to_update, product, paid_orders;
        for (let product_id in products_stock_by_id)
        {
            product = self.db.get_product_by_id(product_id);
            if (!product || !self.has_to_check_product_stock(product))
                continue;
            if (product.qty_available_list === undefined)
                product.qty_available_list = {};
            to_update = {'qty_available':products_stock_by_id[product_id].qty_available};
            for (let lot_id in products_stock_by_id[product_id])
            {
                if (lot_id === 'qty_available')
                    continue;
                if (self.lots_by_product_id[product_id] === undefined)
                    self.lots_by_product_id[product_id] = [];
                var lot_line = {'name':products_stock_by_id[product_id][lot_id].name,
                                'id':lot_id
                                }
                self.lots_by_product_id[product_id].push(lot_line);
                self.lots_by_id[lot_id] = lot_line;
                to_update[lot_id] = products_stock_by_id[product_id][lot_id].qty_available;
            }
            _.extend(product.qty_available_list, to_update);
            paid_orders  = self.db.get_orders();
            if (self.has_to_check_stock() && to_update && paid_orders.length > 0)
            {
                //check unposted orders and deduct qty
                paid_orders.forEach(function (paid_order)
                {
                    paid_order.data.lines.forEach(function (paid_order_line)
                    {
                        if (paid_order_line[2].product_id !== product.id)
                            return;
                        //update total_qty_available
                        product.qty_available_list -= paid_order_line[2].qty;
                        //lot case
                        if (paid_order_line[2].pack_lot_ids.length > 0)
                        {
                            var lot_id, lot_name;
                            paid_order_line[2].pack_lot_ids.forEach(function (pack_lot_line)
                            {
                                var lot_name = pack_lot_line[2].lot_name;
                                //////////////console.log.log((("lot_name=",lot_name)
                                if (!lot_name)
                                    return;
                                lot_id = self.get_product_lot_id_by_name(product,lot_name);
                                if (!lot_id)
                                  return;
                                if (product.qty_available_list[lot_id] !== undefined)
                                {
                                  if (product.tracking === 'serial')
                                    product.qty_available_list[lot_id] -= 1;
                                  else if (product.tracking === 'lot')
                                    product.qty_available_list[lot_id] -= paid_order_line[2].qty;
                                }
                            });
                        }
                    });
                });
            }
        }
    },

    load_and_update_stock: async function(product_ids,location_id,lot_ids=[],lot_names=[],fetch_lot=true)
    {
        var self = this;
        return self.rpc({
                model: 'product.product',
                method: "get_pos_product_quantity_available",
                args: [product_ids,location_id,lot_ids,lot_names,fetch_lot]
                },
                {
                timeout: 30000 * product_ids.length,
                //shadow: !options.to_invoice
            })
            .then(function (stock_info) {
                self.update_product_stock(stock_info);
                return true
            }).catch(function (reason){
                //var error = reason.message || '';
                //console.log.warn('Failed to fetch stock:', product_ids,String(reason || ''));
                return false;
                /*
                if(error.code === 200 ){    // Business Logic Error, not a connection problem
                    // Hide error if already shown before ...
                    if ((!self.get('failed') || options.show_error) && !options.to_invoice) {
                        self.set('failed',error);
                        throw error;
                    }
                }
                throw error;
                */
            });
    },
    /*
    load_server_data: function () {
        var self = this;
        self.db.pos = this;
        return posmodel_super.load_server_data.apply(this, arguments).then(function () {
        });
    },
    */
});

    var _order_super = models.Order.prototype;
    var _super_orderline = models.Orderline.prototype;

    models.Order = models.Order.extend({
        get_product_total_qty: function(extras={})
        {
            //qty_to_add -> (add_product case either qty dec / inc)
            var product = extras.product;
            var qty_to_add = extras.qty_to_add || 0;
            var self = this,
            include_lot_names = extras.include_lots || [], source_line = extras.source_line,
            total_qty = 0, qty_info = {},
            line, line_qty;
            if (include_lot_names.length <= 0 && source_line && source_line.pack_lot_lines)
            {
                let lot_name;
                for (let lot_line of source_line.pack_lot_lines.get_valid_lots())
                {
                    lot_name = lot_line.get_lot_name();
                    include_lot_names.push(lot_name);
                }
            }
            for (var i = 0; i < self.orderlines.length; i++)
            {
                line = self.orderlines.at(i);
                line_qty = line.quantity;
                if (product.id === line.product.id)
                {
                    total_qty += (line_qty || 0);
                    if (line.pack_lot_lines)
                    {
                        var lot_name, lot_id;
                        for (let lot_line of line.pack_lot_lines.get_valid_lots()) {
                            lot_name = lot_line.get_lot_name();
                            if (include_lot_names.length > 0 && !include_lot_names.includes(lot_name))
                                continue;
                            lot_id = self.pos.get_product_lot_id_by_name(product,lot_name);
                            if (lot_id)
                            {
                                if (product.tracking === 'lot')
                                {
                                    qty_info[lot_id] = (qty_info[lot_id] || 0) + (line_qty || 0);
                                    //changing qty of a line (set_quantity)
                                    //if (source_line && source_line.id === line.id)
                                    //    qty_info[lot_id] += qty_to_add;
                                }
                                else if (product.tracking === 'serial')
                                    qty_info[lot_id] = (qty_info[lot_id] || 0) + 1;
                            }
                            //unknown_lots
                            else
                            {
                                if (product.tracking === 'lot')
                                    qty_info['mt_unk_lot_'+lot_name] = (qty_info['mt_unk_lot_'+lot_name] || 0) + (line_qty || 0);
                                else if (product.tracking === 'serial')
                                    qty_info['mt_unk_lot_'+lot_name] = (qty_info['mt_unk_lot_'+lot_name] || 0) + 1;
                            }
                        }
                    }
                }
            }
            qty_info.total_qty = parseFloat(total_qty + qty_to_add);
            return qty_info;
        },
        add_product: async function (product, options)
        {
            var self = this;
            //for checking there is a merge
            if (product && this.pos.has_to_check_product_stock(product))
            {
                var qty_by_line_id = [];
                self.get_orderlines().forEach(function (orderline) {
                    qty_by_line_id[orderline.id] = orderline.get_quantity();
                });
            }
            _order_super.add_product.apply(this, arguments);
            if (product && this.pos.has_to_check_product_stock(product))
            {
                var extras = {}, include_lot_names = [],
                selected_line = this.get_selected_orderline(), qty_info;
                //include only this lots in counting of qty
                if (selected_line && selected_line.pack_lot_lines)
                {
                    for (let lot_line of selected_line.pack_lot_lines.get_valid_lots())
                    {
                        include_lot_names.push(lot_line.get_lot_name());
                    }
                }
                //try to update_stock
                //await self.pos.load_and_update_stock([product.id],self.pos.config.default_location_src_id[0]);
                //
                if (selected_line && qty_by_line_id[selected_line.id] !== undefined)
                    extras.order_line_old_qty = qty_by_line_id[selected_line.id];
                var qty_info_args = {'qty_to_add':0,'product':product,
                                    'include_lots':include_lot_names,'source_line':selected_line
                                    };
                extras['order_line'] = selected_line;
                self.pos.validate_product_stock(product,qty_info_args,'add_product',extras);
            }
            //return
        },
        initialize: function (attributes, options) {
            _order_super.initialize.apply(this, arguments);
            this.set_out_stock_list([]);
        },
        init_from_JSON: function (json) {
            _order_super.init_from_JSON.apply(this, arguments);
            if (json.out_stock_list)
                this.set_out_stock_list(json.out_stock_list);
        },
        export_as_JSON: function ()
        {
            var json = _order_super.export_as_JSON.apply(this,arguments);
            json.out_stock_list = this.out_stock_list || [];
            return json;
        },
        set_out_stock_list: function(out_stock_list)
        {
            this.out_stock_list = out_stock_list;
        },
    });
    //order line class
    models.Orderline = models.Orderline.extend({
        init_from_JSON: function(json) {
            this.is_from_init_from_JSON = true;
            _super_orderline.init_from_JSON.apply(this,arguments);
            this.is_from_init_from_JSON = false;
        },
        setPackLotLines: async function({ modifiedPackLotLines, newPackLotLines }) {
            this.is_from_setPackLotLines = true;
            var old_pack_lots = {};
            for (let lotLine of this.pack_lot_lines.models) {
                old_pack_lots[lotLine.cid] = lotLine.get_lot_name();
            }
            //////////////console.log.log((("old_pack_lots=",old_pack_lots);
            this.old_pack_lots = old_pack_lots;
            await _super_orderline.setPackLotLines.apply(this,arguments);
            //hided becasue of popup is await
            //this.old_pack_lots = {};
            //this.is_from_setPackLotLines = false;
        },
        set_quantity: async function(quantity, keep_price)
        {
            var self = this, is_new_line = true,
            dont_call_validate_product_stock = this.dont_call_validate_product_stock,
            old_line_qty = this.get_quantity();// || 0;
            ////////////console.log.log((('dont_call_validate_product_stock=',dont_call_validate_product_stock)
            if (this.get_quantity() !== undefined)
                is_new_line = false;
            _super_orderline.set_quantity.apply(this,arguments);
            if (quantity !== 'remove')
            {
                var product = this.get_product();
                ////////////console.log.log((("st qty product=",product)
                ////////////console.log.log((("this.is_from_init_from_JSON =",this.is_from_init_from_JSON )
                var quant = typeof(quantity) === 'number' ? quantity : (field_utils.parse.float('' + quantity) || 0);
                if (!is_new_line && quant && !this.is_from_init_from_JSON && product && this.pos.has_to_check_product_stock(product))
                {
                    //try to update stock
                    //await self.pos.load_and_update_stock([product.id],self.pos.config.default_location_src_id[0]);
                    var qty_add_ded = (quant-(this.get_quantity() || 0));
                    var qty_info_args = {'product':product,'qty_to_add':qty_add_ded,
                                        'source_line':this
                                        };
                    if (dont_call_validate_product_stock !== true)
                    {
                        self.pos.validate_product_stock(product, qty_info_args,'set_qty',{'order_line':this,'order_line_old_qty':old_line_qty})
                    }
                }
            }
            //this.is_from_init_from_JSON = false;
        },
    });
});