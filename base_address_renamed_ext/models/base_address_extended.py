from odoo import api, fields, models, _
from odoo.exceptions import UserError
import re


# from dateutil.relativedelta import relativedelta
# from datetime import datetime, date, timedelta

# from odoo.addons import decimal_precision as dp


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_default_country_id(self):
        bh_country = self.env.ref('base.bh')
        if bh_country:
            return bh_country.id

    # def _get_default_child_name(self):
    #    print("context",self.env.context)

    @api.model
    def set_street_format(self):
        bh_country = self.env.ref('base.bh')
        bh_country.write({f'address_format': '%(street)s\n%(state_code)s\n%(country_name)s'})
        bh_country.write({f'street_format': '%(street_name)s\nFlat/Shop No. %(street_number2)s, Building: %(street_number)s,\nRoad/Street: %(street2)s, %(city)s,\nBlock: %(zip)s'})

    def _get_default_name(self):
        context = self._context
        if 'child_ids' in context:
            count = len(context.get('child_ids', [])) + 1
            return count

    name = fields.Char(default=_get_default_name)
    street_name = fields.Char(string='Street Name', inverse='_inverse_street_data', store=True)
    street_number = fields.Char(string='Building', inverse='_inverse_street_data', store=True)
    street_number2 = fields.Char(string='Flat', inverse='_inverse_street_data', store=True )
    street2 = fields.Char(string="Street/Road", inverse='_inverse_street_data', store=True)
    city = fields.Char(string='Area', inverse='_inverse_street_data', store=True)
    # city_id = fields.Many2one(string='Area', inverse='_inverse_street_data', store=True, domain="[('country_id', '=?', country_id)]")
    zip = fields.Char(string='Block', inverse='_inverse_street_data', store=True)
    country_id = fields.Many2one('res.country', default=_get_default_country_id)

    # @api.onchange('city_id')
    # def _onchange_city_id(self):
    #     if self.city_id:
    #         self.city = self.city_id.name
    #         #self.zip = self.city_id.zipcode
    #         self.state_id = self.city_id.state_id
    #         if self.city_id.country_id:
    #             self.country_id = self.city_id.country_id
    #     elif self._origin:
    #         self.city = False
    #         #self.zip = False
    #         self.state_id = False

    # @api.onchange('zip', 'country_id')
    # def _onchange_zip_and_country(self):
    #     if self.zip:
    #         Cities = self.env['res.city']
    #         recs = Cities.search([
    #             ('zipcode', '=', self.zip),
    #             ('country_id', '=', self.country_id.id)]
    #             )
    #         if recs:
    #             self.city_id = recs[0]

            

    def _get_street_fields(self):
        """Returns the fields that can be used in a street format.
        Overwrite this function if you want to add your own fields."""
        #return ['street_name', 'street_number', 'street_number2','street2', 'zip', 'city','city_id']
        return super(ResPartner, self)._get_street_fields() + ['street2', 'zip', 'city']

    # @api.onchange('city_id')
    # def onchange_city_id(self):
    #    city = self.city_id.name or ''
    @api.model
    def _get_default_address_format(self):
        # return "%(street)s\nRoad: %(street2)s\nArea: %(city)s %(state_code)s, Block: %(zip)s\n%(country_name)s"
        # return "Building: %(street_number)s, Flat: %(street_number2)s, Street: %(street2)s\nArea: %(city)s %(state_code)s, Block: %(zip)s\n%(country_name)s"
        return "%(street)s\n%(state_code)s\n%(country_name)s"

    @api.depends('street')
    def _compute_street_data(self):
        # ignore this function
        pass
        # super()._compute_street_data()
    #     """Splits street value into sub-fields.
    #     Recomputes the fields of STREET_FIELDS when `street` of a partner is updated"""
    #     street_fields = self._get_street_fields()
    #     print("street_fields==",street_fields)
    #     for partner in self:
    #         if not partner.street:
    #             for field in street_fields:
    #                 partner[field] = None
    #             continue

    #         # street_format = (partner.country_id.street_format or
    #         #                 '%(street_number)s/%(street_number2)s %(street_name)s')
    #         street_format = (partner.country_id.street_format or
    #                          'Building: %(street_number)s, Flat: %(street_number2)s\nStreet: %(street2)s, Area: %(city)s\nBlock: %(zip)s')

    #         street_raw = partner.street
    #         vals = self._split_street_with_params(street_raw, street_format)
    #         # assign the values to the fields
    #         print("vals==", vals)
    #         for k, v in vals.items():
    #             partner[k] = v
    #             print("partner[k]==", partner[k])
    #         for k in set(street_fields) - set(vals):
    #             partner[k] = None
    #             print("partner[k]2==", partner[k])

    def _inverse_street_data(self):
        """Updates the street field.
        Writes the `street` field on the partners when one of the sub-fields in STREET_FIELDS
        has been touched"""
        street_fields = self._get_street_fields()
        for partner in self:
            street_format = (partner.country_id.street_format or
                '%(street_number)s/%(street_number2)s %(street_name)s')
            previous_field = None
            previous_pos = 0
            street_value = ""
            separator = ""
            # iter on fields in street_format, detected as '%(<field_name>)s'
            for re_match in re.finditer(r'%\((\w+)\)s', street_format):
                field_name = re_match.group(1)
                field_pos = re_match.start()
                if field_name not in street_fields:
                    raise UserError(_("Unrecognized field %s in street format.", field_name))
                if not previous_field:
                    # first iteration: add heading chars in street_format
                    if partner[field_name]:
                        street_value += street_format[0:field_pos] + partner[field_name]
                else:
                    # get the substring between 2 fields, to be used as separator
                    separator = street_format[previous_pos:field_pos]
                    if partner[field_name]:
                        street_value += separator + partner[field_name]
                previous_field = field_name
                previous_pos = re_match.end()

            # add trailing chars in street_format
            street_value += street_format[previous_pos:]
            # trim other trailing chars
            street_value = re.sub(r'^[\s,]+', '', street_value)
            street_value = re.sub(r'[\s,]+$', '', street_value)
            partner.street = street_value

    def write(self, vals):
        res = super(ResPartner, self).write(vals)
        self.check_chd_dupl_name()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        partners = super(ResPartner, self).create(vals_list)
        partners.check_chd_dupl_name()
        return partners

    def check_chd_dupl_name(self):
        for part in self.filtered(lambda p: p.child_ids):
            for ch in part.child_ids:
                duplicates = part.child_ids.filtered(lambda p: p.id != ch.id and \
                                                               ch.name == p.name)
                if duplicates:
                    raise UserError(_(f"Please avoid customer name duplication\n\n" \
                                      f"Contact Name: {duplicates[0].name}\n" \
                                      f"Duplicate Count: {len(duplicates)}"))
