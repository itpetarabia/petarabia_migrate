odoo.define('pos_debt_notebook.ClientListScreen', function(require) {
    'use strict';

    const { debounce } = owl.utils;
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');
    const ClientListScreen = require('point_of_sale.ClientListScreen');
    const core = require("web.core");
    var QWeb = core.qweb;
    var models = require("point_of_sale.models");

    const PosNotebookClientListScreen = (ClientListScreen) =>
        class extends ClientListScreen {
            constructor() {
                console.log("clientLineConstructor");
                super(...arguments);
                this.state['debtHistoryIsShown'] = false;
                console.log("this.stateeee",this.state);
                this.env.pos.on(
                    "updateDebtHistory",
                    function(partner_ids) {
                        console.log("fffffffff",partner_ids);
                        this.update_debt_history(partner_ids);
                    },
                    this
                );
                this.debt_history_limit_initial = 10;
                this.debt_history_limit_increment = 10;

            }
            update_debt_history(partner_ids) {
                console.log("update_debt_history",this.env.pos.get_client(),partner_ids,this);
                var self = this;
                var customers = this.env.pos.db.get_partners_sorted(1000);
                //var partner = this.new_client || this.env.pos.get_client();
                var partner = this.env.pos.db.get_partner_by_id(partner_ids[0]);
                console.log("partnerrrr",partner);
                if (partner) {
                    var debt = partner.debt;
                    if (this.env.pos.config.debt_type === "credit") {
                        debt = -debt;
                    }
                    debt = this.env.pos.format_currency(debt);
                    this.render_debt_history(partner);
                    /*if (partner_ids.length && _.contains(partner_ids, partner.id)) {
                        // Updating only opened partner profile and debt history
                        $(".client-detail .detail.client-debt").text(debt);
                        var debts = _.values(partner.debts);
                        //if (partner.debts) {
                        //    var credit_lines_html = "";
                        //    credit_lines_html = QWeb.render("CreditList", {
                        //        partner: partner,
                        //        debts: debts,
                        //        widget: self,
                        //    });
                        //    $("div.credit_list").html(credit_lines_html);
                        //}
                        //if (this.debt_history_is_opened()) {
                        //    console.log("call-debt_history_is_opened");
                        //    this.render_debt_history(partner);
                        //}
                        console.log("call-debt_history_is_opened",partner);
                        this.render_debt_history(partner);
                    } else {
                        //this.render_list(customers);
                        $(
                            "tr.client-line[data-id=" + partner.id + "] td.client-debt"
                        ).text(debt);
                    }*/
                }
                //_.each(partner_ids, function(id) {
                //    self.partner_cache.clear_node(id);
                //});
                //this.render_list(customers);
            }
            //render_list: function(partners) {
            //    console.log("render_list")
            //    var debt_type = this.env.pos.config.debt_type;
            //    if (debt_type === "debt") {
            //        this.$("#client-list-credit").remove();
            //    } else if (debt_type === "credit") {
            //        this.$("#client-list-debt").remove();
            //   }
            //    var selected_partner = this.selected_line
            //        ? this.pos.db.get_partner_by_id(this.selected_line[2])
            //        : this.new_client;
            //    if (selected_partner) {
            //        this.old_client = selected_partner;
            //    }
            //    this._super(partners);
            //    this.old_client = this.pos.get_client();
            //    this.selected_line = false;
            //},
            render_debt_history(partner) {
                console.log("render_debt_history")
                var self = this;
                console.log("selfffff",this.el);
                //var contents = this.el.querySelectorAll("#debt_history_contents");
                var contents = $("#debt_history_contents");
                $("#debt_history_contents").empty();
                contents.innerHTML = "";
                var debt_type = this.env.pos.config.debt_type;
                var debt_history = partner.history;
                console.log("debt_historyssss",partner,debt_history,contents)
                var sign = debt_type === "credit" ? -1 : 1;
                this.history_length = debt_history ? debt_history.length : 0;
                //if (debt_type === "debt") {
                //    this.el.find("th:contains(Total Balance)").text("Total Debt");
                //}
                console.log("this.history_length",this.history_length)
                if (this.history_length) {
                    var total_balance = partner.debt;
                    for (var i = 0; i < debt_history.length; i++) {
                        debt_history[i].total_balance =
                            (sign * Math.round(total_balance * 100)) / 100;
                        total_balance += debt_history[i].balance;
                    }
                    var cashregisters = _.filter(self.env.pos.payment_methods, function(cr) {
                        return cr.debt;
                    });
                    _.each(cashregisters, function(cr) {
                        var pymt_method_id = cr.id;
                        var total_journal = partner.debts[pymt_method_id].balance;
                        for (i = 0; i < debt_history.length; i++) {
                            console.log("debt_history[i]",debt_history[i])
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
                        console.log("debt_history_line",debt_history_line,debt_history_line_html);
                        //contents.appendChild(debt_history_line);
                        contents.append(debt_history_line);
                        console.log("contents123",contents);
                    }
                    if (debt_history.length !== partner.records_count) {
                        var debt_history_load_more_html = QWeb.render(
                            "DebtHistoryLoadMore"
                        );
                        var debt_history_load_more = document.createElement("tbody");
                        debt_history_load_more.innerHTML = debt_history_load_more_html;
                        debt_history_load_more = debt_history_load_more.childNodes[1];
                        //contents.appendChild(debt_history_load_more);
                        contents.append(debt_history_load_more);
                        $("#load_more").on("click", function() {
                            //console.log("kkkkkkkkkkk")
                            self.env.pos
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
            }
            debt_history_is_opened() {
                return $("#debt_history").not(".oe_hidden")[0] || false;
            }
            /*updateClientList(event) {
                this.state.query = event.target.value;
                const clients = this.clients;
                //this._super(event);
                console.log('event000',event,this.state);
                super.updateClientList(event);
                this.env.pos.reload_debts([partner_id], 0, {postpone: false});
            }*/
            clickClient(event) {
                super.clickClient(event);
                if (this.state.selectedClient) {
                    this.env.pos.reload_debts(this.state.selectedClient.id, 0, {
                        postpone: false,
                    });
                }
            }
            async saveChanges(event) {
                await super.saveChanges(event);
                this.env.pos.reload_debts([this.state.selectedClient.id], 0, {
                    postpone: false,
                });
            }



            clickShowDebtHistory() {
                this.state.editModeProps = {
                    partner: this.state.selectedClient,
                };
                this.state.debtHistoryIsShown = true;
                //this.env.pos.reload_debts(this.state.selectedClient, 0, {postpone: false});
                this.env.pos.reload_debts([this.state.selectedClient.id], 0, {postpone: false});
                this.render();
            }
            clickPayFullDebt() {
                var self = this;
                var client = self.new_client || self.env.pos.get_order().get_client();
                if (!client) {
                    self.showPopup('ErrorPopup', {
                        title: this.env._t('Unknown customer'),
                        body: this.env._t('You cannot use Debt payment. Select customer first.'),
                    });
                    return;
                }
                if (client.debt <= 0) {
                    self.showPopup("ErrorPopup", {
                        title: this.env._t("Error: No Debt"),
                        body: this.env._t("The selected customer has no debt."),
                    });
                    return;
                }
                // If the order is empty, add a dummy product with price = 0
                var order = self.env.pos.get_order();
                //console.log("order1122",order)
                if (order) {
                    var lastorderline = order.get_last_orderline();
                    //console.log("lastorderline",lastorderline,self.pos.config.debt_dummy_product_id)
                    if (
                        !lastorderline &&
                        self.env.pos.config.debt_dummy_product_id
                    ) {
                        //console.log("create_pdt")
                        var dummy_product = self.env.pos.db.get_product_by_id(
                            self.env.pos.config.debt_dummy_product_id[0]
                        );
                        order.add_product(dummy_product, {price: 0});
                    }
                }
                console.log("k1111111");
                // Select debt journal
                var debtjournal = false;
                //console.log("debtjournal",self.pos)
                _.each(self.env.pos.payment_methods, function(cashregister) {
                    if (cashregister.debt) {
                        debtjournal = cashregister;
                    }
                });
                console.log("k2222222");
                // Add payment line with amount = debt *-1
                var paymentLines = order.get_paymentlines();
                if (paymentLines.length) {
                    console.log("paymentLineee1",paymentLines)
                    _.each(paymentLines.models, function(paymentLine) {
                        if (paymentLine.payment_method.debt) {
                            console.log("paymentLineee",paymentLine)
                            paymentLine.destroy();
                        }
                    });

                }
                console.log("k3333333");
                var newDebtPaymentline = new models.Paymentline(
                    {},
                    {order: order, payment_method: debtjournal, pos: self.env.pos}
                );
                console.log("k4444444",newDebtPaymentline,client.debt);
                newDebtPaymentline.set_amount(client.debt * -1);
                console.log("newDebtPaymentline123",newDebtPaymentline)
                order.paymentlines.add(newDebtPaymentline);
                this.showScreen('PaymentScreen');
                this.trigger('close-temp-screen');
                order.select_paymentline(newDebtPaymentline);

                //self.env.gui.show_screen("payment");


                var $show_debt_history = $("#show_debt_history");
                var client = this.env.pos.get_order().get_client();
                if (client || this.new_client) {
                    $show_debt_history.removeClass("oe_hidden");
                    //self.$el.find(".client-details").removeClass("debt-history");
                    this.env.pos.reload_debts(client.id, 0, {postpone: false});
                }



                //var partner = this.new_client || this.env.pos.get_client();
                //if (!partner) {
                //    this.showPopup('ErrorPopup', {
                //        title: this.env._t('Unknown customer'),
                //        body: this.env._t('You cannot use Debt payment. Select customer first.'),
                //    });
                //}
            }
            get isDebtHistoryVisible() {
                if (this.state.selectedClient && !this.state.detailIsShown && !this.state.debtHistoryIsShown){
                    return true;
                }else{
                    return false;
                }

            }
            back() {
                if (this.state.detailIsShown) {
                    this.state.detailIsShown = false;
                    this.render();
                }else if (this.state.debtHistoryIsShown) {
                    this.state.debtHistoryIsShown = false;
                    this.render();
                }else {
                    this.props.resolve({ confirmed: false, payload: false });
                    this.trigger('close-temp-screen');
                }
            }

        };

    Registries.Component.extend(ClientListScreen, PosNotebookClientListScreen);

    return ClientListScreen;
});

        /*back() {
            if(this.state.detailIsShown) {
                this.state.detailIsShown = false;
                this.render();
            } else {
                this.props.resolve({ confirmed: false, payload: false });
                this.trigger('close-temp-screen');
            }
        }
        confirm() {
            this.props.resolve({ confirmed: true, payload: this.state.selectedClient });
            this.trigger('close-temp-screen');
        }
        get currentOrder() {
            return this.env.pos.get_order();
        }

        get clients() {
            if (this.state.query && this.state.query.trim() !== '') {
                return this.env.pos.db.search_partner(this.state.query.trim());
            } else {
                return this.env.pos.db.get_partners_sorted(1000);
            }
        }
        get isNextButtonVisible() {
            return this.state.selectedClient ? true : false;
        }
        get nextButton() {
            if (!this.props.client) {
                return { command: 'set', text: 'Set Customer' };
            } else if (this.props.client && this.props.client === this.state.selectedClient) {
                return { command: 'deselect', text: 'Deselect Customer' };
            } else {
                return { command: 'set', text: 'Change Customer' };
            }
        }

        updateClientList(event) {
            this.state.query = event.target.value;
            const clients = this.clients;
            console.log("updateClientList",event);
            if (event.code === 'Enter' && clients.length === 1) {
                this.state.selectedClient = clients[0];
                this.clickNext();
            } else {
                this.render();
            }
        }
        clickClient(event) {
            let partner = event.detail.client;
            if (this.state.selectedClient === partner) {
                this.state.selectedClient = null;
            } else {
                this.state.selectedClient = partner;
            }
            this.render();
        }
        editClient() {
            this.state.editModeProps = {
                partner: this.state.selectedClient,
            };
            this.state.detailIsShown = true;
            this.render();
        }
        clickNext() {
            this.state.selectedClient = this.nextButton.command === 'set' ? this.state.selectedClient : null;
            this.confirm();
        }
        activateEditMode(event) {
            const { isNewClient } = event.detail;
            this.state.isEditMode = true;
            this.state.detailIsShown = true;
            this.state.isNewClient = isNewClient;
            if (!isNewClient) {
                this.state.editModeProps = {
                    partner: this.state.selectedClient,
                };
            }
            this.render();
        }
        deactivateEditMode() {
            this.state.isEditMode = false;
            this.state.editModeProps = {
                partner: {
                    country_id: this.env.pos.company.country_id,
                    state_id: this.env.pos.company.state_id,
                },
            };
            this.render();
        }
        async saveChanges(event) {
            try {
                let partnerId = await this.rpc({
                    model: 'res.partner',
                    method: 'create_from_ui',
                    args: [event.detail.processedChanges],
                });
                console.log("partnerId000",partnerId);
                await this.env.pos.load_new_partners();
                console.log("partnerId111",partnerId);
                this.state.selectedClient = this.env.pos.db.get_partner_by_id(partnerId);
                this.state.detailIsShown = false;
                this.render();
            } catch (error) {
                console.log("saveChanges error",error);
                if (error.message.code < 0) {
                    await this.showPopup('OfflineErrorPopup', {
                        title: this.env._t('Offline'),
                        body: this.env._t('Unable to save changes.'),
                    });
                } else {
                    throw error;
                }
            }
        }*/

