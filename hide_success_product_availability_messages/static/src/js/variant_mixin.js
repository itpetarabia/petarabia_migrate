odoo.define('hide_success_product_availability_messages.VariantMixin', function (require) {
  'use strict';

  var core = require('web.core');
  var publicWidget = require('web.public.widget');
  var ajax = require('web.ajax');
  var qweb = core.qweb;
  var VariantMixin = require('website_sale_stock.VariantMixin');
  var xml_load = ajax.loadXML(
    '/hide_success_product_availability_messages/static/src/xml/custom.xml', qweb);


 VariantMixin._hideMsgs = function (ev, $parent, combination) {
    xml_load.then(function () {
        $('.oe_website_sale')
            .find('.availability_message_' + combination.product_template)
            .remove();

        var $message = $(qweb.render(
            'hide_success_product_availability_messages.hide_msgs',
            combination
        ));
        $('div.availability_messages').html($message);
    });
    }

  // }
  publicWidget.registry.WebsiteSale.include({
    /**
     * Adds the stock checking to the regular _onChangeCombinationStock method
     * @override
     */
    _onChangeCombination: function () {
      this._super.apply(this, arguments);
      VariantMixin._hideMsgs.apply(this, arguments);
    }
  });
  return VariantMixin;
});
