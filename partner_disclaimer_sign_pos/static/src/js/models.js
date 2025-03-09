odoo.define('partner_disclaimer_sign_pos.models', function (require) {
"use strict";
var models = require('point_of_sale.models');
models.load_fields("res.partner", ["disclaimer_sign","disclaimer_sign_doc"]);
});
