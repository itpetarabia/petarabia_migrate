# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from datetime import datetime
#from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
module_name = 'inventory_reordering_customize'

class ReorderingRequest(models.Model):
    _name = "reordering.request"
    _description = 'Transfer Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'date_order desc, id desc'

    READONLY_STATES = {
        'confirm': [('readonly', True)],
        'approved': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }



    @api.depends('request_line.date_planned', 'date_order')
    def _compute_date_planned(self):
        for order in self:
            min_date = False
            for line in order.request_line:
                if not min_date or line.date_planned < min_date:
                    min_date = line.date_planned
            if min_date:
                order.date_planned = min_date
            else:
                order.date_planned = order.date_order

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'internal'), ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'internal'), ('warehouse_id', '=', False)])
        return types[:1]

    def _default_source_warehouse(self):
        w_house = self.env['stock.warehouse'].search(
            [('reordering_warehouse', '=', True),('company_id', '=', self.env.user.company_id.id)])
        #print("w_house",w_house)
        if w_house:
            return w_house[0]
        return False

    name = fields.Char('Reference', required=True, index=True, copy=False, default='New')
    date_order = fields.Datetime(string='Date Order',required=True, states=READONLY_STATES, index=True, copy=False, default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('approved', 'Approved'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    request_line = fields.One2many('reordering.request.line', 'request_id', string='Request Lines',
                                 states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)
    notes = fields.Text('Terms and Conditions')
    user_id = fields.Many2one('res.users', string='Representative', index=True, tracking=True,
                              default=lambda self: self.env.user,copy=False)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, states=READONLY_STATES,
                                 default=lambda self: self.env.user.company_id.id)
    date_approve = fields.Date('Approval Date', readonly=1, index=True, copy=False)
    date_planned = fields.Datetime(string='Scheduled Date', compute='_compute_date_planned', store=True, index=True)
    picking_count = fields.Integer(compute='_compute_picking', string='Picking count', default=0, store=True)
    picking_ids = fields.Many2many('stock.picking', compute='_compute_picking', string='Transfers', copy=False,store=True)

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=READONLY_STATES,
                                      required=True, default=_default_picking_type,
                                      help="This will determine operation type of incoming shipment")
    is_shipped = fields.Boolean(compute="_compute_is_shipped")
    source_warehouse_id = fields.Many2one('stock.warehouse', 'From Warehouse', default=_default_source_warehouse, required=True, states=READONLY_STATES)
    dest_warehouse_id = fields.Many2one('stock.warehouse', 'To Warehouse', required=True, states=READONLY_STATES)

    @api.depends('request_line.move_ids.returned_move_ids',
                 'request_line.move_ids.state',
                 'request_line.move_ids.picking_id')
    def _compute_picking(self):
        for order in self:
            pickings = self.env['stock.picking']
            for line in order.request_line:
                moves = line.move_ids | line.move_ids.mapped('returned_move_ids')
                pickings |= moves.mapped('picking_id')
            order.picking_ids = pickings
            order.picking_count = len(pickings)

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_is_shipped(self):
        for order in self:
            if order.picking_ids and all([x.state in ['done', 'cancel'] for x in order.picking_ids]):
                order.is_shipped = True

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('reordering.request') or '/'
        return super(ReorderingRequest, self).create(vals)

    #@api.multi
    def action_set_date_planned(self):
        for order in self:
            order.request_line.update({'date_planned': order.date_planned})

    #@api.multi
    def button_approve(self):
        self.ensure_one()
        msg = self.product_qty_check_availability()
        action = self.env.ref('inventory_reordering_customize.action_transfer_request_validation').read()[0]
        try:
            if msg:
                action['context'] = {
                    'default_confirm_validation_message': msg,
                    'default_request_id': self.id,

                }
                action['view_type'] = 'form',
                action['view_mode'] = 'form',
                return action
            else:
                self.write({'state': 'approved', 'date_approve': fields.Date.context_today(self)})
                self.activity_schedule(
                    f'{module_name}.mail_act_manager_approval_transfer_req',
                    user_id=self.user_id.id)
                self.filtered(lambda hol: hol.state in ['approved']).activity_unlink(
                    [f'{module_name}.mail_act_manager_approval_transfer_req'])
                self._create_picking()
            return False
        except Exception as e:
            raise e

        return msg

    #@api.multi
    def button_draft(self):
        self.write({'state': 'draft'})
        return {}

    #@api.multi
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft']:
                continue
            if order.user_has_groups('inventory_reordering_customize.group_reordering_req_manager'):
                action = order.button_approve()
                return action
            else:
                order.write({'state': 'confirm'})
                for req_manger in self.env.ref(f"{module_name}.group_reordering_req_manager").sudo().users:
                    order.activity_schedule(
                        f'{module_name}.mail_act_manager_approval_transfer_req',
                        user_id=req_manger.id)
        return True



    #@api.multi
    def button_cancel(self):
        for order in self:
            for pick in order.picking_ids:
                if pick.state == 'done':
                    raise UserError(
                        _('Unable to cancel Transfer request %s as some transfers have already been done.') % (
                            order.name))
            if order.state in ('draft', 'confirm'):
                for order_line in order.request_line:
                    if order_line.move_dest_ids:
                        move_dest_ids = order_line.move_dest_ids.filtered(lambda m: m.state not in ('done', 'cancel'))
                        siblings_states = (move_dest_ids.mapped('move_orig_ids')).mapped('state')
                        if all(state in ('done', 'cancel') for state in siblings_states):
                            move_dest_ids.write({'procure_method': 'make_to_stock'})
                            move_dest_ids._recompute_state()

            for pick in order.picking_ids.filtered(lambda r: r.state != 'cancel'):
                pick.action_cancel()

            order.request_line.write({'move_dest_ids': [(5, 0, 0)]})

        self.write({'state': 'cancel'})

    #@api.multi
    def button_unlock(self):
        self.write({'state': 'approved'})

    #@api.multi
    def button_done(self):
        self.write({'state': 'done'})

    #@api.multi
    def action_view_picking(self):
        """ This function returns an action that display existing picking orders of given transfer request ids. When only one found, show the picking immediately.
        """
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        # override the context to get rid of the default filtering on operation type
        result['context'] = {}
        pick_ids = self.mapped('picking_ids')
        # choose the view_mode accordingly
        if not pick_ids or len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state, view) for state, view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = pick_ids.id
        return result

    #@api.multi
    def _get_destination_location(self):
        self.ensure_one()
        return self.dest_warehouse_id.lot_stock_id.id

    #@api.multi
    def _get_source_location(self):
        self.ensure_one()
        return self.source_warehouse_id.lot_stock_id.id
    #@api.multi
    def _get_piking_type_id(self):
        if self.dest_warehouse_id:
            type = self.env['stock.picking.type'].search([('code','=','internal'),('warehouse_id','=',self.dest_warehouse_id.id)])
            if type:
                return type[0]
        return self.picking_type_id
    @api.model
    def _prepare_picking(self):
        return {
            'picking_type_id': self._get_piking_type_id().id,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self._get_source_location(),
            'company_id': self.company_id.id,
        }

    #@api.multi
    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self:
            if any([ptype in ['product', 'consu'] for ptype in order.request_line.mapped('product_id.type')]):
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.create(res)
                else:
                    picking = pickings[0]
                moves = order.request_line._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()

        return True


    def product_qty_check_availability(self):
        message2 = ''
        for line in self.request_line:
            message = ''
            if line.request_id.dest_warehouse_id:
                dest_loc = self.dest_warehouse_id.lot_stock_id
                orderpoint = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', line.product_id.id),('location_id', '=', dest_loc.id)])
                if orderpoint:
                    orderpoint = orderpoint[-1]
                    real_quant = 0
                    quant = self.env['stock.quant'].search([('product_id','=',line.product_id.id),('location_id','=',dest_loc.id)])
                    if quant:
                        real_quant = sum(quant.mapped('quantity'))
                    qty = (real_quant + line.product_qty) - orderpoint.product_max_qty
                    if qty > 0:
                        message += _(
                            'Destination location: %s,\nProduct quantity will be %s greater than the maximum quantity of reordering rule.\n\n') % \
                                  (dest_loc.display_name, qty)

            if line.request_id.source_warehouse_id:
                source_loc = self.source_warehouse_id.lot_stock_id
                orderpoint = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', line.product_id.id),('location_id', '=', source_loc.id)])
                if orderpoint:
                    orderpoint = orderpoint[-1]
                    real_quant = 0
                    quant = self.env['stock.quant'].search([('product_id','=',line.product_id.id),('location_id','=',source_loc.id)])
                    if quant:
                        real_quant = sum(quant.mapped('quantity'))
                    qty = orderpoint.product_min_qty - (real_quant - line.product_qty)
                    if qty > 0:
                        message += _(
                            'Source location: %s,\nProduct quantity will be %s less than the minimum quantity of reordering rule.\n\n') % \
                                  (source_loc.display_name, qty)

            if message:
                message2 += _('Product: %s\n\n') % (line.product_id.name)
                message2 += message

        if message2:
            return message2

    def run_scheduler(self):
        print("run_scheduler")
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        print("warehouse_ids",warehouse_ids)
        orderpoint = self.env['stock.warehouse.orderpoint'].search(
            [('company_id', '=', company),('warehouse_id', 'not in', warehouse_ids.ids)])
        print("orderpoint",orderpoint)
        if orderpoint:
            whouse_ids = orderpoint.mapped('warehouse_id')
            for wh in whouse_ids:
                orderpoint2 = self.env['stock.warehouse.orderpoint'].search(
                    [('company_id', '=', company), ('warehouse_id', 'in', wh.ids)])
                product_ids = orderpoint2.mapped('product_id')
                flag = 0
                obj_req_line = self.env['reordering.request.line']
                req_line_val = {}
                print("product_ids",product_ids)
                for product in product_ids:
                    if product.type == 'product':
                        real_quant = 0
                        dest_loc = wh.lot_stock_id
                        quant = self.env['stock.quant'].search(
                            [('product_id', '=', product.id), ('location_id', '=', dest_loc.id)])
                        if quant:
                            real_quant = sum(quant.mapped('quantity'))
                        else:
                            real_quant = 0
                        orderpoint3 = self.env['stock.warehouse.orderpoint'].search(
                            [('company_id', '=', company), ('warehouse_id', 'in', wh.ids), ('product_id', '=', product.id)])
                        if orderpoint3:
                            min_qty = orderpoint3[-1].product_min_qty
                            max_qty = orderpoint3[-1].product_max_qty
                            if real_quant < min_qty:
                                qty = max_qty - real_quant
                                request_ids = self.env['reordering.request'].search([('dest_warehouse_id', '=', wh.id), ('state', 'in', ['draft','confirm'])])
                                transfer_qty = 0
                                for request_id in request_ids:
                                    transfer_qty += sum(request_id.request_line.filtered(lambda m: m.product_id == product).mapped('product_qty'))
                                qty = qty - transfer_qty
                                if qty > 0:
                                    if flag == 0:
                                        req_id = self.env['reordering.request'].create_transfer_request(product,qty,warehouse_ids,wh,company)
                                    flag = 1
                                    if req_id:
                                        req_line_val['product_id'] = product.id
                                        req_line_val['name'] = product.name
                                        req_line_val['date_planned'] = fields.Datetime.now()
                                        req_line_val['product_qty'] = qty
                                        req_line_val['product_uom'] = product.uom_id.id
                                        req_line_val['request_id'] = req_id.id
                                        obj_req_line.create(req_line_val)
    #@api.multi
    def create_transfer_request(self, product,qty,warehouse_ids,wh,company):
        obj_req = self.env['reordering.request']

        req_vals = {}
        req_vals['request_line'] = []
        req_vals['date_order'] = fields.Datetime.now()
        req_vals['source_warehouse_id'] = warehouse_ids.id
        req_vals['dest_warehouse_id'] = wh.id
        req_vals['company_id'] = company
        req_id = obj_req.create(req_vals.copy())
        return req_id


    def unlink(self):
        for order in self:
            if not order.state == 'cancel':
                raise UserError(_('In order to delete a transfer request, you must cancel it first.'))
        return super(ReorderingRequest, self).unlink()

