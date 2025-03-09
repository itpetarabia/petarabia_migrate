odoo.define('theme_alan.s_product_banner_slide_front', function (require) {
'use strict';

var publicWidget = require('web.public.widget');

publicWidget.registry.product_banner_slide_front = publicWidget.Widget.extend({
    'selector':'.as_product_banner_slider',
    disabledInEditableMode: false,
    'events':{
        'click #add_to_cart_json':'_addToCart',
        'click #buy_now_json':'_buyNow'
    },
    _addToCart:function(ev){
        ev.preventDefault()
        var $form = $(ev.currentTarget).closest('form');
        var $custom_val = $form.find('.variant_custom_value');
        var custom_product_template_attribute_value_id = $custom_val.data('custom_product_template_attribute_value_id')
        var attribute_value_name = $custom_val.data('attribute_value_name')
        var value = $custom_val.val()
        if(value != undefined){
            var product_custom_attribute_values = [{"custom_product_template_attribute_value_id":custom_product_template_attribute_value_id
            ,"attribute_value_name":attribute_value_name,"custom_value":value}]
        }
        this._rpc({
            route: '/shop/cart/update_json',
            params: {
                product_id: parseInt($form.find('input[name="product_id"]').val()),
                add_qty: 1,
                product_custom_attribute_values:product_custom_attribute_values
            },
        }).then(function (data) {
            location.href = '/shop/cart';
        });
    },
    _buyNow:function(ev){
        ev.preventDefault()
        var $form = $(ev.currentTarget).closest('form');
        var is_public_user = $form.find('input[name="public_user"]').val()
        var $custom_val = $form.find('.variant_custom_value');
        var custom_product_template_attribute_value_id = $custom_val.data('custom_product_template_attribute_value_id')
        var attribute_value_name = $custom_val.data('attribute_value_name')
        var value = $custom_val.val()
        var product_custom_attribute_values = false
        if(value != undefined){
            var product_custom_attribute_values = [{"custom_product_template_attribute_value_id":custom_product_template_attribute_value_id
            ,"attribute_value_name":attribute_value_name,"custom_value":value}]
        }
        this._rpc({
            route: '/shop/cart/update_json',
            params: {
                product_id: parseInt($form.find('input[name="product_id"]').val()),
                add_qty: 1,
                product_custom_attribute_values:product_custom_attribute_values

            },
        }).then(function (data) {
            if(is_public_user.trim() == 'True'){
                location.href = '/shop/address';
            }else{
                location.href = '/shop/payment';
            }
        });
    },

    start: function (editable_mode) {
        var self = this;
        if (self.editableMode){
            self.$target.empty().append('<div class="container"><div class="seaction-head"><h2>'+ self.$target.attr('data-sp_name')  +'</h2></div></div>');
        }
        if(!self.editableMode){
            var product_id=self.$target.attr('data-sp_id');
            if(product_id != '0'){
                var addCart = self.$target.attr('data-add_to_cart');
                var buyBtn = self.$target.attr('data-buy_btn');
                var prodRating = self.$target.attr('data-prod_rating');
                var prodLab = self.$target.attr('data-prob_label');
                var pos = self.$target.attr('data-pos');
                return self._rpc({
                    route: '/get/product_banner/',
                    params: {
                        'id':product_id,
                        'edit_mode':false,
                        'add_to_cart':addCart,
                        'buy_btn':buyBtn,
                        'prod_rating':prodRating,
                        'prod_label':prodLab,
                        'pos':pos,
                    }
                }).then(function (result) {
                    self.$target.empty().append(result['prods_banner_temp']);
                    self.initialize_owl()
                });
            }
        }
    },
    initialize_owl: function (autoplay=false, items=4, slider_timing=5000) {
        $('.prod_banner_carousel_list').owlCarousel({
            items:1,
            loop:true,
            margin:10,
            merge:true,
            responsive:{
                0: {
                    items: 1,
                },
                768: {
                    items: 1,
                }
            }
        });
    },
});
});
