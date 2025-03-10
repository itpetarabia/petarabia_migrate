from odoo import fields, models


class HelpdeskTicketTag(models.Model):
    _name = "helpdesk.ticket.tag"
    _description = "Helpdesk Ticket Tag"

    name = fields.Char(string="Name")
    color = fields.Integer(string="Color Index")
    active = fields.Boolean(default=True)
