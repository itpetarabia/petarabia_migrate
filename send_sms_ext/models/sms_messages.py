from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class SmsMessagesGateway(models.Model):

    _name = 'sms.messages.gateway'
    _description = 'SMS Messages'
    _rec_name = 'name'
    _order = "date Desc"

    name = fields.Char('Sender ID',required=True)
    sms_type = fields.Selection([('delivery','Delivery Note'),('appointment','Reminder Appointment'),('appointment_confirm','Confirm Appointment'),('appointment_pickup','Appointment: Ready for Pickup'),('point_of_sale','POS: Payment done')], string='SMS for', required=True)
    message = fields.Text(string='Message', required=True)
    date = fields.Datetime('Date', default=lambda self: fields.Datetime.now(),required=True)
    state = fields.Selection([('draft','Draft'),('confirm', 'Confirm'),('done', 'Done'),('cancel', 'Cancelled')], string='Status', index=True, readonly=True, default='draft', tracking=True, copy=False)
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, readonly=True,states={'draft': [('readonly', False)]},default=lambda self: self.env.company)
    
    def sms_confirm(self):
        return self.write({'state':'confirm'})
        
    def sms_cancel(self):
        return self.write({'state':'cancel'})

    def sms_draft(self):
        return self.write({'state': 'draft'})
        
    