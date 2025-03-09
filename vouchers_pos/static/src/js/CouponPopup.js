odoo.define('voucher_pos.CouponPopup', function(require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useAutofocus, useListener } = require('web.custom_hooks');
    var rpc = require('web.rpc');

    var core = require('web.core');

    var _t = core._t;

    function find_coupon(code, coupons, vouchers) {
        var coupon = [];
        for(var i in coupons){
            if (coupons[i]['code'] == code){
                coupon.push(coupons[i]);
            }
        }
        if(coupon.length > 0){
            for(var i in vouchers){
                if (vouchers[i]['id'] == coupon[0]['voucher'][0]){
                    coupon.push(vouchers[i]);
                    return coupon;
                }
            }
        }
        return false
    }

        function check_validity(coupon, applied_coupons, customer) {
        // checking it is already used or not
        for (var i in applied_coupons){
            if(applied_coupons[i]['coupon_pos'] == coupon[0]['code'] && applied_coupons[i]['partner_id'][0] == customer['id']){
                return applied_coupons[i];
            }
        }
        return false;
    }

    function check_expiry(start, end) {
        var today = moment().format('YYYY-MM-DD');
        if(start && end) {
            if (today < start || today > end)
                return false;
        }
        else if(start){
            if (today < start)
                return false;
        }
        else if(end){
            if (today > end)
                return false;
        }
        return true;
    }

    function get_coupon_product(products) {
        for (var i in products){
            if(products[i]['display_name'] == 'Gift-Coupon')
                return products[i]['id'];
        }
        return false;
    }

    class CouponPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
           this.flag = true;
           useAutofocus({ selector: 'input' });
           this.coupon_product = get_coupon_product(this.env.pos.db.product_by_id);
        }
        apply_coupon() {
            if (this.coupon_product == false)
            {
                this.trigger('close-popup');
                this.showPopup('ErrorPopup',{
                            'title': _t('Unable to find gift-Coupon product !'),
                            'body': _t("Please create a product with name 'Gift-Coupon'" ),
                        });
                return;
            }
            var self = this;
            // verifying and applying coupon
                if(self.flag){
                    var order = this.env.pos.get_order();
                    var lines = order ? order.orderlines : false;
                    if(order.coupon){
                        //self.gui.close_popup();
                        self.trigger('close-popup');
                        self.showPopup('ErrorPopup',{
                            'title': _t('Unable to apply Coupon !'),
                            //'body': _t('Either coupon is already applied or you have not selected any products.'),
                            'body': _t('Coupon is already applied.'),
                        });
                    }
                    else{
                        if(lines.models.length > 0 && order.check_voucher_validity()) {
                            var product = self.env.pos.db.get_product_by_id(self.coupon_product);
                            var price = -1;
                            if (order.coupon_status['type'] == 'fixed') {
                                price *= order.coupon_status['voucher_val'];
                            }
                            if (order.coupon_status['type'] == 'percentage') {
                                price *= order.get_total_with_tax() * order.coupon_status['voucher_val'] / 100;
                            }
                            if ((order.get_total_with_tax - price) <= 0) {
                                //self.gui.close_popup();
                                self.trigger('close-popup');
                                self.showPopup('ErrorPopup', {
                                    'title': _t('Unable to apply Coupon !'),
                                    'body': _t('Coupon amount is too large to apply. The total amount cannot be negative'),
                                });
                            }
                            else{
                                //console.log("Add product=",product)
                                order.add_product(product, {quantity: 1, price: price});
                                order.coupon_applied();
                                // updating coupon balance after applying coupon
                                var client = order.get_client();
                                var temp = {
                                    'partner_id': client['id'],
                                    'coupon_pos': order.coupon_status['code'],
                                };
                                rpc.query({
                                    model: 'partner.coupon.pos',
                                    method: 'update_history',
                                    args: ['', temp]
                                }).then(function (result) {
                                    var applied = self.env.pos.applied_coupon;
                                    var already_used = false;
                                    for (var j in applied) {
                                        if (applied[j]['partner_id'][0] == client['id'] &&
                                            applied[j]['coupon_pos'] == order.coupon_status['code']) {
                                            applied[j]['number_pos'] += 1;
                                            already_used = true;
                                            break;
                                        }
                                    }
                                    if (!already_used) {
                                        //console.log("already_used")
                                        var temp = {
                                            'partner_id': [client['id'], client['name']],
                                            'number_pos': 1,
                                            'coupon_pos': order.coupon_status['code']
                                        };
                                        self.env.pos.applied_coupon.push(temp);
                                        //self.gui.close_popup();
                                        self.trigger('close-popup');
                                    }
                                });
                            }
                        }
                        else{
                            //self.gui.close_popup();
                            self.trigger('close-popup');
                            self.showPopup('ErrorPopup',{
                                'title': _t('Unable to apply Coupon !'),
                                'body': _t('This coupon is not applicable on the products or category you have selected !'),
                            });
                        }
                    }
                }
                else{
                    //self.gui.close_popup();
                     self.trigger('close-popup');
                    self.showPopup('ErrorPopup',{
                        'title': _t('Unable to apply Coupon !'),
                        'body': _t('Invalid Code or no Coupons left !')
                    });
                }


        }
        /*
        confirm(event) {
            var order = this.env.pos.get_order();
            var coupon = $(".coupon_code").val();
            //var value = this.$('input').val();
            console.log('apply coupon=',order);
            this.trigger('close-popup');
        }
        */
        validate_coupon()
        {
            // checking the code entered
                var current_order = this.env.pos.get_order();
                var coupon = $(".coupon_code").val();
                if (current_order.orderlines.models.length == 0){
                    this.showPopup('ErrorPopup',{
                        'title': this.env._t('No products !'),
                        'body': this.env._t('You cannot apply coupon without products.'),
                    });
                }
                else if(coupon){
                    if(current_order.get_client()){
                        var customer = current_order.get_client();
                        var coupon_res = find_coupon(coupon, this.env.pos.coupons, this.env.pos.vouchers);
                        var flag = true;
                        // is there a coupon with this code which has balance above zero
                        if(coupon_res && coupon_res[0]['total_avail'] > 0){
                            var applied_coupons = this.env.pos.applied_coupon;
                            // checking coupon status
                            var coupon_stat = check_validity(coupon_res, applied_coupons, customer);
                            // if this coupon was for a particular customer and is not used already
                            if(coupon_res[0]['partner_id'] && coupon_res[0]['partner_id'][0] != customer['id']){
                                flag = false;
                            }
                            var today = moment().format('YYYY-MM-DD');
                            // checking coupon balance and expiry
                            if(flag && coupon_stat && coupon_stat.number_pos < coupon_res[0]['limit'] &&
                                today <= coupon_res[1]['expiry_date']){
                                // checking coupon validity
                                flag = check_expiry(coupon_res[0]['start_date'], coupon_res[0]['end_date']);
                            }
                            // this customer has not used this coupon yet
                            else if(flag && !coupon_stat && today <= coupon_res[1]['expiry_date']){
                                flag = check_expiry(coupon_res[0]['start_date'], coupon_res[0]['end_date']);
                            }
                            else{
                                flag = false;
                                $(".coupon_status_p").text("Unable to apply coupon. Check coupon validity.!");
                            }
                        }
                        else{
                            flag = false;
                            $(".coupon_status_p").text("Invalid code or no coupons left. Please try again !!");
                        }
                        if(flag){
                            var val = coupon_res[0]['type'] == 'fixed' ?
                                coupon_res[0]['voucher_val'] : coupon_res[0]['voucher_val'] + "%";
                            var obj = $(".coupon_status_p").text("Voucher value is : "+val+" \n" +
                                " Do you want to proceed ? \n This operation cannot be reversed.");
                            obj.html(obj.html().replace(/\n/g,'<br/>'));
                            //var order = self.pos.get_order();
                            current_order.set_coupon_value(coupon_res[0]);
                        }
                        self.flag = flag;
                        if(flag){
                           $(".confirm-coupon").css("display", "block");
                        }
                        else{
                            var ob = $(".coupon_status_p").text("Invalid code or no coupons left. \nPlease check coupon validity.\n" +
                                "or check whether the coupon usage is limited to a particular customer.");
                            ob.html(ob.html().replace(/\n/g,'<br/>'));
                        }
                    }
                    else{
                        $(".coupon_status_p").text("Please select a customer !!");
                    }
                }
        }

    }
    CouponPopup.template = 'CouponPopup';
    CouponPopup.defaultProps = {
        confirmText: 'Apply',
        cancelText: 'Cancel',
        title: 'Enter Your Coupon',
    };

    Registries.Component.add(CouponPopup);

    return CouponPopup;
});
