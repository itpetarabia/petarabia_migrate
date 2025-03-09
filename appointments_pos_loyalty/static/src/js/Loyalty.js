odoo.define('appointments_pos_loyalty.pos_loyalty', function (require) {
"use strict";

var models = require('point_of_sale.models');
var core = require('web.core');
var utils = require('web.utils');

var round_pr = utils.round_precision;

var _t = core._t;

var _super_order = models.Order.prototype;
models.Order = models.Order.extend({

    /* The list of rewards that the current customer can get */
    // replace function
    get_available_rewards: function(){
        var client = this.get_client();
        if (!client) {
            return [];
        }

        var self = this;
        var rewards = [];
        console.log("this.pos.loyalty",this.pos.loyalty,self.get_spendable_points());
        for (var i = 0; i < this.pos.loyalty.rewards.length; i++) {
            var reward = this.pos.loyalty.rewards[i];
            if (reward.minimum_points > self.get_spendable_points()) {
                continue;
            } else if(reward.reward_type === 'discount' && reward.point_cost > self.get_spendable_points()) {
                continue;
            } else if(reward.reward_type === 'gift' && reward.point_cost > self.get_spendable_points()) {
                continue;
            } else if(reward.reward_type === 'discount' && reward.discount_apply_on === 'specific_products' ) {
                var found = false;
                self.get_orderlines().forEach(function(line) {
                    found |= reward.discount_specific_product_ids.find(function(product_id){return product_id === line.get_product().id;});
                });
                if(!found)
                    continue;
            } else if(reward.reward_type === 'discount' && reward.discount_type === 'fixed_amount' && self.get_total_with_tax() && self.get_total_with_tax() < reward.minimum_amount) {
                //added && self.get_total_with_tax()
                continue;
            }
            rewards.push(reward);
        }
        return rewards;
    },

    
});

});
