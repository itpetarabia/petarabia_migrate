odoo.define('base_address_renamed_ext.pos_models', function (require) {
"use strict";

var models = require('point_of_sale.models');
models.load_fields('res.partner',['street_number', 'street_number2', 'zip', 'street2']);
});
