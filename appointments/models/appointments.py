# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields, models, _, api
from odoo.tools import float_compare
from odoo.addons import decimal_precision as dp
_logger = logging.getLogger(__name__)
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.addons.send_sms_ext.tools.format import format_pet_name
import ast

class PosAppointments(models.Model):
    _name = "pos.appointments"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = "POS Appointments"
    _rec_name = 'pet_names'
    
    #@api.one
    @api.depends('company_id')
    def _compute_currency(self):
        for res in self:
            res.currency_id = res.company_id.currency_id or res.env.user.company_id.currency_id

    @api.model
    def _default_alarm_ids(self):
        #return []
        alarm_id = self.env['ir.config_parameter'].sudo().get_param('appointments.alarm_ids') or []
        if alarm_id:
            return [(6,0,ast.literal_eval(alarm_id))]

    @api.depends('appointment_line.total_amt')
    def _compute_amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.appointment_line:
                amount_untaxed += line.untax_amt
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })
    
       
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True, states={'draft': [('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always', track_sequence=1, help="You can find a customer by its Name, TIN, Email or Internal Reference.")
    pet_ids = fields.Many2many('res.pet', string='Pets', readonly=True, states={'draft': [('readonly', False)]}, required=True, track_visibility='always', help="Pets that requires the appointment.")
    pet_names = fields.Char(string='Pet Names', store=False, readonly=True, compute='_compute_pet_names')
    #product_id = fields.Many2one('product.product', string='Service', required=True, domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict')
    start_datetime = fields.Datetime('Start DateTime', required=True,
        readonly=False,
        states={
            'cancel': [('readonly', True)],
            'confirmed': [('readonly', True)],
            'order': [('readonly', True)],
            'ready': [('readonly', True)],
            'done': [('readonly', True)],
            'paid': [('readonly', True)],
            },
        track_visibility='onchange')
    duration = fields.Float('Duration', readonly=True, states={'draft': [('readonly', False)]})
    location = fields.Char('Location', readonly=True, states={'draft': [('readonly', False)]}, track_visibility='onchange', help="Location of Event")
    description = fields.Text('Description', states={'done': [('readonly', True)]})
    alarm_ids = fields.Many2many('calendar.alarm', string='Reminders', readonly=True, states={
        'draft': [('readonly', False)],
        'confirmed': [('readonly', False)]},
        ondelete="restrict", copy=False, default=_default_alarm_ids)
    employee_ids = fields.Many2many('hr.employee', readonly=True, states={
        'draft': [('readonly', False)],
        'confirmed': [('readonly', False)]
        },
        string='Employees')
    #untax_amt = fields.Float('Untax Amount', store=True, readonly=True, compute='_compute_untax_amt')
    #tax_ids = fields.Many2many('account.tax', string='Taxes Applied', domain=['|', ('active', '=', False), ('active', '=', True)],
    #    help="Taxes that apply on the base amount")
    #total_amt = fields.Float('Total', store=True, readonly=True, compute='_amount_all', track_visibility='always', track_sequence=6)
    config_id = fields.Many2one('pos.config', readonly=True, states={'draft': [('readonly', False)]},
        required=True,
        string='Point of Sale')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirmed', 'Confirmed'),
        # ('order', 'Order'),
        # ('paid', 'Paid'),
        ('order', 'Ongoing'),
        ('ready', 'Ready for Pickup'),
        ('done', 'Done'),
        ('paid', 'Done & Paid'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', track_sequence=3, default='draft')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', oldname='currency', string="Currency")
    
    pos_order_ids = fields.One2many('pos.order', 'appointment_id', string='Orders')
    pos_order_count = fields.Integer(string='POS Orders', compute='_compute_pos_order_ids')
    meeting_ids = fields.One2many('calendar.event', 'appointment_id', string='Meeting')
    meeting_count = fields.Integer(string='Meeting', compute='_compute_meeting_ids')
    user_id = fields.Many2one('res.users', string='Responsibility', index=True, track_visibility='onchange',
                              track_sequence=2, default=lambda self: self.env.user)

    appointment_line = fields.One2many('pos.appointments.line', 'appointment_id', string='Appointment Lines', copy=True, auto_join=True)

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_compute_amount_all',
                                     track_visibility='onchange', track_sequence=5)
    #amount_by_group = fields.Binary(string="Tax amount by group", compute='_amount_by_group',
    #                                help="type: [(name, amount, base, formated amount, formated base)]")
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_compute_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount_all',
                                   track_visibility='always', track_sequence=6)

    @api.depends('pos_order_ids')
    def _compute_pos_order_ids(self):
        for appoint in self:
            appoint.pos_order_count = len(appoint.pos_order_ids)
    @api.depends('meeting_ids')
    def _compute_meeting_ids(self):
        for appoint in self:
            appoint.meeting_count = len(appoint.meeting_ids)
    
    @api.depends('pet_ids')
    def _compute_pet_names(self):
        for appoint in self:
            pets = appoint.pet_ids
            if len(pets):
                appoint.pet_names = format_pet_name(pets)
            else:
                appoint.pet_names = appoint.name

    @api.model
    def _fill_pets(self):
        appointments = self.env['pos.appointments'].search(
            ['&', ('pet_id', '!=', False), ('pet_ids', '=', False)])
        for r in appointments:
            if not r.pet_ids and r.pet_id:
                r.write({'pet_ids': [(6, 0, [r.pet_id.id])]})
            else:
                r.pet_ids = False
        
    
    """@api.depends('tax_ids','untax_amt')
    def _amount_all(self):
        total_amount = 0.0
        if self.untax_amt:
            total_amount = self.untax_amt
            if self.tax_ids:
                taxes = self.tax_ids.compute_all(self.untax_amt, self.currency_id, product=self.product_id, partner=self.partner_id)
                total_amount = total_amount + (taxes['total_included'] -  self.untax_amt)
        self.total_amt = total_amount"""
                
    """@api.depends('product_id')
    def _compute_untax_amt(self):
        if self.product_id.lst_price:
            self.untax_amt = self.product_id.lst_price
        else:
            self.untax_amt = 0.0"""
    
    @api.onchange('partner_id')
    def _onchange_responsible_id(self):
        for rec in self:
            return {'domain': {'pet_ids': [('parent_id', '=', rec.partner_id.id)]}}

    @api.constrains('start_datetime')
    def check_startdate(self):
        for rec in self:
            start_date = rec.start_datetime.replace(tzinfo=None)
            if start_date < datetime.now():
                raise ValidationError(_(f"Appointment date cannot be set in the past."))

    #@api.multi
    def action_confirm(self):
        self.ensure_one()
        obj_calendar = self.env['calendar.event']
        for appoint in self:
            cal_vals = {}
            partner_list = []
            partner_list.append(appoint.partner_id.id)
            for emp in appoint.employee_ids:
                if emp.address_home_id:
                    if emp.address_home_id.id not in partner_list:
                        partner_list.append(emp.address_home_id.id)
                else:
                    raise UserError(_('If you need to make appointment for employee \'%s\', You should fill Private Address.') % emp.name)
            cal_vals['partner_ids'] = [(6, 0, partner_list)]
            cal_vals['name'] = 'Ref: '+appoint.name
            #cal_vals['start_datetime'] = appoint.start_datetime
            cal_vals['duration'] = appoint.duration
            cal_vals['location'] = appoint.config_id.name or appoint.location
            cal_vals['description'] = appoint.description
            cal_vals['alarm_ids'] = [(6, 0, appoint.alarm_ids.ids)]
            start = appoint.start_datetime
            cal_vals['start'] = appoint.start_datetime
            #cal_vals['stop'] = start + timedelta(hours=cal.duration) - timedelta(seconds=1)
            cal_vals['stop'] = start + timedelta(hours=appoint.duration)
            #cal_vals['stop_datetime'] = start + timedelta(hours=appoint.duration)
            #print("ggggg",cal_vals['start'],cal_vals['stop'])
            #print("lllll",appoint.partner_id.ids)
            cal_vals['appointment_id'] = appoint.id
            cal_id = obj_calendar.create(cal_vals)
            appoint.meeting_ids = [(4, cal_id.id)]
            appoint._action_confirm()
    
    #@api.multi
    def action_view_pos_order(self):
        action = self.env.ref('point_of_sale.action_pos_pos_form').sudo().read()[0]
        pos_order = self.mapped('pos_order_ids')
        if len(pos_order) > 1:
            action['domain'] = [('id', 'in', pos_order.ids)]
        elif pos_order:
            action['views'] = [(self.env.ref('point_of_sale.view_pos_pos_form').id, 'form')]
            action['res_id'] = pos_order.id
        return action
    
    #@api.multi
    def action_view_meeting_appointment(self):
        action = self.env.ref('calendar.action_calendar_event').sudo().read()[0]
        meeting_id = self.mapped('meeting_ids')
        if len(meeting_id) > 1:
            action['domain'] = [('id', 'in', meeting_id.ids)]
        elif meeting_id:
            action['views'] = [(self.env.ref('calendar.view_calendar_event_form').id, 'form')]
            action['res_id'] = meeting_id.id
        return action
    
    #@api.multi
    def _action_confirm(self):
        ##modify
        ## NOTE DISABLED here since we don't need an order created
        # self.action_payment()
        #######

        return self.write({'state': 'confirmed'})
    #@api.multi
    #def _action_order(self):
    #    return self.write({'state': 'order'})
    
    #@api.multi
    def _action_paid(self):
        return self.write({'state': 'paid'})
    #@api.multi
    def action_cancel(self):
        flag = 0
        if self.pos_order_ids:
            for order in self.pos_order_ids:
                if order.state in ['paid','done']:
                    flag = 1
        if flag == 0:
            if self.pos_order_ids:
                for order in self.pos_order_ids:
                    if order.state in ['draft']:
                        order.write({'state': 'cancel'})
            if self.meeting_ids:
                for cal in self.meeting_ids:
                    cal.unlink()
            return self.write({'state': 'cancel'})
        else:
            raise UserError(_('You cannot cancel this appointment, because they contains Paid/Posted order '))
    #@api.multi
    def action_cancel_meeting(self):
        if self.meeting_ids:
            for cal in self.meeting_ids:
                cal.unlink()
    #@api.multi
    def action_draft(self):
        orders = self.filtered(lambda s: s.state in ['cancel'])
        return orders.write({
            'state': 'draft',
        })
    def action_ongoing(self):
        orders = self.filtered(lambda s: s.state in ['confirmed'])
        return orders.write({
            'state': 'order',
        })
    def action_ready_for_pickup(self):
        orders = self.filtered(lambda s: s.state in ['order'])
        return orders.write({
            'state': 'ready',
        })
    #@api.multi
    def action_done(self):
        paid_flag = True
        for order in self.env['pos.order'].search([('appointment_id', '=', self.id),('state', 'not in', ['cancel'])]):
            if order.state != 'paid':
                paid_flag = False
        if paid_flag:
            #return self.write({'state': 'paid'})
            return self._action_paid()
        else:
            return self.write({'state': 'done'})


    #@api.multi
    #def action_unlock(self):
    #    if self.is_purchase_order == True:
    #        self.write({'state': 'order2'})
    #    else:
    #        self.write({'state': 'order'})
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
           vals['name'] = self.env['ir.sequence'].next_by_code('pos.appointments') or _('New')
        result = super(PosAppointments, self).create(vals)
        return result

    def zero_pad(self,num,size):
        s = "" + str(num)
        while (len(s) < size):
            s = "0" + s
        return s

    #@api.multi
    def action_payment(self):
        self.ensure_one()
        obj_pos = self.env['pos.order']
        obj_pos_line = self.env['pos.order.line']
        obj_session = self.env['pos.session']
        session = obj_session.search([('state', '=', 'opened'), ('config_id', '=', self.config_id.id)])
        if not session:
            raise UserError(_('You have to open POS \'%s\' session first.') % self.config_id.name)
        else:
            for appoint in self:
                pos_vals = {}
                pos_vals['lines'] = []
                pos_vals['partner_id'] = appoint.partner_id.id
                #pos_vals['name'] = 
                pos_vals['session_id'] = session[0].id
                #pos_vals['pos_reference'] = "Order " + str(session.id) + '-' + str(session.login_number) + '-' + str(session.sequence_number)
                pos_vals['pos_reference'] = "Order " + self.zero_pad(session.id,5) + '-' + self.zero_pad(session.login_number,3)\
                                            + '-' + str(self.env['ir.sequence'].next_by_code('appointment.pos.receipt'))
                pos_vals['date_order'] = datetime.now()
                pos_vals['amount_tax'] = 0.0
                pos_vals['amount_total'] = 0.0
                pos_vals['amount_paid'] = 0.0
                pos_vals['amount_return'] = 0.0
                res = self.env['product.pricelist']._get_partner_pricelist_multi(appoint.partner_id.ids,company_id=appoint.company_id.id)
                pricelist = res.get(appoint.partner_id.id)
                if pricelist:
                    pos_vals['pricelist_id'] = pricelist.id
                pos_id = obj_pos.create(pos_vals)
                pos_line_val={}
                for line in appoint.appointment_line:
                    pos_line_val['product_id'] = line.product_id.id
                    pos_line_val['qty'] = 1.0
                    pos_line_val['price_unit'] = line.pos_untax_amt
                    pos_line_val['tax_ids'] = [(6, 0, line.tax_ids.ids)]
                    pos_line_val['price_subtotal'] = 0.0
                    pos_line_val['price_subtotal_incl'] = 0.0
                    pos_line_val['full_product_name'] = line.product_id.name

                    pos_line_val['order_id'] = pos_id.id
                    pos_line_id = obj_pos_line.create(pos_line_val)
                    pos_line_id._onchange_amount_line_all()
                
                appoint.pos_order_ids = [(4, pos_id.id)]
                pos_id._onchange_amount_all()
                ##modify
                #appoint._action_order()

                session.sequence_number += 1
        
        
