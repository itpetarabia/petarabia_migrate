from odoo import fields, models


class HelpdeskCategory(models.Model):

    _name = "helpdesk.ticket.category"
    _description = "Helpdesk Ticket Category"

    active = fields.Boolean(
        string="Active",
        default=True,
    )
    name = fields.Char(
        string="Name",
        required=True,
        translate=True,
    )
