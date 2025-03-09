from odoo import fields, models


class HelpdeskTicketChannel(models.Model):

    _name = "helpdesk.ticket.channel"
    _description = "Helpdesk Ticket Channel"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
