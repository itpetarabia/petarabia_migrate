odoo.define('pos_important_customer_ext.models', function (require) {
    "use strict";
	var models = require('point_of_sale.models');
    var ClientListScreen = require('point_of_sale.ClientListScreen');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _super_orderline = models.Orderline.prototype;
	var utils = require('web.utils');
    var round_pr = utils.round_precision;
	
	var PosModelSuper = models.PosModel;



//console.log('test')
models.load_models({
    model:  'pos.order',
    fields: ['name', 'partner_id','date_order','amount_total', 'amount_tax',
        'pos_reference','lines','state','session_id','company_id'],
    loaded: function(self, orders){
        self.orders = orders;
        console.log('orders', self.orders)
        }

    },
    {
    model: 'pos.order.line',
    fields: ['product_id','qty','price_unit','price_subtotal_incl','order_id','discount'],
    loaded: function(self,order_lines){
    self.order_line = [];
    for (var i = 0; i < order_lines.length; i++) {
        self.order_line[i] = order_lines[i];
    }
    console.log('orderline[]', self.order_line)
    }
});

models.PosModel = models.PosModel.extend({
    after_load_server_data: function(){
		var dict_partner_total={};
		PosModelSuper.prototype.after_load_server_data.apply(this, arguments);
		this.orders.forEach(function (order) {
			if(dict_partner_total[order.partner_id[0]]){
				dict_partner_total[order.partner_id[0]] = dict_partner_total[order.partner_id[0]]+order.amount_total
			}else{
				dict_partner_total[order.partner_id[0]] = order.amount_total
			}
        console.log('dict_partner_total', dict_partner_total)
			
		});	
		
		// Create items array
		var items = Object.keys(dict_partner_total).map(function(key) {
          console.log('items', dict_partner_total[key])
		  return [key, dict_partner_total[key]];
		});
		
		// Sort the array based on the second element
		items.sort(function(first, second) {
		  return second[1] - first[1];
		});
		
		// Create a new array with only the first 5 items
		items = items.slice(0, 20)
		this.dict_partner_total = items;
		ClientListScreen.dict_partner_total = items;
        
    },
    get_client: function() {
        //var part_id = PosModelSuper.prototype.get_client.apply(this, arguments);
        var part_id = PosModelSuper.prototype.get_client.call(this);
        //console.log("get_client_inherit",this)
        var set=0
        if(part_id){
            this.dict_partner_total.forEach(function (dict){
                if(part_id.id == dict[0]){
                    $('.set-customer').addClass('button-red');
                    set=1
                }
            });
        }
        if($('.set-customer').hasClass('button-red')){
            if(set !=1){
                $('.set-customer').removeClass('button-red');
            }
        }
        return part_id;

    },
});
/*
screens.ClientListScreenWidget.include({
	save_changes: function(){
		this._super();
		var self = this;
		if(this.new_client){
			var partner_id = this.new_client.id
			var set=0
			if(partner_id){
				self.pos.dict_partner_total.forEach(function (dict){
					if(partner_id == dict[0]){
						$('.set-customer').addClass('button-red');
						set=1
						//break;
					}else if($('.set-customer').hasClass('button-red')){
						if(set !=1){
							$('.set-customer').removeClass('button-red');	
						}
						
					}	
				});
			}
			
			
		}
	},

});	

*/




});



