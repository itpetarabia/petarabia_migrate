from odoo.exceptions import ValidationError, UserError
from odoo import api, fields, models, _


class Pet(models.Model):
    _name = "res.pet"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Pet's Details"
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, tracking=True)

    reference = fields.Char(string='Reference', required=True, copy=False,
                            readonly=True, default=lambda self: _('New'))

    dob = fields.Date(string='DoB', tracking=True, copy=False)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], required=True, default='male', tracking=True)

    note = fields.Text(string='Notes')
    parent_id = fields.Many2one("res.partner", string="Parent", required=True)

    type_id = fields.Many2one("pet.type", string="Type", required=True)
    breed = fields.Char(string="Breed")

    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([('alive', 'Alive'), ('dead', 'Dead')],
                              default="alive", string="Status", tracking=True)
    color_id = fields.Many2one("pet.color", string="Color", required=True)
    size = fields.Selection([
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large')
    ], tracking=True)
    issues = fields.Text(string='Issues')
    behavior = fields.Text(string='Behavior')

    @api.model
    def create(self, vals):
        # if vals.get('note') is False:
        #     vals['note'] = 'New Pet'
        # Generate a reference from the sequence
        vals['reference'] = self.env['ir.sequence'].next_by_code('res.pet') or _('New')
        return super().create(vals)

    @api.model
    def default_get(self, fields):
        """
        fields --> ['reference', 'gender', 'name'... ] # All Fields
        res --> {'gender': 'male', 'reference': 'New', ..}
        """
        res = super().default_get(fields)
        return res
    
    def copy(self, default=None):
        if default is None:
            default = {}
        if not default.get('name'):
            default['name'] = _(f'{self.name} (Copy)')
        default['note'] = 'Copied Data'
        return super().copy(default)

    def action_dead(self):
        for rec in self:
            if rec.active:
                rec.active = False
                rec.state = "dead"
            else:
                raise UserError("You can't mark an archived pet as 'Dead', you must unarchive it first")

    def action_unarchive(self):
        for rec in self:
            if rec.state == 'dead':
                raise UserError("You can't unarchive a dead pet!")
        super().action_unarchive()

    # @api.constrains('name')
    # def check_name(self):
    #     for rec in self:
    #         # To search through the database for records that match self's name
    #         patients = self.env['hospital.patient'].search([('name', '=', rec.name),
    #                                                         ('id', '!=', rec.id)])
    #         if patients:
    #             raise ValidationError(_(f"Name `{rec.name}` Already Exists!"))

    # @api.constrains('age')
    # def check_age(self):
    #     for rec in self:
    #         if self.age <= 0:
    #             raise ValidationError(_(f"Age Cannot Be Zero!"))
    
    def name_get(self):
        result = []
        for rec in self:
            name = f"[{rec.type_id.name}] {rec.name}"
            result.append([rec.id, name])
        return result


class PetType(models.Model):
    _name = "pet.type"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Pet Types"
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True, tracking=True)

    reference = fields.Char(string='Reference', required=True, copy=False,
                            readonly=True, default=lambda self: _('New'))
    active = fields.Boolean(string='Active', default=True)

    @api.model
    def create(self, vals):
        # Generate a reference from the sequence
        vals['reference'] = self.env['ir.sequence'].next_by_code('pet.type') or _('New')
        return super().create(vals)
    
    def copy(self, default=None):
        if default is None:
            default = {}
        if not default.get('name'):
            default['name'] = _(f'{self.name} (Copy)')
        return super().copy(default)
    

class PetColor(models.Model):
    _name = "pet.color"
    _description = "Pet Colors"
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    _sql_constraints = [('unique_name', 'unique(name)', 'This color has already been defined.')]