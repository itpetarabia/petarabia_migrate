from odoo import models,_,api, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def set_mail_template(self):
        try:
            self.env.ref('stock.mail_template_data_delivery_confirmation').report_template = self.env.ref('pet_arabia_custom_report.action_report_delivery')
        except ValueError:
            return False

    def do_print_picking(self):
        self.write({'printed': True})
        return self.env.ref('pet_arabia_custom_report.action_report_delivery').report_action(self)

    def _attach_sign(self):
        """ Render the delivery report in pdf and attach it to the picking in `self`. """
        self.ensure_one()
        report = self.env.ref('pet_arabia_custom_report.action_report_delivery')._render_qweb_pdf(self.id)
        filename = "%s_signed_delivery_slip" % self.name
        if self.partner_id:
            message = _('Order signed by %s') % (self.partner_id.name)
        else:
            message = _('Order signed')
        self.message_post(
            attachments=[('%s.pdf' % filename, report[0])],
            body=message,
        )
        return True



# class StockMoveLine(models.Model):
#     _inherit = "stock.move.line"
#
#     product_variant_details = fields.Char(
#         string="Product Variants",
#         compute="_compute_product_variant_details",
#         store=False
#     )
#
#     @api.depends('product_id',)
#     def _compute_product_variant_details(self):
#         for line in self:
#             if line.product_id:
#                 variants = line.product_id.product_template_attribute_value_ids
#                 details = [f"{v.attribute_id.name}: {v.name}" for v in variants]
#                 line.product_variant_details = ", ".join(details)
#             else:
#                 line.product_variant_details = ""