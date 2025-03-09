odoo.define('pos_debt_notebook.PaymentScreen', function(require) {
    'use strict';

    const { parse } = require('web.field_utils');
    const PosComponent = require('point_of_sale.PosComponent');
    const { useErrorHandlers } = require('point_of_sale.custom_hooks');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const { onChangeOrder } = require('point_of_sale.custom_hooks');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const core = require("web.core");
    var QWeb = core.qweb;
    var models = require("point_of_sale.models");

    const PosNotebookPaymentScreen = (PaymentScreen) =>
        class extends PaymentScreen {
            constructor() {
                console.log("constructor-PaymentScreen");
                super(...arguments);
                this.env.pos.on(
                    "updateDebtHistory",
                    function(partner_ids) {
                        this.update_debt_history(partner_ids);
                    },
                    this
                );
                //var validation_button = $(QWeb.render("ValidationButton", {widget: this}));
                //validation_button.find(".autopay").click(function() {
                //    this.click_autopay_validation();
                //});
            }
            update_debt_history(partner_ids) {
                console.log("update_debt_history123w1")
                var client = this.env.pos.get_client();
                if (client && $.inArray(client.id, partner_ids) !== -1) {
                    //this.gui.screen_instances.products.actionpad.renderElement();
                    this.customer_changed();
                }
            }
            async validateOrder(isForceValidate) {
                console.log("validate_order123w")
                var currentOrder = this.env.pos.get_order();
                var zero_paymentlines = _.filter(currentOrder.get_paymentlines(), function(
                    p
                ) {
                    return p.amount === 0;
                });
                // KPL: hide code
                //_.each(zero_paymentlines, function(p) {
                //    currentOrder.remove_paymentline(p);
                //});
                var isDebt = currentOrder.updates_debt();
                var debt_amount = currentOrder.get_debt_delta();
                var client = currentOrder.get_client();
                if (client) {
                    currentOrder.debt_before = client.debt;
                    currentOrder.debt_after = currentOrder.debt_before + debt_amount;
                } else {
                    currentOrder.debt_before = false;
                    currentOrder.debt_after = false;
                }
                if (isDebt && !client) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Unknown customer'),
                        body: this.env._t('You cannot use Debt payment. Select customer first.'),
                    });
                    return;
                }
                var paymentlines_with_credits_via_discounts = currentOrder.has_paymentlines_with_credits_via_discounts();
                if (paymentlines_with_credits_via_discounts.length) {
                    var paymentlines_with_credits_via_discounts_text = _.map(
                        paymentlines_with_credits_via_discounts,
                        function(pl) {
                            return pl.name;
                        }
                    ).join(", ");

                    if (this.check_discount_credits_for_taxed_products()) {
                        this.showPopup('ErrorPopup', {
                            title: this.env._t("Unable to validate with the " +
                                    paymentlines_with_credits_via_discounts_text +
                                    " payment method"),
                            body: this.env._t(
                                "You cannot use " +
                                    paymentlines_with_credits_via_discounts_text +
                                    " for products with taxes. Use an another payment method, or pay the full price with only discount credits"
                                    ),
                        });
                        return;
                    }
                    if (currentOrder.has_credit_product()) {

                        this.showPopup("ErrorPopup", {
                            title: this.env._t(
                                "Unable to validate with the " +
                                    paymentlines_with_credits_via_discounts_text +
                                    " payment method"
                            ),
                            body: this.env._t(
                                "You cannot use " +
                                    paymentlines_with_credits_via_discounts_text +
                                    " for credit top-up products. Use an another non-discount payment method"
                            ),
                        });
                        return;
                    }
                }
                //console.log("get_paymentlines()",currentOrder.get_paymentlines());
                if (
                    !currentOrder.get_paymentlines().length &&
                    currentOrder.has_return_product()
                ) {

                    this.showPopup("ErrorPopup", {
                        title: this.env._t("Unable to validate return order"),
                        body: this.env._t("Specify Payment Method"),
                    });
                    return;
                }
                if (currentOrder.has_credit_product() && !client) {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("Unknown customer"),
                        body: this.env._t("Don't forget to specify Customer when sell Credits."),
                    });
                    return;
                }
                if (isDebt && currentOrder.get_orderlines().length === 0) {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("Empty Order"),
                        body: this.env._t(
                            "There must be at least one product in your order before it can be validated. (Hint: you can use some dummy zero price product)"
                        ),
                    });
                    return;
                }
                var exceeding_debts = this.exceeding_debts_check();
                if (client && exceeding_debts) {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("Max Debt exceeded"),
                        body: this.env._t(
                            "You cannot sell products on credit payment method " +
                                exceeding_debts +
                                " to the customer because its max debt value will be exceeded."
                        ),
                    });
                    return;
                }
                if (this.debt_change_check()) {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t(
                            "Unable to return the change or cash out with the debt payment method"
                        ),
                        body: this.env._t(
                            "Please enter the exact or lower debt amount than the cost of the order."
                        ),
                    });
                    return;
                }
                var violations = this.debt_journal_restricted_categories_check();
                console.log("violations",violations)
                if (violations.length) {
                    this.showPopup("ErrorPopup", {
                        title: this.env._t("Unable to validate with the debt payment method"),
                        body: this.env._t(this.restricted_categories_message(violations)),
                    });
                    return;
                }
                //if (client)
                //    this.pos.gui.screen_instances.clientlist.partner_cache.clear_node(
                //        client.id
                //    );
                await super.validateOrder(isForceValidate);
            }
            async _finalizeValidation() {
                console.log("finalize_validation123w")
                var self = this;
                var order = this.env.pos.get_order(),
                    paymentlines = order.get_paymentlines(),
                    partner = this.env.pos.get_client();
                var debt_pl = _.filter(paymentlines, function(pl) {
                    //return pl.cashregister.journal.debt;
                    return pl.payment_method.debt;
                });
                if (debt_pl && partner) {
                    order.has_paymentlines_with_credits_via_discounts();
                    await super._finalizeValidation();
                    // Offline updating of credits, on a restored network this data will be replaced by the servers one
                    _.each(debt_pl, function(pl) {
                        //partner.debts[pl.cashregister.journal.id].balance -= pl.amount;
                        //console.log("l1",pl);
                        partner.debts[pl.payment_method.id].balance -= pl.amount;
                        partner.debt += pl.amount;
                    });
                } else {
                    await super._finalizeValidation();
                }
                var debt_prod = _.filter(order.get_orderlines(), function(ol) {
                    return ol.product.credit_product;
                });
                if (debt_prod) {
                    var value = 0;
                    _.each(debt_prod, function(dp) {
                        value = round_pr(
                            dp.quantity * dp.price,
                            self.env.pos.currency.rounding
                        );
                        partner.debts[dp.product.credit_product[0]].balance += value;
                        partner.debt -= value;
                    });
                }
            }
            get_used_debt_cashregisters(paymentlines) {
                console.log("get_used_debt_cashregisters123w")
                paymentlines = paymentlines || this.env.pos.get_order().get_paymentlines();
                var cashregisters = _.uniq(
                    _.map(paymentlines, function(pl) {
                        console.log("l3",pl);
                        return pl.payment_method;
                    })
                );
                return _.filter(cashregisters, function(cr) {
                    //return cr.journal.debt;
                    //console.log("l2",cr)
                    return cr.debt;
                });
            }
            restricted_categories_message(cashregisters) {
                console.log("restricted_categories_message123w")
                var self = this;
                var body = [];
                var categ_names = [];
                _.each(cashregisters, function(cr) {
                    //console.log("l4",cr)
                    var pymt_method = cr;
                    _.each(pymt_method.category_ids, function(categ) {
                        categ_names.push(self.env.pos.db.get_category_by_id(categ).name);
                    });
                    //body.push(categ_names.join(", ") + " with " + cr.journal_id[1] + " ");
                    body.push(categ_names.join(", ") + " with " + cr + " ");
                });
                // TODO we can make a better formatting here
                return "You may only buy " + body.toString();
            }
            debt_journal_restricted_categories_check() {
                console.log("debt_journal_restricted_categories_check123w")
                var self = this;
                var cashregisters = this.get_used_debt_cashregisters();
                //console.log("cashregisters",cashregisters)
                cashregisters = _.filter(cashregisters, function(cr) {
                    //console.log("crrrrr",cr)
                    return cr.category_ids.length > 0;
                });
                var violations = [];
                _.each(cashregisters, function(cr) {
                    if (self.restricted_products_check(cr)) {
                        violations.push(cr);
                    }
                });
                return violations;
            }
            check_discount_credits_for_taxed_products() {
                console.log("check_discount_credits_for_taxed_products123w")
                var order = this.env.pos.get_order(),
                    discount_pl = order.has_paymentlines_with_credits_via_discounts();
                if (
                    !discount_pl.length ||
                    discount_pl.length === order.get_paymentlines().length
                ) {
                    return false;
                }
                var taxes_id = false;
                var taxed_orderlines = _.find(order.orderlines.models, function(ol) {
                    // Returns only a found orderline with a tax that is not included in the price
                    taxes_id = ol.product.taxes_id;
                    if (taxes_id && taxes_id.length) {
                        return _.find(taxes_id, function(t) {
                            return !order.pos.taxes_by_id[t].price_include;
                        });
                    }
                    return false;
                });
                if (!taxed_orderlines) {
                    return false;
                }
                return true;
            }
            restricted_products_check(cr) {
                console.log("restricted_products_check123w")
                var order = this.env.pos.get_order();
                var sum_pl = round_pr(
                    order.get_summary_for_cashregister(cr),
                    this.env.pos.currency.rounding
                );
                //console.log("l5")
                var limits = order.get_payment_limits(cr, "products_restriction");
                var allowed_lines = _.filter(order.get_orderlines(), function(ol) {
                    var categories = [];
                    if (ol.product.pos_categ_id) {
                        categories = [ol.product.pos_categ_id[0]];
                    } else {
                        categories = ol.product.pos_category_ids;
                    }
                    if (_.intersection(cr.category_ids, categories).length) {
                        return true;
                    }
                    return false;
                });
                if (
                    allowed_lines.length === order.get_orderlines().length ||
                    this.cash_out_check()
                ) {
                    // If all products are allowed or it is a cash out case
                    // we don't need to check max debt exceeding, because it was checked earlier
                    return false;
                }
                if (
                    _.has(limits, "products_restriction") &&
                    sum_pl > limits.products_restriction
                ) {
                    return cr;
                }
                return false;
            }
            cash_out_check() {
                console.log("cash_out_check123w")
                var order = this.env.pos.get_order();
                if (
                    order.get_orderlines().length === 1 &&
                    this.pos.config.debt_dummy_product_id &&
                    order.get_orderlines()[0].product.id ===
                        this.pos.config.debt_dummy_product_id[0]
                ) {
                    return true;
                }
                return false;
            }
            exceeding_debts_check() {
                console.log("exceeding_debts_check123w")
                var order = this.env.pos.get_order(),
                    flag = false;
                if (this.env.pos.get_client()) {
                    _.each(this.get_used_debt_cashregisters(), function(cr) {
                        var limits = order.get_payment_limits(cr, "debt_limit");
                        var sum_pl = order.get_summary_for_cashregister(cr);
                        //console.log("l6",cr,cr.debt_limit)
                        // No need to check that debt_limit is in limits by the reason of get_payment_limits definition
                        if (cr.debt_limit > 0 && sum_pl > limits.debt_limit) {
                            //flag = cr.journal_id[1];
                            flag = cr.name;
                        }
                    });
                    return flag;
                }
            }
            debt_change_check() {
                console.log("debt_change_check123w")
                var order = this.env.pos.get_order(),
                    paymentlines = order.get_paymentlines();
                console.log("paymentlines",paymentlines)
                for (var i = 0; i < paymentlines.length; i++) {
                    //var journal = paymentlines[i].cashregister.journal;
                    var pymt_method = paymentlines[i].payment_method;
                    if (
                        pymt_method.debt &&
                        !pymt_method.pos_cash_out &&
                        order.get_change(paymentlines[i]) > 0
                    ) {
                        return true;
                    }
                }
                return false;
            }
            async pay_full_debt() {
                console.log("pay_full_debt Extended123w");
                var self = this;
                //this._super();
                var total_debt_balance = this.get_debt_balance();
                console.log("total_debt_balance=",total_debt_balance);
                const { confirmed, payload: inputNumber } = await this.showPopup('NumberPopup', {
                    startingValue: Math.abs(total_debt_balance),
                    cheap: true,
                    title: this.env._t('Pay Debt'),
                });
                console.log("confirmed",confirmed,inputNumber);
                if (!confirmed) return false;
                if (inputNumber <= 0 || inputNumber > Math.abs(total_debt_balance)){
                    this.showPopup('ErrorPopup',{
                        title: this.env._t('Error: Debt Amount Exceeded'),
                        body: this.env._t('The entered amount '+ String(inputNumber) +' is greater than debt. Maximum debt is '+String(Math.abs(total_debt_balance))),
                    });

                }
                else{
                    self.pay_full_debt_inherited(inputNumber);
                }





            }
            //org function = pay_full_debt
            pay_full_debt_inherited(debt_input) {
                console.log("pay_full_debt_inherited=123w");
                debt_input = Math.abs(debt_input);
                var self = this;
                var order = this.env.pos.get_order();
                if (order && !order.orderlines.length && this.env.pos.config.debt_dummy_product_id){
                    order.add_product(
                        this.env.pos.db.get_product_by_id(this.env.pos.config.debt_dummy_product_id[0]),
                        {'price': 0}
                    );
                }
                console.log("111111");
                var paymentLines = order.get_paymentlines();
                console.log("paymentLines=",paymentLines);
                if (paymentLines.length) {
                    _.each(paymentLines, function(paymentLine) {
                        if (paymentLine && paymentLine.payment_method.debt){
                            paymentLine.destroy();
                        }
                    });
                }

                console.log("2222222");
                var debts = order.get_client().debts;
                _.each(debts, function(debt) {
                    console.log("2.1111",debts);
                    if (debt.balance < 0) {
                        var newDebtPaymentline = new models.Paymentline({},{
                            pos: self.env.pos,
                            order: order,
                            payment_method: _.find(self.env.pos.payment_methods, function(cr){
                                //return cr.journal_id[0] === debt.journal_id[0];
                                return cr.id === debt.payment_method_id[0];
                            })
                        });
                        console.log("2.222",newDebtPaymentline);
                        //
                        if (debt_input > 0)
                        {
                            var balance = debt.balance;
                            if (Math.abs(debt.balance) <= debt_input)
                            {
                                debt_input-= Math.abs(debt.balance)
                            }
                            else
                            {
                                balance = -debt_input;
                                debt_input= 0;
                            }
                            //
                            newDebtPaymentline.set_amount(balance);
                            order.paymentlines.add(newDebtPaymentline);
                            order.select_paymentline(newDebtPaymentline);
                        }
                    }
                });
                console.log("333333");
                //this.render_paymentlines();
            }

            get_debt_balance(){
                console.log("get_debt_balance123w")
                var self = this;
                var order = this.env.pos.get_order();

                var total_debt_balance = 0;
                var debts = order.get_client().debts;
                _.each(debts, function(debt) {
                    if (debt.balance < 0) {
                        //var newDebtPaymentline = new models.Paymentline({},{
                        //    pos: self.pos,
                        //    order: order,
                        //    cashregister: _.find(self.pos.cashregisters, function(cr){
                        //        return cr.journal_id[0] === debt.journal_id[0];
                        //    })
                        //});
                        //newDebtPaymentline.set_amount(debt.balance);
                        //order.paymentlines.add(newDebtPaymentline);

                        total_debt_balance+=debt.balance;
                    }

                });
                return total_debt_balance;
            }

            add_autopay_paymentlines() {
                console.log("add_autopay_paymentlines123w")
                var client = this.env.pos.get_client();
                var order = this.env.pos.get_order();
                var status = "";
                if (
                    client &&
                    client.debts &&
                    order &&
                    order.get_orderlines().length !== 0 &&
                    !order.has_credit_product()
                ) {
                    var paymentlines = order.get_paymentlines();
                    if (paymentlines.length && order.get_due() > 0) {
                        _.each(paymentlines, function(pl) {
                            order.remove_paymentline(pl);
                        });
                    }
                    var autopay_cashregisters = _.filter(this.env.pos.payment_methods, function(
                        cr
                    ) {
                        return (
                            cr.debt &&
                            cr.credits_autopay &&
                            client.debts[cr.id].balance > 0
                        );
                    });
                    if (autopay_cashregisters) {
                        _.each(autopay_cashregisters, function(cr) {
                            if (order.get_due()) {
                                console.log("cr0000",cr);
                                order.add_paymentline(cr);
                            }
                        });
                        status = "validate";
                    }
                    if (order.get_due() > 0) {
                        status = "alert";
                    }
                }
                return status;
            }
            change_autopay_button(status) {
                console.log("change_autopay_button123w")
                var content = $(this.autopay_html);
                var button_autopay = content.find(".autopay");
                if (status === "validate") {
                    content.show();
                    button_autopay.removeClass("alert");
                    button_autopay.addClass("validate");
                    button_autopay.find(".title").text("Validate");
                } else if (status === "alert") {
                    content.show();
                    button_autopay.removeClass("validate");
                    button_autopay.addClass("alert");
                    button_autopay.find(".title").text("Not enough credits to autopay");
                }
                //console.log("end11111")
            }
            async click_autopay_validation() {
                console.log("click_autopay_validation123w")
                this.env.pos.get_order().autopay_validated = true;
                //this.validate_order();
                await this.validateOrder(true);
            }
            /*is_paid() {
                console.log("is_paid123w")
                var currentOrder = this.pos.get_order();
                return (
                    currentOrder.getPaidTotal() + 0.000001 >=
                    currentOrder.getTotalTaxIncluded()
                );
            }*/
            customer_changed() {
                console.log("customer_changed123w")
                var self = this;
                var client = this.env.pos.get_client();
                var debt = 0;
                var deb_type = 1;
                var debt_type = this.env.pos.config.debt_type;
                if (client) {
                    debt = Math.round(client.debt * 100) / 100;
                    if (debt_type === "credit") {
                        debt = -debt;
                        deb_type = -1;
                    }
                }
                var $js_customer_name = $(".js_customer_name");
                var $pay_full_debt = $(".pay-full-debt");
                $js_customer_name.text(client ? client.name : _t("Customer"));
                $pay_full_debt.unbind().on("click", function() {
                    //console.log("self.pay_full_debt",self,this)
                    self.pay_full_debt();
                });
                //self.pay_full_debt();
                $pay_full_debt.addClass("oe_hidden");
                if (client && debt) {
                    if (debt_type === "debt") {
                        if (debt > 0) {
                            $pay_full_debt.removeClass("oe_hidden");
                            $js_customer_name.append(
                                '<span class="client-debt positive"> [Debt: ' +
                                    this.env.pos.format_currency(debt) +
                                    "]</span>"
                            );
                        } else if (debt < 0) {
                            $js_customer_name.append(
                                '<span class="client-debt negative"> [Debt: ' +
                                    this.env.pos.format_currency(debt) +
                                    "]</span>"
                            );
                        }
                    } else if (debt_type === "credit") {
                        if (debt > 0) {
                            $js_customer_name.append(
                                '<span class="client-credit positive"> [Credit: ' +
                                    this.env.pos.format_currency(debt) +
                                    "]</span>"
                            );
                        } else if (debt < 0) {
                            $pay_full_debt.removeClass("oe_hidden");
                            $js_customer_name.append(
                                '<span class="client-credit negative"> [Credit: ' +
                                    this.env.pos.format_currency(debt) +
                                    "]</span>"
                            );
                        }
                    }
                }
                console.log("thissss000",this);
                var debt_cashregisters = _.filter(this.env.pos.payment_methods, function(cr) {
                    return cr.debt;
                });
                /*
                _.each(debt_cashregisters, function(cr) {
                    var pymt_method_id = cr.id;
                    //var pm_button = self.el.find("div[data-id=" + pymt_method_id + "]");
                    var pm_button = $(".button[data-id='" + pymt_method_id + "']");
                    pm_button.find("span").remove();
                    if (client && client.debts && client.debts[pymt_method_id]) {
                        var credit_line_html = QWeb.render("CreditNote", {
                            debt: deb_type * client.debts[pymt_method_id].balance,
                            widget: self.env,
                        });
                        pm_button.append(credit_line_html);
                    }
                });
                */
                //var contents = $("#paymentMethodeDebt");
                //console.log("11111111",client);
                //contents.innerHTML = "";

                //_.each(debt_cashregisters, function(cr) {
                //    var pymt_method_id = cr.id;
                //    $("#paymentMethodeDebt").empty();
                //    if (client && client.debts && client.debts[pymt_method_id]) {
                        //if (client.debts[pymt_method_id] == pymt_method_id) {
                //
                //            var credit_line_html = QWeb.render("CreditNote", {
                //                debt: deb_type * client.debts[pymt_method_id].balance,
                //                widget: self.env,
                //            });
                //            contents.append(credit_line_html);
                        //}
                //    }
                //});
                console.log("2222222");
                this.change_autopay_button();
            }
            async selectPayDebt() {
                var partner = this.new_client || this.env.pos.get_client();
                console.log("partner1111",partner);
                if (!partner) {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Unknown customer'),
                        body: this.env._t('You cannot use Debt payment. Select customer first.'),
                    });
                }else if (!partner.debt) {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Error: No Debt Amount'),
                        body: this.env._t('You cannot use Debt payment. There is no Debt Amount to pay.'),
                    });
                }else {
                    await this.pay_full_debt();
                }

                console.log("end-pay-full");

            }







        };

    Registries.Component.extend(PaymentScreen, PosNotebookPaymentScreen);

    return PaymentScreen;
});


        /*
        get currentOrder() {
            console.log("currentOrder");
            return this.env.pos.get_order();
        }
        get paymentLines() {
            console.log("paymentLines");
            return this.currentOrder.get_paymentlines();
        }
        get selectedPaymentLine() {
            console.log("selectedPaymentLine");
            return this.currentOrder.selected_paymentline;
        }
        async selectClient() {
            console.log("selectClient");
            // IMPROVEMENT: This code snippet is repeated multiple times.
            // Maybe it's better to create a function for it.
            const currentClient = this.currentOrder.get_client();
            const { confirmed, payload: newClient } = await this.showTempScreen(
                'ClientListScreen',
                { client: currentClient }
            );
            if (confirmed) {
                this.currentOrder.set_client(newClient);
                this.currentOrder.updatePricelist(newClient);
            }
        }
        addNewPaymentLine({ detail: paymentMethod }) {
            console.log("addNewPaymentLine");
            // original function: click_paymentmethods
            if (this.currentOrder.electronic_payment_in_progress()) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Error'),
                    body: this.env._t('There is already an electronic payment in progress.'),
                });
                return false;
            } else {
                this.currentOrder.add_paymentline(paymentMethod);
                NumberBuffer.reset();
                this.payment_interface = paymentMethod.payment_terminal;
                if (this.payment_interface) {
                    this.currentOrder.selected_paymentline.set_payment_status('pending');
                }
                return true;
            }
        }
        _updateSelectedPaymentline() {
            console.log("_updateSelectedPaymentline");
            if (this.paymentLines.every((line) => line.paid)) {
                this.currentOrder.add_paymentline(this.env.pos.payment_methods[0]);
            }
            if (!this.selectedPaymentLine) return; // do nothing if no selected payment line
            // disable changing amount on paymentlines with running or done payments on a payment terminal
            if (
                this.payment_interface &&
                !['pending', 'retry'].includes(this.selectedPaymentLine.get_payment_status())
            ) {
                return;
            }
            if (NumberBuffer.get() === null) {
                this.deletePaymentLine({ detail: { cid: this.selectedPaymentLine.cid } });
            } else {
                this.selectedPaymentLine.set_amount(NumberBuffer.getFloat());
            }
        }
        toggleIsToInvoice() {
            console.log("toggleIsToInvoice");
            // click_invoice
            this.currentOrder.set_to_invoice(!this.currentOrder.is_to_invoice());
            this.render();
        }
        openCashbox() {
            console.log("openCashbox");
            this.env.pos.proxy.printer.open_cashbox();
        }
        async addTip() {
            console.log("addTip");
            // click_tip
            const tip = this.currentOrder.get_tip();
            const change = this.currentOrder.get_change();
            let value = tip.toFixed(this.env.pos.decimals);

            if (tip === 0 && change > 0) {
                value = change;
            }

            const { confirmed, payload } = await this.showPopup('NumberPopup', {
                title: tip ? this.env._t('Change Tip') : this.env._t('Add Tip'),
                startingValue: value,
            });

            if (confirmed) {
                this.currentOrder.set_tip(parse.float(payload));
            }
        }
        deletePaymentLine(event) {
            console.log("deletePaymentLine");
            const { cid } = event.detail;
            const line = this.paymentLines.find((line) => line.cid === cid);

            // If a paymentline with a payment terminal linked to
            // it is removed, the terminal should get a cancel
            // request.
            if (['waiting', 'waitingCard', 'timeout'].includes(line.get_payment_status())) {
                line.payment_method.payment_terminal.send_payment_cancel(this.currentOrder, cid);
            }

            this.currentOrder.remove_paymentline(line);
            NumberBuffer.reset();
            this.render();
        }
        selectPaymentLine(event) {
            console.log("selectPaymentLine");
            const { cid } = event.detail;
            const line = this.paymentLines.find((line) => line.cid === cid);
            this.currentOrder.select_paymentline(line);
            NumberBuffer.reset();
            this.render();
        }
        async validateOrder(isForceValidate) {
            console.log("validateOrder");
            if (await this._isOrderValid(isForceValidate)) {
                // remove pending payments before finalizing the validation
                for (let line of this.paymentLines) {
                    if (!line.is_done()) this.currentOrder.remove_paymentline(line);
                }
                await this._finalizeValidation();
            }
        }
        async _finalizeValidation() {
            console.log("_finalizeValidation");
            if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
                this.env.pos.proxy.printer.open_cashbox();
            }

            this.currentOrder.initialize_validation_date();
            this.currentOrder.finalized = true;

            let syncedOrderBackendIds = [];

            try {
                if (this.currentOrder.is_to_invoice()) {
                    syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
                        this.currentOrder
                    );
                } else {
                    syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
                }
            } catch (error) {
                if (error instanceof Error) {
                    throw error;
                } else {
                    await this._handlePushOrderError(error);
                }
            }
            if (syncedOrderBackendIds.length && this.currentOrder.wait_for_push_order()) {
                const result = await this._postPushOrderResolve(
                    this.currentOrder,
                    syncedOrderBackendIds
                );
                if (!result) {
                    await this.showPopup('ErrorPopup', {
                        title: 'Error: no internet connection.',
                        body: error,
                    });
                }
            }

            this.showScreen(this.nextScreen);

            // If we succeeded in syncing the current order, and
            // there are still other orders that are left unsynced,
            // we ask the user if he is willing to wait and sync them.
            if (syncedOrderBackendIds.length && this.env.pos.db.get_orders().length) {
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Remaining unsynced orders'),
                    body: this.env._t(
                        'There are unsynced orders. Do you want to sync these orders?'
                    ),
                });
                if (confirmed) {
                    // NOTE: Not yet sure if this should be awaited or not.
                    // If awaited, some operations like changing screen
                    // might not work.
                    this.env.pos.push_orders();
                }
            }
        }
        get nextScreen() {
            console.log("nextScreen");
            return 'ReceiptScreen';
        }
        async _isOrderValid(isForceValidate) {
            console.log("_isOrderValid");
            if (this.currentOrder.get_orderlines().length === 0) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Empty Order'),
                    body: this.env._t(
                        'There must be at least one product in your order before it can be validated'
                    ),
                });
                return false;
            }

            if (this.currentOrder.is_to_invoice() && !this.currentOrder.get_client()) {
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Please select the Customer'),
                    body: this.env._t(
                        'You need to select the customer before you can invoice an order.'
                    ),
                });
                if (confirmed) {
                    this.selectClient();
                }
                return false;
            }

            if (!this.currentOrder.is_paid() || this.invoicing) {
                return false;
            }

            if (this.currentOrder.has_not_valid_rounding()) {
                var line = this.currentOrder.has_not_valid_rounding();
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Incorrect rounding'),
                    body: this.env._t(
                        'You have to round your payments lines.' + line.amount + ' is not rounded.'
                    ),
                });
                return false;
            }

            // The exact amount must be paid if there is no cash payment method defined.
            if (
                Math.abs(
                    this.currentOrder.get_total_with_tax() - this.currentOrder.get_total_paid()  + this.currentOrder.get_rounding_applied()
                ) > 0.00001
            ) {
                var cash = false;
                for (var i = 0; i < this.env.pos.payment_methods.length; i++) {
                    cash = cash || this.env.pos.payment_methods[i].is_cash_count;
                }
                if (!cash) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Cannot return change without a cash payment method'),
                        body: this.env._t(
                            'There is no cash payment method available in this point of sale to handle the change.\n\n Please pay the exact amount or add a cash payment method in the point of sale configuration'
                        ),
                    });
                    return false;
                }
            }

            // if the change is too large, it's probably an input error, make the user confirm.
            if (
                !isForceValidate &&
                this.currentOrder.get_total_with_tax() > 0 &&
                this.currentOrder.get_total_with_tax() * 1000 < this.currentOrder.get_total_paid()
            ) {
                this.showPopup('ConfirmPopup', {
                    title: this.env._t('Please Confirm Large Amount'),
                    body:
                        this.env._t('Are you sure that the customer wants to  pay') +
                        ' ' +
                        this.env.pos.format_currency(this.currentOrder.get_total_paid()) +
                        ' ' +
                        this.env._t('for an order of') +
                        ' ' +
                        this.env.pos.format_currency(this.currentOrder.get_total_with_tax()) +
                        ' ' +
                        this.env._t('? Clicking "Confirm" will validate the payment.'),
                }).then(({ confirmed }) => {
                    if (confirmed) this.validateOrder(true);
                });
                return false;
            }

            return true;
        }
        async _postPushOrderResolve(order, order_server_ids) {
            console.log("_postPushOrderResolve");
            return true;
        }
        async _sendPaymentRequest({ detail: line }) {
            console.log("_sendPaymentRequest");
            // Other payment lines can not be reversed anymore
            this.paymentLines.forEach(function (line) {
                line.can_be_reversed = false;
            });

            const payment_terminal = line.payment_method.payment_terminal;
            line.set_payment_status('waiting');

            const isPaymentSuccessful = await payment_terminal.send_payment_request(line.cid);
            if (isPaymentSuccessful) {
                line.set_payment_status('done');
                line.can_be_reversed = this.payment_interface.supports_reversals;
            } else {
                line.set_payment_status('retry');
            }
        }
        async _sendPaymentCancel({ detail: line }) {
            console.log("_sendPaymentCancel");
            const payment_terminal = line.payment_method.payment_terminal;
            line.set_payment_status('waitingCancel');
            const isCancelSuccessful = await payment_terminal.send_payment_cancel(this.currentOrder, line.cid);
            if (isCancelSuccessful) {
                line.set_payment_status('retry');
            } else {
                line.set_payment_status('waitingCard');
            }
        }
        async _sendPaymentReverse({ detail: line }) {
            console.log("_sendPaymentReverse");
            const payment_terminal = line.payment_method.payment_terminal;
            line.set_payment_status('reversing');

            const isReversalSuccessful = await payment_terminal.send_payment_reversal(line.cid);
            if (isReversalSuccessful) {
                line.set_amount(0);
                line.set_payment_status('reversed');
            } else {
                line.can_be_reversed = false;
                line.set_payment_status('done');
            }
        }
        async _sendForceDone({ detail: line }) {
            console.log("_sendForceDone");
            line.set_payment_status('done');
        }
        _onPrevOrder(prevOrder) {
            console.log("_onPrevOrder");
            prevOrder.off('change', null, this);
            prevOrder.paymentlines.off('change', null, this);
            if (prevOrder) {
                prevOrder.stop_electronic_payment();
            }
        }
        async _onNewOrder(newOrder) {
            console.log("_onNewOrder");
            newOrder.on('change', this.render, this);
            newOrder.paymentlines.on('change', this.render, this);
            NumberBuffer.reset();
            await this.render();
        }
        */
