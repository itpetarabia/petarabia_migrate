
from odoo import models, fields, api, _

dt_tm_format = "%d/%m/%Y %H:%M %p"
dt_format = "%d/%m/%Y"
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('account.email_template_edi_invoice', False)
        if template:
            report_new = self.env.ref('pet_arabia_custom_report.account_invoices')
            if template.report_template.id != report_new.id:
                template.report_template = report_new.id
        return super(AccountInvoice,self).action_invoice_sent()

    def action_invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Only invoices could be printed."))

        self.filtered(lambda inv: not inv.is_move_sent).write({'is_move_sent': True})
        #1==1
        if self.user_has_groups('account.group_account_invoice') or 1==1:
            return self.env.ref('pet_arabia_custom_report.account_invoices').report_action(self)
        else:
            return self.env.ref('account.account_invoices_without_payment').report_action(self)

    def date_of_supply(self):
        date_suply = ''
        so_ids = list(set(self.invoice_line_ids.mapped('sale_line_ids').mapped('order_id').mapped('id')))
        po_ids = list(set(self.invoice_line_ids.mapped('purchase_line_id').mapped('order_id').mapped('id')))
        sales_orders = self.env['sale.order'].browse(so_ids)
        purchase_orders = self.env['purchase.order'].browse(po_ids)
        if sales_orders:
            picking = self.env['stock.picking'].search(
                [('sale_id', 'in', sales_orders.ids), ('state', 'in', ['done']),('location_dest_id.usage','=','customer')], order='date_done desc')
            if picking:
                picking = picking[0]
                if picking:
                    date_suply = picking.date_done
        elif purchase_orders:
            picking = self.env['stock.picking'].search(
                [('purchase_id', 'in', purchase_orders.ids), ('state', 'in', ['done']),('location_dest_id.usage','=','internal')], order='date_done desc')
            if picking:
                picking = picking[0]
                if picking:
                    date_suply = picking.date_done
        return date_suply
    """
    def inv_line_discount(self):
        disc_amt = 0
        total_amt = 0
        for line in self.invoice_line_ids:
            disc_amt += line.price_unit * line.quantity - line.price_subtotal
            total_amt += line.price_unit * line.quantity
        return{
            'disc_amt': disc_amt,
            'total_amt': total_amt,
        }
    """



class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    lot_no = fields.Char(
        string="Lot Number",
        compute="_compute_lot_no",
        store=False
    )
    product_variant_details = fields.Char(
        string="Product Variants",
        compute="_compute_product_variant_details",
        store=False
    )

    @api.depends('product_id', 'move_id')
    def _compute_lot_no(self):
        for line in self:
            # Find the sale order lines linked to this invoice line
            sale_lines = line.sale_line_ids
            if sale_lines:
                stock_move_lines = self.env['stock.move.line'].search([
                    ('move_id.sale_line_id', 'in', sale_lines.ids)
                ])
                lots = stock_move_lines.mapped('lot_id.name')
                line.lot_no = ", ".join(lots) if lots else ""

    @api.depends('product_id')
    def _compute_product_variant_details(self):
        for line in self:
            if line.product_id:
                variants = line.product_id.product_template_attribute_value_ids
                details = [variant.name for variant in variants]

                variant_string = ", ".join(details)

                max_length = 100
                if len(variant_string) > max_length:
                    variant_string = variant_string[:max_length] + "..."

                line.product_variant_details = variant_string
            else:
                line.product_variant_details = ""