class AppointmentLine(models.Model):
    _name = 'pos.appointments.line'
    _description = 'Appointment Line'
    _order = 'sequence, id'

    """@api.depends('product_id')
    def _compute_untax_amt(self):
        if self.product_id.lst_price:
            self.untax_amt = self.product_id.lst_price
        else:
            self.untax_amt = 0.0"""

    #@api.multi
    def _compute_tax_id(self):
        for line in self:
            taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            print("taxes",taxes)
            line.tax_ids = taxes

    #@api.multi
    def _get_display_price(self, product, pricelist):
        #no_variant_attributes_price_extra = [
        #    ptav.price_extra for ptav in self.product_no_variant_attribute_value_ids.filtered(
        #        lambda ptav:
        #        ptav.price_extra and
        #        ptav not in product.product_template_attribute_value_ids
        #    )
        #]
        #if no_variant_attributes_price_extra:
        #    product = product.with_context(
        #        no_variant_attributes_price_extra=no_variant_attributes_price_extra
        #    )

        if pricelist.discount_policy == 'with_discount':
            return product.with_context(pricelist=pricelist.id).price
        product_context = dict(self.env.context, partner_id=self.appointment_id.partner_id.id, date=self.appointment_id.create_date,
                               )

        final_price, rule_id = pricelist.with_context(product_context).get_product_price_rule(
            self.product_id, 1.0, self.appointment_id.partner_id)
        base_price, currency = self.with_context(product_context)._get_real_price_currency(product, rule_id,
                                                                                           pricelist.id)
        if currency != pricelist.currency_id:
            base_price = currency._convert(
                base_price, pricelist.currency_id,
                self.appointment_id.company_id or self.env.company, self.appointment_id.create_date or fields.Date.today())
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.depends('tax_ids', 'untax_amt')
    def _amount_all(self):
        print("_amount_all",self)
        total_amount = 0.0
        for line in self:
            if line.appointment_id.partner_id.property_product_pricelist:
                #line.appointment_id.partner_id.property_product_pricelist
                res = self.env['product.pricelist']._get_partner_pricelist_multi(line.appointment_id.partner_id.ids, company_id=line.company_id.id)
                pricelist = res.get(line.appointment_id.partner_id.id)
                price_unit = line.env['account.tax']._fix_tax_included_price_company(
                    line._get_display_price(line.product_id, pricelist),
                    line.tax_ids, line.tax_ids, line.company_id)
                line.pos_untax_amt = price_unit
            elif line.product_id.lst_price:
                line.pos_untax_amt = line.product_id.lst_price
            else:
                line.pos_untax_amt = 0.0
            #line._compute_tax_id()

            #if line.untax_amt:
            #total_amount = self.untax_amt
            #if line.tax_ids:
            taxes = line.tax_ids.compute_all(line.pos_untax_amt, line.currency_id, product=line.product_id,
                                             partner=line.appointment_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'total_amt': taxes['total_included'],
                'untax_amt': taxes['total_excluded'],
            })
                    #total_amount = total_amount + (taxes['total_included'] - line.untax_amt)
            #self.total_amt = total_amount



    #@api.one
    @api.depends('company_id')
    def _compute_currency(self):
        for res in self:
            res.currency_id = res.company_id.currency_id or res.env.user.company_id.currency_id

    appointment_id = fields.Many2one('pos.appointments', string='Appointment Reference', required=True, ondelete='cascade', index=True,
                               copy=False)
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    product_id = fields.Many2one('product.product', string='Service', required=True, domain=[('sale_ok', '=', True), ('type', '=', 'service')],
                                 change_default=True, ondelete='restrict')
    untax_amt = fields.Float('Untax Amount', store=True, readonly=True, compute='_amount_all', digits=dp.get_precision('Product Price'))
    tax_ids = fields.Many2many('account.tax', string='Taxes',
                               domain=['|', ('active', '=', False), ('active', '=', True)],
                               help="Taxes that apply on the base amount")
    price_tax = fields.Float(compute='_amount_all', string='Total Tax', readonly=True, store=True)

    #total_amt = fields.Float('Total', store=True, readonly=True, compute='_amount_all', track_visibility='always',
    #                         track_sequence=6)
    total_amt = fields.Monetary(compute='_amount_all', string='Total', readonly=True, store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirmed', 'Confirmed'),
        #('order', 'Order'),
        #('paid', 'Paid'),
        ('order', 'Ongoing'),
        ('ready', 'Ready for Pickup'),
        ('done', 'Done'),
        ('paid', 'Done & Paid'),
    ], related='appointment_id.state', string='Appointment Status', readonly=True, copy=False, tracking=True, store=True, default='draft')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', compute='_compute_currency', oldname='currency', string="Currency")
    pos_untax_amt = fields.Float('POS Untax Amount', store=True, readonly=True, compute='_amount_all',
                             digits=dp.get_precision('Product Price'))

    #@api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        self.name = self.product_id.display_name
        self._compute_tax_id()

class Contacts(models.Model):
    """ Personnal calendar filter """

    _name = 'hr.user.pos.appointment.employee'
    _description = 'Work Entries Employees'

    user_id = fields.Many2one('res.users', 'Me', required=True, default=lambda self: self.env.user)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True)
    active = fields.Boolean('Active', default=True)

    _sql_constraints = [
        ('user_id_employee_id_unique', 'UNIQUE(user_id,employee_id)', 'You cannot have the same employee twice.')
    ]

    @api.model
    def unlink_from_employee_id(self, employee_id):
        return self.search([('employee_id', '=', employee_id)]).unlink()
