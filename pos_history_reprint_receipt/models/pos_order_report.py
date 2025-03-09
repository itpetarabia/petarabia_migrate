import logging
from datetime import timedelta
#from functools import partial

#import psycopg2
#import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models, tools, _
#from odoo.tools import float_is_zero
#from odoo.exceptions import UserError
#from odoo.http import request
#from odoo.addons import decimal_precision as dp
from odoo.tools import float_is_zero, float_round
_logger = logging.getLogger(__name__)

class ReportSaleDetails(models.AbstractModel):

    _inherit = 'report.point_of_sale.report_saledetails'

    #replace
    @api.model
    def get_pos_saleshistory(self, date_start=False, date_stop=False, maiconfig_id=False,order_id=False):
        
        configs = self.env['pos.config'].browse(maiconfig_id)
        mai_session_id = self.env['pos.session'].search([('config_id','=',maiconfig_id),('state','=','opened')])
        reference = ''
        uid = ''
        amount_return = 0.0
        amount_round = 0.0
        cashier_name = ''
        client = ''
        client_phone = ''
        today = fields.Datetime.from_string(fields.Date.context_today(self))
        if date_start:
            date_start = fields.Datetime.from_string(date_start)
        else:
            date_start = today

        if date_stop:
            date_stop = fields.Datetime.from_string(date_stop)
        else:
            date_stop = today + timedelta(days=1, seconds=-1)

        date_stop = max(date_stop, date_start)

        date_start = fields.Datetime.to_string(date_start)
        date_stop = fields.Datetime.to_string(date_stop)
        if order_id:
            #print("get_pos_saleshistory",order_id)
            orders = self.env['pos.order'].search([
                ('state', 'in', ['paid', 'invoiced','done']),
                ('id', '=', order_id)])
        else:
            orders = self.env['pos.order'].search([
                ('state', 'in', ['paid','invoiced']),
                ('config_id', 'in', configs.ids)])

        user_currency = self.env.user.company_id.currency_id
        #currency = self.currency_id or self.company_id.currency_id
        total = 0.0
        total_paid = 0.0
        products_sold = {}
        taxes = {}
        disc_amount = sum(orders.mapped('lines').mapped('disc_amount'))
        order_line = []
        for order in orders:
            if user_currency != order.pricelist_id.currency_id:
                total += order.pricelist_id.currency_id.compute(order.amount_total, user_currency)
                total_paid += order.pricelist_id.currency_id.compute(order.amount_paid, user_currency)
            else:
                total += order.amount_total
                total_paid += order.amount_paid
            currency = order.session_id.currency_id
            #print("order_lines000", order)
            for line in order.lines:
                key = (line.product_id, line.price_unit, line.discount)
                products_sold.setdefault(key, 0.0)
                products_sold[key] += line.qty

                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.compute_all(line.price_unit * (1-(line.discount or 0.0)/100.0), currency, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)
                    for tax in line_taxes['taxes']:
                        print("taxxxxx",tax)
                        tax_id = self.env['account.tax'].browse(tax['id'])
                        taxes.setdefault(tax['id'], {'name': tax['name'], 'total':0.0, 'base':0.0, 'code': tax_id.description, 'percent': tax_id.amount, 'amount_type': tax_id.amount_type})
                        taxes[tax['id']]['total'] += tax['amount']
                        taxes[tax['id']]['base'] += tax['base']
            reference = order.pos_reference
            #print("order_lines",order)

            order_line_dict = {}
            for o_line in order.lines:
                line_tax = []
                if o_line.id not in order_line_dict:
                    for tax in o_line.tax_ids:
                        line_tax.append(tax.description)
                    order_line_dict[o_line.id] = {
                        'product_id': o_line.product_id.id,
                        'product_name': o_line.product_id.name,
                        'code': o_line.product_id.default_code,
                        'quantity': o_line.qty,
                        'price_unit': o_line.price_unit,
                        'discount': o_line.discount,
                        'uom': o_line.product_id.uom_id.name,
                        'price_subtotal': o_line.price_subtotal,
                        'price_subtotal_incl': o_line.price_subtotal_incl,
                        'taxDetails': line_tax,
                    }
            for b in order_line_dict:
                order_line.append(order_line_dict.get(b))
        payments_ids = self.env["pos.payment"].search([('pos_order_id', 'in', orders.ids),('is_change', '=', False)])
        print("==payments_ids==", payments_ids)
        payments = []
        payments_dict = {}
        for payment in payments_ids:
            if payment.payment_method_id.id not in payments_dict:
                #if payment.amount>0:
                payments_dict[payment.payment_method_id.id] = {
                    'name': payment.payment_method_id.name,
                    'total': payment.amount,
                }
            else:
                if payment.amount > 0:
                    payments_dict[payment.payment_method_id.id]['total'] += payment.amount

        for a in payments_dict:
            payments.append(payments_dict.get(a))
        change = 0.0
        rounding = 0.0
        for order in orders:
            if order.state in ['paid', 'done', 'invoiced']:
                amount_return = order.amount_return
            else:
                if not payments:
                    # change = total_paid - total - this.get_rounding_applied();
                    change = total_paid - total
                else:
                    change = -total_paid
                    print("payments",payments)
                    for pay in payments:
                        change += pay['total']

                amount_return = change
            if user_currency.round(total_paid) < user_currency.round(total):
                amount_round = user_currency.round(total_paid)-user_currency.round(total)
            if order.pos_history_reference_uid:
                uid = order.pos_history_reference_uid
            cashier_name = order.user_id.name if order.user_id else ''
            client = order.partner_id.name if order.partner_id else ''
            if order.partner_id and order.partner_id.phone:
                client_phone = order.partner_id.phone
            elif order.partner_id and order.partner_id.mobile:
                client_phone = order.partner_id.mobile
        return {
            'disc_amount': disc_amount,
            'pos_name': mai_session_id[0].config_id.name,
            #'cashier_name': mai_session_id[0].user_id.name,
            'cashier_name': cashier_name,
            'session_start': mai_session_id[0].start_at,
            'session_end': fields.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'total_amt_with_tax': user_currency.round(total),
            'total_paid': user_currency.round(total_paid),
            'payments': payments,
            'reference': reference,
            'amount_return': user_currency.round(amount_return),
            'amount_round': user_currency.round(amount_round),
            'uid': uid,
            'company_name': self.env.user.company_id.name,
            'taxes': list(taxes.values()),
            'order_line': order_line,
            'client': client,
            'client_phone': client_phone,
            'products': sorted([{
                'product_id': product.id,
                'product_name': product.name,
                'code': product.default_code,
                'quantity': qty,
                'price_unit': price_unit,
                'discount': discount,
                'uom': product.uom_id.name
            } for (product, price_unit, discount), qty in products_sold.items()], key=lambda l: l['product_name'])
        }

