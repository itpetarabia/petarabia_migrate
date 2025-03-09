/* Copyright 2016-2018 Ivan Yelizariev <https://it-projects.info/team/yelizariev>
 * Copyright 2016-2017 Stanislav Krotov <https://it-projects.info/team/ufaks>
 * Copyright 2017 Artyom Losev
 * Copyright 2017-2018 Gabbasov Dinar <https://it-projects.info/team/GabbasovDinar>
 * Copyright 2018 Kolushov Alexandr <https://it-projects.info/team/KolushovAlexandr>
 * License MIT (https://opensource.org/licenses/MIT). */
/* eslint complexity: "off"*/
odoo.define("pos_debt_notebook.pos", function(require) {
    "use strict";

    var models = require("point_of_sale.models");
    //var screens = require("point_of_sale.screens");
    const core = require("web.core");
    //var gui = require("point_of_sale.gui");
    var utils = require("web.utils");
    var rpc = require("web.rpc");
    //var PopupWidget = require("point_of_sale.popups");
    const ClientListScreen = require('point_of_sale.ClientListScreen');

    var QWeb = core.qweb;
    var _t = core._t;
    var round_pr = utils.round_precision;

    var _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function(attributes) {
            //console.log("initialize123w")
            this.reload_debts_partner_ids = [];
            this.reload_debts_timer = $.when();
            models.load_fields("pos.payment.method", [
                "debt",
                "debt_limit",
                "credits_via_discount",
                "pos_cash_out",
                "category_ids",
                "credits_autopay",
            ]);
            models.load_fields("product.product", ["credit_product"]);
            _super_posmodel.initialize.apply(this, arguments);
        },

        after_load_server_data: function() {
            //console.log("after_load_server_data123w")
            var self = this;
            var partner_ids = _.map(this.partners, function(p) {
                return p.id;
            });

            var done = new $.Deferred();

            var progress = (this.models.length - 0.5) / this.models.length;
            //this.chrome.loading_message(_t("Loading Credits data"), progress);
            this.reload_debts(partner_ids, 0, {postpone: false}).then(function() {
                var result = _super_posmodel.after_load_server_data.apply(
                    self,
                    arguments
                );
                done.resolve();
                return result;
            });
            return done;
        },
        _save_to_server: function(orders, options) {
            //console.log("_save_to_server123w",orders)
            var self = this;
            var def = _super_posmodel._save_to_server.apply(this, arguments);
            var partner_ids = [];
            _.each(orders, function(o) {
                if (o.data.updates_debt && o.data.partner_id) {
                    partner_ids.push(o.data.partner_id);
                }
            });
            //console.log("03333");
            partner_ids = _.unique(partner_ids);
            if (partner_ids.length) {
                return def.then(function(server_ids) {
                    self.reload_debts(partner_ids);
                    return server_ids;
                });
            }
            return def;
        },
        reload_debts: function(partner_ids, limit, options) {
            //console.log("reload_debts123w",partner_ids, limit, options)
            /**
             @param {Array} partner_ids
             @param {Number} limit
             @param {Object} options
               * "shadow" - set true to load in background (i.e. without blocking the screen). Default is True
               * "postpone" - make a short delay before actual requesting to
                 gather partner_ids from other calls and request them at once.
                 Default is true

             **/

            // FIXME: on multiple calls limit value from last call is conly used.
            // We probably need to have different partner_ids list (like reload_debts_partner_ids) for each limit value, e.g.
            // limit=0 -> partner_ids=[1,2,3]
            // limit=10 -> partner_ids = [1, 101, 102, 103]
            //
            // As for shadow it seems ok to use last value

            var self = this;
            // Function is called whenever we need to update debt value from server
            if (typeof limit === "undefined") {
                limit = 10;
            }
            //console.log("0111",partner_ids,partner_ids.length,limit);
            if (partner_ids.length === 1 && !limit) {
                // Incoming data about balance updates not contains limit
                // this block changes limit only in case of opened debt history for a partner who have got an update
                //var client_list_screen = this.gui.screen_instances.clientlist;
                ////console.log("0111");
                //if (client_list_screen && client_list_screen.debt_history_is_opened()) {
                //    var partner = client_list_screen.new_client || this.env.pos.get_client();
                //    if (partner && partner_ids[0] === partner.id) {
                //        limit =
                //            client_list_screen.history_length ||
                //            client_list_screen.debt_history_limit_initial;
                //    }
                //}

                /*//console.log("ClientListScreennnn",ClientListScreen);
                if (ClientListScreen && ClientListScreen.debt_history_is_opened()) {
                    var partner = ClientListScreen.new_client || this.env.pos.get_client();
                    if (partner && partner_ids[0] === partner.id) {
                        limit =
                            ClientListScreen.history_length ||
                            ClientListScreen.debt_history_limit_initial;
                    }
                }
                /////////////////////////////////*/
                limit = 10
                //console.log("0222",partner_ids);
            }
            options = options || {};
            if (typeof options.postpone === "undefined") {
                options.postpone = true;
            }
            if (typeof options.shadow === "undefined") {
                options.shadow = true;
            }
            var download_debts_ready = options.deferred || $.Deferred();
            this.reload_debts_partner_ids = this.reload_debts_partner_ids.concat(
                partner_ids
            );
            if (options.postpone && this.reload_debts_timer.state() === "resolved") {
                ////console.log("timeout")
                // Add timeout to gather requests before reloading
                var reload_ready_def = $.Deferred();
                this.reload_debts_timer = reload_ready_def;
                setTimeout(
                    function() {
                        reload_ready_def.resolve();
                    },
                    typeof options.postpone === "number" ? options.postpone : 1000
                );
            }
            ////console.log("reload_debts_timer111111",options)
            self._load_debts(partner_ids, limit, options)
            .then(function(data) {
                                // Success
                                ////console.log("testttttt22");
                                download_debts_ready.resolve();
                                self._on_load_debts(data);
                            })
            this.reload_debts_timer = this.reload_debts_timer.then(function() {
                ////console.log("reload_debts_timer")
                if (self.reload_debts_partner_ids.length > 0) {
                    var load_partner_ids = _.uniq(
                        self.reload_debts_partner_ids.splice(0)
                    );
                    var new_partners = _.any(load_partner_ids, function(id) {
                        return !self.db.get_partner_by_id(id);
                    });
                    var def = $.Deferred();
                    if (new_partners) {
                        self.load_new_partners().always(function() {
                            // In case this function was called from saved_client_details load_new_partners may work asynchronously
                            // because saved_client_details works with deferred objects but returns nothing, so we cannot wait for it
                            // rejection means that all new partners data was already previously updated, otherwise, they were updated now
                            // related PR: https://github.com/odoo/odoo/pull/26220
                            def.resolve();
                        });
                    } else {
                        def.resolve();
                    }
                    /*return def.then(function() {
                        var request_finished = $.Deferred();
                        ////console.log("self._load_debts13",load_partner_ids, limit, options);
                        self._load_debts(load_partner_ids, limit, options)
                            .then(function(data) {
                                // Success
                                download_debts_ready.resolve();
                                self._on_load_debts(data);
                            })
                            .always(function() {
                                // Allow to do next call
                                request_finished.resolve();
                            })
                            .fail(function() {
                                // Make request again, Timeout is set to allow properly work in offline mode
                                self.reload_debts(load_partner_ids, 0, {
                                    postpone: 4000,
                                    shadow: false,
                                    deferred: download_debts_ready,
                                });
                                self.trigger("updateDebtHistoryFail");
                            });
                        return request_finished;
                    });*/
                    return def.then(function () {
                        var request_finished = $.Deferred();

                        self._load_debts(load_partner_ids, limit, options).then(
                            function (data) {
                                // Success
                                download_debts_ready.resolve();
                                request_finished.resolve();
                                self._on_load_debts(data);
                            },
                            function () {
                                // Make request again, Timeout is set to allow properly work in offline mode
                                request_finished.resolve();
                                self.reload_debts(load_partner_ids, 0, {
                                    postpone: 4000,
                                    shadow: false,
                                    deferred: download_debts_ready,
                                });
                                self.trigger("updateDebtHistoryFail");
                            }
                        );
                        return request_finished;
                    });
                }
                return download_debts_ready.resolve();
            });
            ////console.log("timerrendddd",this)
            //this.pos.update_debt_history(partner_ids);
            return download_debts_ready;
        },
        _load_debts: function(partner_ids, limit, options) {
            //console.log("_load_debts123w321",partner_ids, limit, options)
            return rpc
                .query({
                    model: "res.partner",
                    method: "debt_history",
                    args: [partner_ids, limit],
                })
                .then(function(res) {
                    return res;
                });
        },
        _on_load_debts: function(debts) {
            //console.log("_on_load_debts123w",this,debts);
            var self = this;
            var partner_ids = _.map(debts, function(debt) {
                return debt.partner_id;
            });
            _.each(_.values(debts), function(deb) {
                ////console.log("deb",deb);
                var partner = self.db.get_partner_by_id(deb.partner_id);
                if (partner) {
                    ////console.log("deb",deb,partner)
                    partner.debt = deb.debt;
                    ////console.log("deb222222",deb.history)
                    partner.debts = deb.debts;
                    partner.records_count = deb.records_count;
                    if (deb.history && deb.history.length) {
                        // That condition prevent from rewriting partners history to nothing
                        partner.history = deb.history;
                    }
                }
                ////console.log("partner000",partner);
            });
            this.trigger("updateDebtHistory", partner_ids);
        },
        //thumb_up_animation: function() {
        //    this.gui.show_popup("thumb-up");
        //},
    });

    var _super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function(attributes,options) {
            //console.log("initialize22123w")
            this.on(
                "change:client",
                function() {
                    // Reload debt history whenever we set customer,
                    // because debt value can be obsolete due to network issues
                    // and pos_longpolling status is not 100% gurantee
                    var client = this.get_client();
                    if (client) {
                        // Reload only debt value, use background mode, send request immediatly
                        this.pos.reload_debts([client.id], 0, {postpone: false});
                    }
                },
                this
            );
            return _super_order.initialize.apply(this, arguments);
        },

        updates_debt: function() {
            //console.log("updates_debt123w")
            // Wheither order update debt value
            return this.has_credit_product() || this.has_debt_journal();
        },
        has_debt_journal: function() {
            //console.log("has_debt_journal123w")
            return this.paymentlines.any(function(line) {
                //return line.cashregister.journal.debt;
                ////console.log("ffffff",line)
                return line.payment_method.debt;
            });
        },
        has_paymentlines_with_credits_via_discounts: function() {
            //console.log("has_paymentlines_with_credits_via_discounts123w")
            return _.filter(this.get_paymentlines(), function(pl) {
                //return pl.cashregister.journal.credits_via_discount;
                ////console.log("hhhhhhhh",pl.payment_method.credits_via_discount)
                return pl.payment_method.credits_via_discount;
            });
        },
        has_credit_product: function() {
            //console.log("has_credit_product123w123",this);
            return this.orderlines.any(function(line) {
                return line.product.credit_product;
            });
        },
        has_return_product: function() {
            //console.log("has_return_product123w321")
            return this.get_orderlines().some(function(line) {
                return line.quantity < 0;
            });
        },
        get_debt_delta: function() {
            //console.log("get_debt_delta123w123",this);
            var debt_amount = 0;
            var plines = this.get_paymentlines();
            for (var i = 0; i < plines.length; i++) {
                //if (plines[i].cashregister.journal.debt) {
                if (plines[i].payment_method.debt) {
                    debt_amount += plines[i].amount;
                }
            }
            this.orderlines.each(function(line) {
                if (line.product.credit_product) {
                    debt_amount -= line.get_price_with_tax();
                }
            });
            return debt_amount;
        },
        export_as_JSON: function() {
            //console.log("export_as_JSON123w")
            var data = _super_order.export_as_JSON.apply(this, arguments);
            data.updates_debt = this.updates_debt();
            return data;
        },
        export_for_printing: function() {
            //console.log("export_for_printing123w")
            var data = _super_order.export_for_printing.apply(this, arguments);
            var client = this.get_client();
            if (client) {
                var rounding = this.pos.currency.rounding;
                data.debt_before = round_pr(this.debt_before, rounding);
                data.debt_after = round_pr(this.debt_after, rounding);
                data.debt_type = this.pos.config.debt_type;
            }
            return data;
        },
        get_payment_limits: function(payment_method, limit_code) {
            //console.log("get_payment_limits123w")
            // By default with one first argument returns all limits of the cashregister
            // Output may be changed from all limits to a one particular limit by setting the second string argument
            // Available atributes 'debt_limit', 'products_restriction', 'due' and 'all' is default
            // 'debt_limit' = partner balance + debt limit
            // 'products_restriction' = sum of resticted products only
            // 'due' = remained amount to pay
            limit_code = limit_code || "all";
            var vals = {};
            if (payment_method.debt) {
                var partner_balance = this.get_client().debts[
                        payment_method.id
                    ].balance,
                    category_list = payment_method.category_ids;
                var debt_limit = round_pr(
                    partner_balance + payment_method.debt_limit,
                    this.pos.currency.rounding
                );
                if (limit_code === "debt_limit" || limit_code === "all") {
                    vals.debt_limit = debt_limit;
                }
                if (
                    category_list.length &&
                    (limit_code === "products_restriction" || limit_code === "all")
                ) {
                    vals.products_restriction = this.get_summary_for_categories(
                        category_list
                    );
                }
            }
            if (limit_code === "due" || limit_code === "all") {
                vals.due = this.get_due();
            }
            return vals;
        },
        get_summary_for_cashregister: function(payment_method) {
            //console.log("get_summary_for_cashregister1111123w",this)
            return this.paymentlines.models.reduce(function(memo, pl) {
                ////console.log("get_summary_for_cashregister000",pl)
                if (pl.payment_method.id === payment_method.id) {
                    return memo + pl.amount;
                }
                return memo;
                }, 0);

            /*return _.reduce(
                this.paymentlines.models,
                function(memo, pl) {
                    //console.log("get_summary_for_cashregister",pl)
                    if (pl.cashregister.journal_id[0] === payment_method.id) {
                        return memo + pl.amount;
                    }
                    return memo;
                },
                0
            );*/
            ////console.log("get_summary_for_cashregister2222")
        },
        get_summary_for_categories: function(category_list) {
            //console.log("get_summary_for_categories123w123",this);
            var self = this;
            return round_pr(
                _.reduce(
                    this.orderlines.models,
                    function(memo, ol) {
                        category_list = _.union(
                            category_list,
                            _.flatten(
                                _.map(category_list, function(cl) {
                                    return self.pos.db.get_category_childs_ids(cl);
                                })
                            )
                        );
                        // Compatibility with pos_category_multi
                        var product_categories = [];
                        if (ol.product.pos_categ_id) {
                            product_categories = [ol.product.pos_categ_id[0]];
                        } else {
                            product_categories = ol.product.pos_category_ids;
                        }

                        if (_.intersection(category_list, product_categories).length) {
                            return memo + ol.get_price_with_tax();
                        }
                        return memo;
                    },
                    0
                ),
                this.pos.currency.rounding
            );
        },
        get_summary_for_discount_credits: function() {
            //console.log("get_summary_for_discount_credits123w")
            var paymentlines = this.get_paymentlines();
            return _.reduce(
                paymentlines,
                function(memo, pl) {
                    //if (pl.cashregister.journal.credits_via_discount) {
                    if (pl.payment_method.credits_via_discount) {
                        return memo + pl.get_amount();
                    }
                    return memo;
                },
                0
            );
        },
        //edit
        add_paymentline: function(payment_method) {

            //console.log("add_paymentline123w",payment_method)
            this.assert_editable();
            var self = this;
            var payment_method = payment_method;
            if (!this.get_client() && (this.has_credit_product() || payment_method.debt)) {
                //setTimeout(function() {
                //    self.pos.gui.show_screen("clientlist");
                //}, 30);
            }
            var due = this.get_due_debt();

            //var newPaymentline = new exports.Paymentline({},{order: this, payment_method:payment_method, pos: this.pos});
            var newPaymentline = new models.Paymentline(
                {},
                {
                    order: this,
                    payment_method: payment_method,
                    pos: this.pos,
                }
            );
            if (payment_method.debt && this.get_client()) {
                //console.log("add_paymentline1111111",due)
                if (due < 0) {
                    newPaymentline.set_amount(due);
                } else {

                    var limits = this.get_payment_limits(payment_method, "all");

                    newPaymentline.set_amount(
                        Math.max(
                            Math.min.apply(null, _.values(limits)) -
                                this.get_summary_for_cashregister(payment_method),
                            0
                        )
                    );
                    newPaymentline.set_amount(due);
                    //console.log("add_paymentline22222",due)
                }
            } else if (due < 0) {
                //console.log("newPaymentline.set_amount(due)")
                newPaymentline.set_amount(due);
            } else {
                //console.log("add_paymentline.apply()")
                return _super_order.add_paymentline.apply(this, arguments);
            }

            this.paymentlines.add(newPaymentline);
            this.select_paymentline(newPaymentline);
            $(this.autopay_html).hide();
            //extra fkp - 9 apr 2022 // to fix error 'There is already an electronic payment in progress'.
            return newPaymentline;
            //
        },
        get_due_debt: function(paymentline) {
            //console.log("get_due_debt123w",paymentline)
            var due = this.get_total_with_tax() - this.get_total_paid() + this.get_rounding_applied();
            //var due = this.get_total_with_tax() - this.get_total_paid();
            if (paymentline) {
                due = this.get_total_with_tax();
                var lines = this.paymentlines.models;
                for (var i = 0; i < lines.length; i++) {
                    if (lines[i] === paymentline) {
                        break;
                    } else {
                        due -= lines[i].get_amount();
                    }
                }
            }
            return round_pr(due, this.pos.currency.rounding);
        },
    });
    /*
    screens.PaymentScreenWidget.include({
        init: function(parent, options) {
            //console.log("init33123w")
            this._super(parent, options);
            this.pos.on(
                "updateDebtHistory",
                function(partner_ids) {
                    this.update_debt_history(partner_ids);
                },
                this
            );
        },
        update_debt_history: function(partner_ids) {
            //console.log("update_debt_history123w")
            var client = this.pos.get_client();
            if (client && $.inArray(client.id, partner_ids) !== -1) {
                this.gui.screen_instances.products.actionpad.renderElement();
                this.customer_changed();
            }
        },
        validate_order: function(options) {
            //console.log("validate_order123w")
            var currentOrder = this.pos.get_order();
            var zero_paymentlines = _.filter(currentOrder.get_paymentlines(), function(
                p
            ) {
                return p.amount === 0;
            });
            _.each(zero_paymentlines, function(p) {
                currentOrder.remove_paymentline(p);
            });
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
                this.gui.show_popup("error", {
                    title: _t("Unknown customer"),
                    body: _t("You cannot use Debt payment. Select customer first."),
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
                    this.gui.show_popup("error", {
                        title: _t(
                            "Unable to validate with the " +
                                paymentlines_with_credits_via_discounts_text +
                                " payment method"
                        ),
                        body: _t(
                            "You cannot use " +
                                paymentlines_with_credits_via_discounts_text +
                                " for products with taxes. Use an another payment method, or pay the full price with only discount credits"
                        ),
                    });
                    return;
                }
                if (currentOrder.has_credit_product()) {
                    this.gui.show_popup("error", {
                        title: _t(
                            "Unable to validate with the " +
                                paymentlines_with_credits_via_discounts_text +
                                " payment method"
                        ),
                        body: _t(
                            "You cannot use " +
                                paymentlines_with_credits_via_discounts_text +
                                " for credit top-up products. Use an another non-discount payment method"
                        ),
                    });
                    return;
                }
            }
            if (
                !currentOrder.get_paymentlines().length &&
                currentOrder.has_return_product()
            ) {
                this.gui.show_popup("error", {
                    title: _t("Unable to validate return order"),
                    body: _t("Specify Payment Method"),
                });
                return;
            }
            if (currentOrder.has_credit_product() && !client) {
                this.gui.show_popup("error", {
                    title: _t("Unknown customer"),
                    body: _t("Don't forget to specify Customer when sell Credits."),
                });
                return;
            }
            if (isDebt && currentOrder.get_orderlines().length === 0) {
                this.gui.show_popup("error", {
                    title: _t("Empty Order"),
                    body: _t(
                        "There must be at least one product in your order before it can be validated. (Hint: you can use some dummy zero price product)"
                    ),
                });
                return;
            }
            var exceeding_debts = this.exceeding_debts_check();
            if (client && exceeding_debts) {
                this.gui.show_popup("error", {
                    title: _t("Max Debt exceeded"),
                    body: _t(
                        "You cannot sell products on credit payment method " +
                            exceeding_debts +
                            " to the customer because its max debt value will be exceeded."
                    ),
                });
                return;
            }
            if (this.debt_change_check()) {
                this.gui.show_popup("error", {
                    title: _t(
                        "Unable to return the change or cash out with the debt payment method"
                    ),
                    body: _t(
                        "Please enter the exact or lower debt amount than the cost of the order."
                    ),
                });
                return;
            }
            var violations = this.debt_journal_restricted_categories_check();
            //console.log("violations",violations)
            if (violations.length) {
                this.gui.show_popup("error", {
                    title: _t("Unable to validate with the debt payment method"),
                    body: _t(this.restricted_categories_message(violations)),
                });
                return;
            }
            if (client)
                this.pos.gui.screen_instances.clientlist.partner_cache.clear_node(
                    client.id
                );
            this._super(options);
        },
        finalize_validation: function() {
            //console.log("finalize_validation123w")
            var self = this;
            var order = this.pos.get_order(),
                paymentlines = order.get_paymentlines(),
                partner = this.pos.get_client();
            var debt_pl = _.filter(paymentlines, function(pl) {
                //return pl.cashregister.journal.debt;
                return pl.payment_method.debt;
            });
            if (debt_pl && partner) {
                order.has_paymentlines_with_credits_via_discounts();
                this._super();
                // Offline updating of credits, on a restored network this data will be replaced by the servers one
                _.each(debt_pl, function(pl) {
                    //partner.debts[pl.cashregister.journal.id].balance -= pl.amount;
                    ////console.log("l1",pl);
                    partner.debts[pl.payment_method.id].balance -= pl.amount;
                    partner.debt += pl.amount;
                });
            } else {
                this._super();
            }
            var debt_prod = _.filter(order.get_orderlines(), function(ol) {
                return ol.product.credit_product;
            });
            if (debt_prod) {
                var value = 0;
                _.each(debt_prod, function(dp) {
                    value = round_pr(
                        dp.quantity * dp.price,
                        self.pos.currency.rounding
                    );
                    partner.debts[dp.product.credit_product[0]].balance += value;
                    partner.debt -= value;
                });
            }
        },
        get_used_debt_cashregisters: function(paymentlines) {
            //console.log("get_used_debt_cashregisters123w")
            paymentlines = paymentlines || this.pos.get_order().get_paymentlines();
            var cashregisters = _.uniq(
                _.map(paymentlines, function(pl) {
                    ////console.log("l3",pl);
                    return pl.payment_method;
                })
            );
            return _.filter(cashregisters, function(cr) {
                //return cr.journal.debt;
                ////console.log("l2",cr)
                return cr.debt;
            });
        },
        restricted_categories_message: function(cashregisters) {
            //console.log("restricted_categories_message123w")
            var self = this;
            var body = [];
            var categ_names = [];
            _.each(cashregisters, function(cr) {
                ////console.log("l4",cr)
                var pymt_method = cr;
                _.each(pymt_method.category_ids, function(categ) {
                    categ_names.push(self.pos.db.get_category_by_id(categ).name);
                });
                //body.push(categ_names.join(", ") + " with " + cr.journal_id[1] + " ");
                body.push(categ_names.join(", ") + " with " + cr + " ");
            });
            // TODO we can make a better formatting here
            return "You may only buy " + body.toString();
        },
        debt_journal_restricted_categories_check: function() {
            //console.log("debt_journal_restricted_categories_check123w")
            var self = this;
            var cashregisters = this.get_used_debt_cashregisters();
            ////console.log("cashregisters",cashregisters)
            cashregisters = _.filter(cashregisters, function(cr) {
                ////console.log("crrrrr",cr)
                return cr.category_ids.length > 0;
            });
            var violations = [];
            _.each(cashregisters, function(cr) {
                if (self.restricted_products_check(cr)) {
                    violations.push(cr);
                }
            });
            return violations;
        },
        check_discount_credits_for_taxed_products: function() {
            //console.log("check_discount_credits_for_taxed_products123w")
            var order = this.pos.get_order(),
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
        },
        restricted_products_check: function(cr) {
            //console.log("restricted_products_check123w")
            var order = this.pos.get_order();
            var sum_pl = round_pr(
                order.get_summary_for_cashregister(cr),
                this.pos.currency.rounding
            );
            ////console.log("l5")
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
        },
        cash_out_check: function() {
            //console.log("cash_out_check123w")
            var order = this.pos.get_order();
            if (
                order.get_orderlines().length === 1 &&
                this.pos.config.debt_dummy_product_id &&
                order.get_orderlines()[0].product.id ===
                    this.pos.config.debt_dummy_product_id[0]
            ) {
                return true;
            }
            return false;
        },
        exceeding_debts_check: function() {
            //console.log("exceeding_debts_check123w")
            var order = this.pos.get_order(),
                flag = false;
            if (this.pos.get_client()) {
                _.each(this.get_used_debt_cashregisters(), function(cr) {
                    var limits = order.get_payment_limits(cr, "debt_limit");
                    var sum_pl = order.get_summary_for_cashregister(cr);
                    ////console.log("l6",cr,cr.debt_limit)
                    // No need to check that debt_limit is in limits by the reason of get_payment_limits definition
                    if (cr.debt_limit > 0 && sum_pl > limits.debt_limit) {
                        //flag = cr.journal_id[1];
                        flag = cr.name;
                    }
                });
                return flag;
            }
        },
        debt_change_check: function() {
            //console.log("debt_change_check123w")
            var order = this.pos.get_order(),
                paymentlines = order.get_paymentlines();
            ////console.log("paymentlines",paymentlines)
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
        },

        pay_full_debt: function(){
    		//console.log("pay_full_debt Extended123w");
    		var self = this;
    		//this._super();
    		var total_debt_balance = this.get_debt_balance();
    		////console.log("total_debt_balance=",total_debt_balance);
    		this.gui.show_popup('number',{
                'title': _t('Pay Debt'),
                'value': Math.abs(total_debt_balance),
                'confirm': function(debt_input) {
                	////console.log("Debt Input=",debt_input);
                    //val = Math.round(Math.max(0,Math.min(100,val)));
                    //self.apply_discount(val);
                	if (debt_input <= 0 || debt_input > Math.abs(total_debt_balance)){
                		this.gui.show_popup('error',{
                            'title': _t('Error: Debt Amount Exceeded'),
                            'body': _t('The entered amount '+ String(debt_input) +' is greater than debt. Maximum debt is '+String(Math.abs(total_debt_balance))),
                        });
                		return;
                	}
                	else{
                		self.pay_full_debt_inherited(debt_input);
                	}


                },
            });

    	},
    	//org function = pay_full_debt
    	pay_full_debt_inherited: function(debt_input){
    		//console.log("pay_full_debt_inherited=123w");
    		debt_input = Math.abs(debt_input);
            var self = this;
            var order = this.pos.get_order();
            if (order && !order.orderlines.length && this.pos.config.debt_dummy_product_id){
                order.add_product(
                    this.pos.db.get_product_by_id(this.pos.config.debt_dummy_product_id[0]),
                    {'price': 0}
                );
            }

            var paymentLines = order.get_paymentlines();
            ////console.log("paymentLines=",paymentLines);
            if (paymentLines.length) {
                _.each(paymentLines, function(paymentLine) {
                    if (paymentLine && paymentLine.payment_method.debt){
                        paymentLine.destroy();
                    }
                });
            }


            var debts = order.get_client().debts;
            _.each(debts, function(debt) {
                if (debt.balance < 0) {
                    var newDebtPaymentline = new models.Paymentline({},{
                        pos: self.pos,
                        order: order,
                        payment_method: _.find(self.pos.payment_methods, function(cr){
                            //return cr.journal_id[0] === debt.journal_id[0];
                            return cr.id === debt.payment_method_id[0];
                        })
                    });
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
                    }
                }
            });

            this.render_paymentlines();
        },

        get_debt_balance:function(){
            //console.log("get_debt_balance123w")
    		var self = this;
            var order = this.pos.get_order();

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
    	},
        is_paid: function() {
            //console.log("is_paid123w")
            var currentOrder = this.pos.get_order();
            return (
                currentOrder.getPaidTotal() + 0.000001 >=
                currentOrder.getTotalTaxIncluded()
            );
        },
        customer_changed: function() {
            //console.log("customer_changed123w")
            var self = this;
            var client = this.pos.get_client();
            var debt = 0;
            var deb_type = 1;
            var debt_type = this.pos.config.debt_type;
            if (client) {
                debt = Math.round(client.debt * 100) / 100;
                if (debt_type === "credit") {
                    debt = -debt;
                    deb_type = -1;
                }
            }
            var $js_customer_name = this.$(".js_customer_name");
            var $pay_full_debt = this.$(".pay-full-debt");
            $js_customer_name.text(client ? client.name : _t("Customer"));
            $pay_full_debt.unbind().on("click", function() {
                ////console.log("self.pay_full_debt",self,this)
                self.pay_full_debt();
            });
            $pay_full_debt.addClass("oe_hidden");
            if (client && debt) {
                if (debt_type === "debt") {
                    if (debt > 0) {
                        $pay_full_debt.removeClass("oe_hidden");
                        $js_customer_name.append(
                            '<span class="client-debt positive"> [Debt: ' +
                                this.format_currency(debt) +
                                "]</span>"
                        );
                    } else if (debt < 0) {
                        $js_customer_name.append(
                            '<span class="client-debt negative"> [Debt: ' +
                                this.format_currency(debt) +
                                "]</span>"
                        );
                    }
                } else if (debt_type === "credit") {
                    if (debt > 0) {
                        $js_customer_name.append(
                            '<span class="client-credit positive"> [Credit: ' +
                                this.format_currency(debt) +
                                "]</span>"
                        );
                    } else if (debt < 0) {
                        $pay_full_debt.removeClass("oe_hidden");
                        $js_customer_name.append(
                            '<span class="client-credit negative"> [Credit: ' +
                                this.format_currency(debt) +
                                "]</span>"
                        );
                    }
                }
            }
            var debt_cashregisters = _.filter(this.pos.payment_methods, function(cr) {
                return cr.debt;
            });
            _.each(debt_cashregisters, function(cr) {
                var pymt_method_id = cr.id;
                var pm_button = self.$el.find("div[data-id=" + pymt_method_id + "]");
                pm_button.find("span").remove();
                if (client && client.debts && client.debts[pymt_method_id]) {
                    var credit_line_html = QWeb.render("CreditNote", {
                        debt: deb_type * client.debts[pymt_method_id].balance,
                        widget: self,
                    });
                    pm_button.append(credit_line_html);
                }
            });
            this.change_autopay_button();
        },
        add_autopay_paymentlines: function() {
            //console.log("add_autopay_paymentlines123w")
            var client = this.pos.get_client();
            var order = this.pos.get_order();
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
                var autopay_cashregisters = _.filter(this.pos.payment_methods, function(
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
        },
        renderElement: function() {
            //console.log("renderElement123w")
            this._super();
            this.autopay_html = this.render_validation_button();
            this.$el.append(this.autopay_html);
        },
        render_validation_button: function() {
            //console.log("render_validation_button123w")
            var self = this;
            var validation_button = $(QWeb.render("ValidationButton", {widget: this}));
            validation_button.find(".autopay").click(function() {
                self.click_autopay_validation();
            });
            return validation_button;
        },
        change_autopay_button: function(status) {
            //console.log("change_autopay_button123w")
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
            ////console.log("end11111")
        },
        click_autopay_validation: function() {
            //console.log("click_autopay_validation123w")
            this.pos.get_order().autopay_validated = true;
            this.validate_order();
        },
        show: function() {
            //console.log("show123w")
            var autopay_status = this.add_autopay_paymentlines();
            this._super();
            this.change_autopay_button(autopay_status);
        },
        render_paymentlines: function() {
            //console.log("render_paymentlines123w")
            var order = this.pos.get_order();
            if (!order) {
                return;
            }
            this._super();
            if (order.get_due()) {
                // Red if not fully paid, green if payment cover up the due
                this.change_autopay_button("alert");
            } else {
                this.change_autopay_button("validate");
            }
            if (!order.get_paymentlines().length || order.has_credit_product()) {
                $(this.autopay_html).hide();
            }
        },
    });
    */
    /*screens.ReceiptScreenWidget.include({
        show: function() {
            //console.log("show22")
            this._super();
            var order = this.pos.get_order();
            $(this.next_button_html).hide();
            if (order && order.autopay_validated) {
                $(this.next_button_html).show();
                var button_next = this.next_button_html.find(".autopay");
                button_next.addClass("validate");
                button_next.find(".title").text("Next");
            }
        },
        click_next: function() {
            //console.log("click_next")
            if (this.pos.get_order().autopay_validated) {
                this._super();
                this.pos.thumb_up_animation();
            } else {
                this._super();
            }
        },
        render_validation_button: function() {
            //console.log("render_validation_button")
            var self = this;
            var validation_button = $(QWeb.render("ValidationButton", {widget: this}));
            validation_button.find(".autopay").click(function() {
                self.click_next();
            });
            return validation_button;
        },
        renderElement: function() {
            //console.log("renderElement")
            this._super();
            this.next_button_html = this.render_validation_button();
            this.$el.append(this.next_button_html);
        },
        render_change: function() {
            //console.log("render_change")
            // Deduct the number of discount credits, because they were spent on discounts, but still presence like unspent
            var order = this.pos.get_order();
            this.$(".change-value").html(this.format_currency(order.get_change()));
        },
    });
    */
    /*
    gui.Gui.prototype.screen_classes
        .filter(function(el) {
            return el.name === "clientlist";
        })[0]
        .widget.include({
            init: function(parent, options) {
                //console.log("init3333")
                this._super(parent, options);
                this.round = function(value) {
                    return Math.round(value * 100) / 100;
                };
                this.check_user_in_group = function(group_id, groups) {
                    return $.inArray(group_id, groups) !== -1;
                };
                this.pos.on(
                    "updateDebtHistory",
                    function(partner_ids) {
                        this.update_debt_history(partner_ids);
                    },
                    this
                );
                this.debt_history_limit_initial = 10;
                this.debt_history_limit_increment = 10;
            },
            line_select: function(event, $line, id) {
                //console.log("line_select")
                this._super(event, $line, id);
                this.selected_line = arguments;
                this.pos.reload_debts(id, 0, {postpone: false});
            },
            update_debt_history: function(partner_ids) {
                //console.log("update_debt_history")
                var self = this;
                var customers = this.pos.db.get_partners_sorted(1000);
                var partner = this.new_client || this.pos.get_client();
                if (partner && this.clientlist_screen_is_opened()) {
                    var debt = partner.debt;
                    if (this.pos.config.debt_type === "credit") {
                        debt = -debt;
                    }
                    debt = this.format_currency(debt);

                    if (partner_ids.length && _.contains(partner_ids, partner.id)) {
                        // Updating only opened partner profile and debt history
                        $(".client-detail .detail.client-debt").text(debt);
                        var debts = _.values(partner.debts);
                        if (partner.debts) {
                            var credit_lines_html = "";
                            credit_lines_html = QWeb.render("CreditList", {
                                partner: partner,
                                debts: debts,
                                widget: self,
                            });
                            $("div.credit_list").html(credit_lines_html);
                        }
                        if (this.debt_history_is_opened()) {
                            this.render_debt_history(partner);
                        }
                    } else {
                        this.render_list(customers);
                        $(
                            "tr.client-line[data-id=" + partner.id + "] td.client-debt"
                        ).text(debt);
                    }
                }
                _.each(partner_ids, function(id) {
                    self.partner_cache.clear_node(id);
                });
                this.render_list(customers);
            },
            render_list: function(partners) {
                //console.log("render_list")
                var debt_type = this.pos.config.debt_type;
                if (debt_type === "debt") {
                    this.$("#client-list-credit").remove();
                } else if (debt_type === "credit") {
                    this.$("#client-list-debt").remove();
                }
                var selected_partner = this.selected_line
                    ? this.pos.db.get_partner_by_id(this.selected_line[2])
                    : this.new_client;
                if (selected_partner) {
                    this.old_client = selected_partner;
                }
                this._super(partners);
                this.old_client = this.pos.get_client();
                this.selected_line = false;
            },
            render_debt_history: function(partner) {
                //console.log("render_debt_history")
                var self = this;
                var contents = this.$el[0].querySelector("#debt_history_contents");
                contents.innerHTML = "";
                var debt_type = this.pos.config.debt_type;
                var debt_history = partner.history;
                var debt_history = partner.history;
                ////console.log("debt_historyssss",partner,debt_history)
                var sign = debt_type === "credit" ? -1 : 1;
                this.history_length = debt_history ? debt_history.length : 0;
                if (debt_type === "debt") {
                    this.$el.find("th:contains(Total Balance)").text("Total Debt");
                }
                ////console.log("this.history_length",this.history_length)
                if (this.history_length) {
                    var total_balance = partner.debt;
                    for (var i = 0; i < debt_history.length; i++) {
                        debt_history[i].total_balance =
                            (sign * Math.round(total_balance * 100)) / 100;
                        total_balance += debt_history[i].balance;
                    }
                    var cashregisters = _.filter(self.pos.payment_methods, function(cr) {
                        return cr.debt;
                    });
                    _.each(cashregisters, function(cr) {
                        var pymt_method_id = cr.id;
                        var total_journal = partner.debts[pymt_method_id].balance;
                        for (i = 0; i < debt_history.length; i++) {
                            ////console.log("debt_history[i]",debt_history[i])
                            //if (debt_history[i].journal_id[0] === pymt_method_id) {
                            if (debt_history[i].payment_method_id[0] === pymt_method_id) {
                                debt_history[i].total_journal =
                                    Math.round(total_journal * 100) / 100;
                                total_journal -= debt_history[i].balance;
                            }
                        }
                    });
                    for (var y = 0; y < debt_history.length; y++) {
                        var debt_history_line_html = QWeb.render("DebtHistoryLine", {
                            partner: partner,
                            line: debt_history[y],
                            widget: self,
                            debt_type: debt_type,
                        });
                        var debt_history_line = document.createElement("tbody");
                        debt_history_line.innerHTML = debt_history_line_html;
                        debt_history_line = debt_history_line.childNodes[1];
                        contents.appendChild(debt_history_line);
                    }
                    if (debt_history.length !== partner.records_count) {
                        var debt_history_load_more_html = QWeb.render(
                            "DebtHistoryLoadMore"
                        );
                        var debt_history_load_more = document.createElement("tbody");
                        debt_history_load_more.innerHTML = debt_history_load_more_html;
                        debt_history_load_more = debt_history_load_more.childNodes[1];
                        contents.appendChild(debt_history_load_more);
                        this.$("#load_more").on("click", function() {
                            ////console.log("kkkkkkkkkkk")
                            self.pos
                                .reload_debts(
                                    partner.id,
                                    debt_history.length +
                                        self.debt_history_limit_increment,
                                    {postpone: false}
                                )
                                .then(function() {
                                    self.render_debt_history(partner);
                                });
                        });
                    }
                }
            },
            toggle_save_button: function() {
                //console.log("toggle_save_button")
                this._super();
                var $pay_full_debt = this.$("#set-customer-pay-full-debt");
                var $show_customers = this.$("#show_customers");
                var $show_debt_history = this.$("#show_debt_history");
                var curr_client = this.pos.get_order().get_client();
                var client = this.new_client || curr_client;
                if (this.editing_client) {
                    $pay_full_debt.addClass("oe_hidden");
                    $show_debt_history.addClass("oe_hidden");
                    $show_customers.addClass("oe_hidden");
                } else if (this.debt_history_is_opened()) {
                    $show_customers.removeClass("oe_hidden");
                } else {
                    if (
                        (this.new_client && this.new_client.debt > 0) ||
                        (curr_client && curr_client.debt > 0 && !this.new_client)
                    ) {
                        $pay_full_debt.removeClass("oe_hidden");
                    } else {
                        $pay_full_debt.addClass("oe_hidden");
                    }
                    if (client) {
                        $show_debt_history.removeClass("oe_hidden");
                    } else {
                        $show_debt_history.addClass("oe_hidden");
                    }
                }

                if (this.debt_history_is_opened() && !this.editing_client) {
                    this.$el.find(".client-details").addClass("debt-history");
                } else {
                    this.$el.find(".client-details").removeClass("debt-history");
                }
            },
            show: function() {
                //console.log("show4444")
                this._super();
                var self = this;
                this.$("#set-customer-pay-full-debt").click(function() {
                    ////console.log('set-customer-pay-full-debt')
                    var client = self.new_client || self.pos.get_order().get_client();
                    self.save_changes();
                    if (client.debt <= 0) {
                        self.gui.show_popup("error", {
                            title: _t("Error: No Debt"),
                            body: _t("The selected customer has no debt."),
                        });
                        return;
                    }
                    // If the order is empty, add a dummy product with price = 0
                    var order = self.pos.get_order();
                    ////console.log("order1122",order)
                    if (order) {
                        var lastorderline = order.get_last_orderline();
                        ////console.log("lastorderline",lastorderline,self.pos.config.debt_dummy_product_id)
                        if (
                            !lastorderline &&
                            self.pos.config.debt_dummy_product_id
                        ) {
                            ////console.log("create_pdt")
                            var dummy_product = self.pos.db.get_product_by_id(
                                self.pos.config.debt_dummy_product_id[0]
                            );
                            order.add_product(dummy_product, {price: 0});
                        }
                    }

                    // Select debt journal
                    var debtjournal = false;
                    ////console.log("debtjournal",self.pos)
                    _.each(self.pos.payment_methods, function(cashregister) {
                        if (cashregister.debt) {
                            debtjournal = cashregister;
                        }
                    });

                    // Add payment line with amount = debt *-1
                    var paymentLines = order.get_paymentlines();
                    ////console.log("paymentLineee2",paymentLines)
                    if (paymentLines.length) {
                        //console.log("paymentLineee1",paymentLines)
                        //_.each(paymentLines.models, function(paymentLine) {

                        //_.each(paymentLines, function(paymentLine) {
                        //    if (paymentLine.payment_method.debt) {
                        //        //console.log("paymentLineee",paymentLine)
                        //        paymentLine.destroy();
                        //    }
                        //});
                    }

                    var newDebtPaymentline = new models.Paymentline(
                        {},
                        {order: order, payment_method: debtjournal, pos: self.pos}
                    );
                    newDebtPaymentline.set_amount(client.debt * -1);
                    //console.log("newDebtPaymentline123",newDebtPaymentline)
                    order.paymentlines.add(newDebtPaymentline);
                    self.gui.show_screen("payment");
                });
                var $show_debt_history = $("#show_debt_history");
                var client = this.pos.get_order().get_client();
                if (client || this.new_client) {
                    $show_debt_history.removeClass("oe_hidden");
                    self.$el.find(".client-details").removeClass("debt-history");
                    this.pos.reload_debts(client.id, 0, {postpone: false});
                }
            },
            renderElement: function() {
                //console.log("renderElement222")
                var self = this;
                this._super();
                var parent = self.$(".client-list").parent();

                var $show_debt_history = this.$el.find("#show_debt_history"),
                    $show_customers = this.$el.find("#show_customers"),
                    $debt_history = this.$el.find("#debt_history");

                $show_debt_history.off().on("click", function() {
                    //console.log("$show_debt_history.off")
                    var client = self.new_client || self.pos.get_order().get_client();
                    var $loading_history = $("#loading_history");
                    $loading_history.removeClass("oe_hidden");
                    self.render_debt_history(client);
                    $(".client-list").addClass("oe_hidden");
                    $debt_history.removeClass("oe_hidden");
                    $show_debt_history.addClass("oe_hidden");
                    $show_customers.removeClass("oe_hidden");

                    var old_size = self.$el.find(".client-details").height();
                    self.$el.find(".client-details").addClass("debt-history");
                    var new_size = self.$el.find(".client-details").height();
                    var resize = old_size - new_size;
                    // Set new height for debt history list
                    parent.height(parent.height() + resize);

                    self.pos
                        .reload_debts(client.id, self.debt_history_limit_initial, {
                            postpone: false,
                        })
                        .then(function() {
                            self.render_debt_history(client);
                            $loading_history.addClass("oe_hidden");
                        });
                });

                $show_customers.off().on("click", function() {
                    $(".client-list").removeClass("oe_hidden");
                    $debt_history.addClass("oe_hidden");
                    $show_customers.addClass("oe_hidden");
                    $show_debt_history.removeClass("oe_hidden");
                    var old_details_size = self.$el.find(".client-details").height();
                    self.$el.find(".client-details").removeClass("debt-history");
                    var new_details_size = self.$el.find(".client-details").height();
                    var new_resize = old_details_size - new_details_size;
                    // Set new height for client list
                    parent.height(parent.height() + new_resize);
                });
            },
            saved_client_details: function(partner_id) {
                //console.log("saved_client_details")
                this.pos.gui.screen_instances.clientlist.partner_cache.clear_node(
                    partner_id
                );
                this._super(partner_id);
                this.pos.reload_debts([partner_id], 0, {postpone: false});
            },
            reload_partners: function() {
                //console.log("reload_partners")
                var self = this;
                return this._super().then(function() {
                    self.render_list(self.pos.db.get_partners_sorted(1000));
                });
            },
            clientlist_screen_is_opened: function() {
                return $(".clientlist-screen.screen").not(".oe_hidden")[0] || false;
            },
            debt_history_is_opened: function() {
                return $("#debt_history").not(".oe_hidden")[0] || false;
            },
        });

    var ThumbUpPopupWidget = PopupWidget.extend({
        template: "ThumbUpPopupWidget",
        show: function(options) {
            this._super(options);
            var self = this;
            var random = Math.random();
            var element = $(".icon-wrapper");
            if (random <= 0.01) {
                element = $(".icon-wrapper-2");
            }
            element.parents(".thumb-up-popup").css({
                "line-height": document.documentElement.clientHeight + "px",
            });
            var k = 50;
            element.css({
                zoom:
                    k *
                        (Math.min(
                            document.documentElement.clientWidth,
                            document.documentElement.clientHeight
                        ) /
                            80) +
                    "%",
            });

            element.show();
            element.addClass("anim");

            setTimeout(function() {
                element.removeClass("anim");
                element.hide();
                self.gui.close_popup();
            }, 1000);
        },
    });
    gui.define_popup({name: "thumb-up", widget: ThumbUpPopupWidget});
    */
});
