odoo.define('pos_orders_history_return.ProductsWidget', function(require) {
    'use strict';

    const { useState } = owl.hooks;
    const PosComponent = require('point_of_sale.PosComponent');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const ProductsWidget = require('point_of_sale.ProductsWidget');

    const ProductsWidgetOrderReturn = (ProductsWidget) =>
        class extends ProductsWidget {
            constructor() {
                super(...arguments);
                useListener('click-add-new-item', this._clickAddNewItem);
                useListener('click-take-exist-item', this._clickTakeExistItem);
                //useListener('click-add-new-item2', this._clickAddNewItem222);
                //console.log("constructor0000vvv",this);
                //this.renderElement();
                //this.get_product_order_history_return(false);

            }
            //mounted() {
            //    //console.log("mount0000vvvv");
            //    this.renderElement();
                //this.env.pos.on('change:selectedCategoryId', this.render, this);

            //}
            async _clickAddNewItem(event) {
                var self_super = this;
                //console.log("_clickAddNewItem");
                //await self_super.click_return_edit(self_super);
                ////console.log("self_super-get_edit_return",self_super.env.pos.get_order().get_edit_return());
                $('.btn_edit_return_take').addClass('highlight');
                $('.btn_edit_return_take').removeClass('oe_hidden');
                $('.btn_edit_return_add').addClass('oe_hidden');
                //self_super.env.pos.get_order().is_all_pdt = true;
                var order = this.env.pos.get_order();
                if(order && order.edit_return !== true)
                {
                    //console.log("order.edit_return to true");
                    order.edit_return = true;
                    //self.$('.btn_edit_return').addClass('highlight');
                    await self_super.renderElement();
                    self_super._clearSearch();
                    //console.log("selectedCategory", this.selectedCategoryId);
                    //self_super.trigger('switch-category', 1);
                    //location.reload();
                    self_super.get_product_order_history_return(false);
                    var lines = this.env.pos.get_order().return_lines
                    var cat = this.env.pos.db.get_product_by_id(lines[0].product_id[0]).pos_categ_id[0];
                    this.trigger('switch-category', cat);
                    this.trigger('switch-category', 0);

                }
            }
            //async _clickAddNewItem222(event){
            //    this.renderElement();
            //    this.showScreen('ProductScreen');
            //}
            async _clickTakeExistItem(event) {
                //console.log("_clickTakeExistItem");
                var self_super = this;
                //await self_super.click_return_edit(self_super);
                $('.btn_edit_return_add').addClass('highlight');
                $('.btn_edit_return_add').removeClass('oe_hidden');
                $('.btn_edit_return_take').addClass('oe_hidden');
                //self_super.env.pos.get_order().is_all_pdt = false;
                var order = this.env.pos.get_order();
                if(order && order.edit_return == true)
                {
                    //console.log("order.edit_return to false");
                    order.edit_return = false;
                    //self.$('.btn_edit_return').removeClass('highlight');
                    //selff.set_category(selff.pos.db.get_category_by_id(Number(selff.dataset.categoryId)));
                    await self_super.renderElement();
                    self_super.get_product_order_history_return(this.env.pos.db.get_product_by_category(this.selectedCategoryId));
                    //console.log("selectedCategory", this.selectedCategoryId);
                    //self_super.trigger('breadcrumb-home');
                    //this.env.pos.set('selectedCategoryId',0);
                    var lines = this.env.pos.get_order().return_lines
                    var cat = this.env.pos.db.get_product_by_id(lines[0].product_id[0]).pos_categ_id[0];
                    this.trigger('switch-category', cat);
                    this.trigger('switch-category', 0);


                }
            }
            get_product_order_history_return(products) {
                //console.log("get_product_order_history_return",products);
                var self = this;
                if (products) {
                    //console.log("products000",products);
                    //this._clearSearch();
                    this.trigger('close-temp-screen');
                    return products

                } else {
                    //console.log("products111",products);
                    var list = [];
                    var lines = this.env.pos.get_order().return_lines;
                    //console.log("lineslines",lines);
                    //fkp june 24 2023 (product_id_added)
                    var product_id_added = [];
                    var product;
                    for (var i = 0, len = lines.length; i < len; i++) {
                        //for (var line in this.env.pos.get_order().return_lines) {
                        //console.log("line0000",lines[i]);
                        if (lines[i].product_id)
                        {
                            product = this.env.pos.db.get_product_by_id(lines[i].product_id[0]);
                            if (product)
                            {
                                if (!product_id_added.includes(product.id))
                                {
                                    list.push(product);
                                    product_id_added.push(product.id);
                                }
                                //fkp - feb 14 2022
                                self.env.pos.get_order().change_return_product_limit(product);
                            }
                        }
                    }
                    return list;
                }

            }
            get productsToDisplay() {
                this.renderElement();
                //console.log("productsToDisplay1111111",this.env.pos.get_order());
                if (this.searchWord !== '') {
                    //console.log("productsToDisplay1111111-0",this.searchWord);
                    return this.env.pos.db.search_product_in_category(
                        this.selectedCategoryId,
                        this.searchWord
                    );

                } else if(this.env.pos.get_order().return_lines && this.env.pos.get_order().edit_return !== true){
                    //console.log("productsToDisplay1111111-1");
                    return this.get_product_order_history_return(false);
                    /*var list = [];
                    var lines = this.env.pos.get_order().return_lines
                    for (var i = 0, len = lines.length; i < len; i++) {
                        //for (var line in this.env.pos.get_order().return_lines) {
                        //console.log("line0000",lines[i]);
                        if (lines[i].product_id){
                            list.push(this.env.pos.db.get_product_by_id(lines[i].product_id[0]));
                        }
                    }
                    //console.log('list000',list);
                    return list;*/

                } else {
                    //console.log("productsToDisplay1111111-2");
                    return this.env.pos.db.get_product_by_category(this.selectedCategoryId);
                }
                //return this.env.pos.db.get_product_by_category(this.selectedCategoryId);
                //else if(this.env.pos.get_order().return_lines && this.env.pos.get_order().is_all_pdt !== true){
            }
            //extra

            async renderElement() {
                //console.log("renderElement - ProductCategoriesWidget - history_return");
                //this._super();
                var self = this;
                var order = this.env.pos.get_order();
                if (
                    order &&
                    (order.get_mode() === "return" ||
                        order.get_mode() === "return_without_receipt")
                ) {
                    var returned_orders = this.env.pos.get_returned_orders_by_pos_reference(
                        order.name
                    );
                    // Add exist products
                    var products = [];
                    if (returned_orders && returned_orders.length) {
                        returned_orders.forEach(function(o) {
                            o.lines.forEach(function(line_id) {
                                var line = self.env.pos.db.line_by_id[line_id];
                                var product = self.env.pos.db.get_product_by_id(
                                    line.product_id[0]
                                );

                                var exist_product = _.find(products, function(r) {
                                    return r.id === product.id;
                                });
                                if (exist_product) {
                                    exist_product.max_return_qty += line.qty;
                                } else {
                                    product.max_return_qty = line.qty;
                                    if (line.price_unit !== product.price) {
                                        product.old_price = line.price_unit;
                                    }
                                    products.push(product);
                                }
                            });
                        });
                    }
                    // Update max qty for current return order
                    order.return_lines.forEach(function(line) {
                        var product = self.env.pos.db.get_product_by_id(line.product_id[0]);
                        var exist_product = _.find(products, function(r) {
                            return r.id === product.id;
                        });
                        if (exist_product) {
                            exist_product.max_return_qty += line.qty;
                        } else {
                            product.max_return_qty = line.qty;
                            if (line.price_unit !== product.price) {
                                product.old_price = line.price_unit;
                            }
                            products.push(product);
                        }
                    });
                    if (products.length) {
                        //this.product_list_widget.set_product_list(products);
                        //this.get_product_order_history_return(products);
                        this.showScreen('ProductScreen');
                    }
                }


            }
            /*async click_return_edit(self_super){
                //console.log('click_return_edit=',self_super);
                var order = this.env.pos.get_order();
                if(order && order.edit_return == true)
                {
                    //console.log("order.edit_return to false");
                    order.edit_return = false;
                    //self.$('.btn_edit_return').removeClass('highlight');
                    //selff.set_category(selff.pos.db.get_category_by_id(Number(selff.dataset.categoryId)));
                    self_super.renderElement();

                }
                else
                {
                    //console.log("order.edit_return to true");
                    order.edit_return = true;
                    //self.$('.btn_edit_return').addClass('highlight');
                    self_super.renderElement();
                    self_super._clearSearch();

                }
            }*/
        };

    Registries.Component.extend(ProductsWidget, ProductsWidgetOrderReturn);

    return ProductsWidget;
});
    /*class ProductsWidget extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('switch-category', this._switchCategory);
            useListener('update-search', this._updateSearch);
            useListener('try-add-product', this._tryAddProduct);
            useListener('clear-search', this._clearSearch);
            this.state = useState({ searchWord: '' });
        }
        mounted() {
            this.env.pos.on('change:selectedCategoryId', this.render, this);
        }
        willUnmount() {
            this.env.pos.off('change:selectedCategoryId', null, this);
        }
        get selectedCategoryId() {
            return this.env.pos.get('selectedCategoryId');
        }
        get searchWord() {
            return this.state.searchWord.trim();
        }
        get productsToDisplay() {
            if (this.searchWord !== '') {
                return this.env.pos.db.search_product_in_category(
                    this.selectedCategoryId,
                    this.searchWord
                );
            } else {
                return this.env.pos.db.get_product_by_category(this.selectedCategoryId);
            }
        }
        get subcategories() {
            return this.env.pos.db
                .get_category_childs_ids(this.selectedCategoryId)
                .map(id => this.env.pos.db.get_category_by_id(id));
        }
        get breadcrumbs() {
            if (this.selectedCategoryId === this.env.pos.db.root_category_id) return [];
            return [
                ...this.env.pos.db
                    .get_category_ancestors_ids(this.selectedCategoryId)
                    .slice(1),
                this.selectedCategoryId,
            ].map(id => this.env.pos.db.get_category_by_id(id));
        }
        get hasNoCategories() {
            return this.env.pos.db.get_category_childs_ids(0).length === 0;
        }
        _switchCategory(event) {
            this.env.pos.set('selectedCategoryId', event.detail);
        }
        _updateSearch(event) {
            this.state.searchWord = event.detail;
        }
        _tryAddProduct(event) {
            const searchResults = this.productsToDisplay;
            // If the search result contains one item, add the product and clear the search.
            if (searchResults.length === 1) {
                const { searchWordInput } = event.detail;
                this.trigger('click-product', searchResults[0]);
                // the value of the input element is not linked to the searchWord state,
                // so we clear both the state and the element's value.
                searchWordInput.el.value = '';
                this._clearSearch();
            }
        }
        _clearSearch() {
            this.state.searchWord = '';
        }
    }
    ProductsWidget.template = 'ProductsWidget';

    Registries.Component.add(ProductsWidget);

    return ProductsWidget;
});
*/