class ReorderingRequestLine(models.Model):
    _name = 'reordering.request.line'
    _description = 'Transfer Request Line'
    _order = 'request_id, sequence, id'

    @api.onchange('product_qty')
    def _onchange_product_qty_check_availability(self):
        for line in self:
            message = ''
            if line.request_id.dest_warehouse_id:
                dest_loc = line.request_id.dest_warehouse_id.lot_stock_id
                orderpoint = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', line.product_id.id),('location_id', '=', dest_loc.id)])
                if orderpoint:
                    orderpoint = orderpoint[0]
                    real_quant = 0
                    quant = self.env['stock.quant'].search([('product_id','=',line.product_id.id),('location_id','=',dest_loc.id)])
                    if quant:
                        real_quant = sum(quant.mapped('quantity'))
                    qty = (real_quant + line.product_qty) - orderpoint.product_max_qty
                    if qty > 0:
                        message += _(
                            'Destination location: %s,\nProduct quantity will be %s greater than the maximum quantity of reordering rule.\n\n') % \
                                  (dest_loc.display_name, qty)

            if line.request_id.source_warehouse_id:
                source_loc = line.request_id.source_warehouse_id.lot_stock_id
                orderpoint = self.env['stock.warehouse.orderpoint'].search([('product_id', '=', line.product_id.id),('location_id', '=', source_loc.id)])
                if orderpoint:
                    orderpoint = orderpoint[0]
                    real_quant = 0
                    quant = self.env['stock.quant'].search([('product_id','=',line.product_id.id),('location_id','=',source_loc.id)])
                    if quant:
                        real_quant = sum(quant.mapped('quantity'))
                    qty = orderpoint.product_min_qty - (real_quant - line.product_qty)
                    if qty > 0:
                        message += _(
                            'Source location: %s,\nProduct quantity will be %s less than the minimum quantity of reordering rule.\n\n') % \
                                  (source_loc.display_name, qty)

            if message:
                message2 = _('Product: %s\n\n') % (line.product_id.name)
                message2 += message
                warning_mess = {
                    'title': _('Product qty warning!'),
                    'message': message2
                }
                return {'warning': warning_mess}

    #@api.multi
    @api.depends('product_uom', 'product_qty', 'product_id.uom_id')
    def _compute_product_uom_qty(self):
        for line in self:
            if line.product_id.uom_id != line.product_uom:
                line.product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
            else:
                line.product_uom_qty = line.product_qty


    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True)
    product_uom_qty = fields.Float(string='Total Quantity', compute='_compute_product_uom_qty', store=True)
    date_planned = fields.Datetime(string='Scheduled Date', required=True, index=True)
    product_uom = fields.Many2one('uom.uom', string='Product Unit of Measure', required=True)
    product_id = fields.Many2one('product.product', string='Product', domain=[('purchase_ok', '=', True)], change_default=True, required=True)
    product_image = fields.Binary(
        'Product Image', related="product_id.image_1920", readonly=False,
        help="Non-stored related field to allow portal user to see the image of the product he has ordered")
    product_type = fields.Selection(related='product_id.type', readonly=True)

    request_id = fields.Many2one('reordering.request', string='Request Reference', index=True, required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', related='request_id.company_id', string='Company', store=True, readonly=True)
    state = fields.Selection(related='request_id.state', store=True, readonly=False)

    date_order = fields.Datetime(related='request_id.date_order', string='Order Date', readonly=True)

    move_ids = fields.One2many('stock.move', 'reordering_line_id', string='Reservation', readonly=True,
                               ondelete='set null', copy=False)
    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint', 'Orderpoint')
    move_dest_ids = fields.One2many('stock.move', 'created_reordering_line_id', 'Downstream Moves')


    #@api.multi
    def unlink(self):
        for line in self:
            if line.request_id.state in ['approved', 'done']:
                raise UserError(_('Cannot delete a transfer request line which is in state \'%s\'.') % (line.state,))
        return super(ReorderingRequestLine, self).unlink()

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = {}
        if not self.product_id:
            return result

        self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        #self.price_unit = 0.0
        self.product_qty = 1.0
        self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
        result['domain'] = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

        self.name = self.product_id.name
        return result





    @api.model
    def create(self, values):
        line = super(ReorderingRequestLine, self).create(values)
        if line.request_id.state == 'approved':
            line._create_or_update_picking()
        return line

    #@api.multi
    def write(self, values):
        result = super(ReorderingRequestLine, self).write(values)
        # Update expected date of corresponding moves
        if 'date_planned' in values:
            self.env['stock.move'].search([
                ('reordering_line_id', 'in', self.ids), ('state', '!=', 'done')
            ]).write({'date': values['date_planned']})
        if 'product_qty' in values:
            self.filtered(lambda l: l.request_id.state == 'approved')._create_or_update_picking()
        return result

    #@api.multi
    def _create_or_update_picking(self):
        for line in self:
            if line.product_id.type in ('product', 'consu'):
                # If the user increased quantity of existing line or created a new line
                pickings = line.request_id.picking_ids.filtered(
                    lambda x: x.state not in ('done', 'cancel') and x.location_dest_id.usage in (
                    'internal', 'transit', 'customer'))
                picking = pickings and pickings[0] or False
                if not picking:
                    res = line.request_id._prepare_picking()
                    picking = self.env['stock.picking'].create(res)
                move_vals = line._prepare_stock_moves(picking)
                for move_val in move_vals:
                    self.env['stock.move'] \
                        .create(move_val) \
                        ._action_confirm() \
                        ._action_assign()

    #@api.multi
    def _prepare_stock_moves(self, picking):
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        for move in self.move_ids.filtered(
                lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        template = {
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'create_date': self.request_id.date_order,
            'date': self.date_planned,
            'location_id': self.request_id._get_source_location(),
            'location_dest_id': self.request_id._get_destination_location(),
            'picking_id': picking.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'reordering_line_id': self.id,
            'company_id': self.request_id.company_id.id,
            'picking_type_id': self.request_id._get_piking_type_id().id,
            'origin': self.request_id.name,
            'route_ids': self.request_id._get_piking_type_id().warehouse_id and [
                (6, 0, [x.id for x in self.request_id._get_piking_type_id().warehouse_id.route_ids])] or [],
            'warehouse_id': self.request_id._get_piking_type_id().warehouse_id.id,
        }
        diff_quantity = self.product_qty - qty
        if float_compare(diff_quantity, 0.0, precision_rounding=self.product_uom.rounding) > 0:
            quant_uom = self.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            # Always call '_compute_quantity' to round the diff_quantity. Indeed, the PO quantity
            # is not rounded automatically following the UoM.
            if get_param('stock.propagate_uom') != '1':
                product_qty = self.product_uom._compute_quantity(diff_quantity, quant_uom, rounding_method='HALF-UP')
                template['product_uom'] = quant_uom.id
                template['product_uom_qty'] = product_qty
            else:
                template['product_uom_qty'] = self.product_uom._compute_quantity(diff_quantity, self.product_uom,
                                                                                 rounding_method='HALF-UP')
            res.append(template)
        return res

    #@api.multi
    def _create_stock_moves(self, picking):
        values = []
        for line in self:
            for val in line._prepare_stock_moves(picking):
                values.append(val)
        return self.env['stock.move'].create(values)




class TransferRequestValidation(models.TransientModel):
    _name = 'transfer.request.validation'

    request_id = fields.Many2one('reordering.request')
    confirm_validation_message = fields.Text()

    #@api.multi
    def action_save(self):
        self.request_id.write({'state': 'approved', 'date_approve': fields.Date.context_today(self.request_id)})
        self.request_id.activity_schedule(
            f'{module_name}.mail_act_manager_approval_transfer_req',
            user_id=self.request_id.user_id.id)
        self.request_id.filtered(lambda hol: hol.state in ['approved']).activity_unlink(
            [f'{module_name}.mail_act_manager_approval_transfer_req'])
        self.request_id._create_picking()
        return True

    #@api.multi
    def action_cancel(self):
        return True
