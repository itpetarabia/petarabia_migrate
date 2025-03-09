# -*- coding: utf-8 -*-
import io
import logging

import numpy as np
import pandas as pd
from pandas.api.types import CategoricalDtype
from odoo import fields, models, _
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

try:
    import openpyxl
except ImportError:
    _logger.debug('Cannot `import openpyxl`.')
try:
    import pandas as pd
except ImportError:
    _logger.debug('Cannot `import pandas`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


ALLOWED_CHARS_IN_BARCODES = """-/\\_"""
    
class ImportProductWizard(models.TransientModel):
    _name='import.product.wizard'
    _description = "Import Product Line"

    product_file=fields.Binary(string="Select File")
    sample_option = fields.Selection([('csv', 'CSV'),('xlsx', 'Excel')], string='Sample Type', default='xlsx')
    down_samp_file = fields.Boolean(string='Download Sample Files')
    
    friendly_columns_to_official = {
        'Name': {'db_name': 'name', 'dtype': str, 'non-null': True},
        'Barcode': {'db_name': 'barcode', 'dtype': str},
        'Internal Reference': {'db_name': 'default_code', 'dtype': str},
        'Sale?': {'db_name': 'sale_ok', 'dtype': 'bool', 'non-null': True},
        'PoS?': {'db_name': 'available_in_pos', 'dtype': 'bool', 'non-null': True},
        'Purchase?': {'db_name': 'purchase_ok', 'dtype': 'bool', 'non-null': True},
        'Type': {'db_name': 'type', 'dtype': CategoricalDtype(categories=['product', 'service', 'consu']), 'non-null': True},
        'Category': {'db_name': 'categ_id', 'dtype': str, 'non-null': True},
        'PoS Category': {'db_name': 'pos_categ_id', 'dtype': str, 'non-null': True},
        'Track By Lot Number?': {'db_name': 'tracking', 'dtype': 'bool', 'non-null': True},
    }
    friendly_columns = list(friendly_columns_to_official.keys())
    column_to_dtypes = {key: value['dtype'] for key, value in friendly_columns_to_official.items()}
    column_renamer = {key: value['db_name'] for key, value in friendly_columns_to_official.items()}
    assert len(friendly_columns) == len(set(friendly_columns)), "Columns mismatch"


    def _get_category_id(self, categ_name):
        results = self.env['product.category'].search([('name', '=', categ_name)])
        if not results:
            raise ValidationError(f'Category "{categ_name}" does not exist')
        if len(results) > 1:
            raise ValidationError(f'There is more than one category called "{categ_name}"\nWhich one do you mean?')
        return results[0].id

    def _get_pos_category_id(self, categ_name):
        results = self.env['pos.category'].search([('name', '=', categ_name)])
        if not results:
            raise ValidationError(f'PoS Category "{categ_name}" does not exist')
        if len(results) > 1:
            raise ValidationError(f'There is more than one PoS category called "{categ_name}"\nWhich one do you mean?')
        return results[0].id


    def _is_code_unique_against_db(self, code: str, *, db_name):
        if not code: return
        if self.env['product.product'].search([
            (db_name, '=', code),
            ('active', '=', True),
            ])  or \
            self.env['product.product'].search([
                (db_name, '=', code),
                ('active', '=', False),
                ]):
            raise ValidationError(f'{db_name} "{code}" already exists')

    def _remove_invalid_chars(self, code: str, *, db_name):
        if not code: return code
        for charac in code:
            if not charac.isalnum() and not (charac in ALLOWED_CHARS_IN_BARCODES):
                raise ValidationError(f'{db_name} "{code}" contains invalid characters!')
        return code

    def _are_codes_unique_in_file(self, product_codes: pd.Series, *, db_name):
        codes_in_file = product_codes.dropna()
        if codes_in_file.nunique() != codes_in_file.shape[0]:
            raise ValidationError(f"There are duplicate {db_name}s in the file. Please check and try again")
        
    def parse_codes(self, codes: pd.Series, *, db_name):
        """Parses Both Barcodes & Internal References"""
        codes = codes.str.strip()
        codes.replace(np.NaN, None, inplace=True)
        codes.replace('', None, inplace=True)
        codes = codes.apply(self._remove_invalid_chars, db_name=db_name)
        self._are_codes_unique_in_file(codes, db_name=db_name)
        codes.apply(self._is_code_unique_against_db, db_name=db_name)
        return codes
        
    def _verify_and_process_sheet(self) -> pd.DataFrame:
        if not self.product_file:
            raise UserError('You need to select a file first!')
        file_data = base64.b64decode(self.product_file)
        try:
            df = pd.read_excel(file_data,
                               usecols=self.friendly_columns,
                               dtype=self.column_to_dtypes)
        except Exception as e:
            _logger.error(e)
            try:
                file_data = io.StringIO(file_data.decode("utf-8"))
                df = pd.read_csv(file_data,
                               usecols=self.friendly_columns,
                               dtype=self.column_to_dtypes)
            except Exception as oe:
                raise ValidationError(f"{e}\n{oe}")

        non_null_columns = [col for col, value in self.friendly_columns_to_official.items() if value.get('non-null')]
        if df[non_null_columns].isnull().sum().sum():
            raise ValidationError(f'These columns cannot have empty or invalid values:\n{non_null_columns}')

        df.loc[:, 'Name'] = df.Name.str.strip()
        df.loc[:, 'Barcode'] = self.parse_codes(df.Barcode, db_name='barcode')
        df.loc[:, 'Internal Reference'] = self.parse_codes(df['Internal Reference'], db_name='default_code')
        df.loc[:, 'Category'] = df.Category.apply(self._get_category_id)
        df.loc[:, 'PoS Category'] = df['PoS Category'].apply(self._get_pos_category_id)
        df.loc[:, 'Track By Lot Number?'] = df['Track By Lot Number?'].apply(lambda uselot: 'lot' if uselot else 'none')

        num_of_abnormalities = df[(df['Track By Lot Number?'] == 'lot') & (df['Type'] == 'service')].shape[0]
        if num_of_abnormalities:
            raise ValidationError("Products cannot be of type `Service` and `Tracked By Lot Number?` set as True at the same time")

        df.rename(self.column_renamer, axis=1, inplace=True)
        return df

    def import_product(self):
        df = self._verify_and_process_sheet()
        df.apply(self.create_product, axis=1)
        return

    def create_product(self, row):
        try:
            companies = self.env['res.company'].sudo().search([])
            sale_taxes = list(filter(lambda x: x, [r['account_sale_tax_id'] for r in companies]))
            sale_taxes_ids = [tax.id for tax in sale_taxes]
            row = row.to_dict()
            row['taxes_id'] = sale_taxes_ids
            self.env['product.product'].sudo().create(row)
        except Exception as e:
            _logger.error(e)
            raise ValidationError(e)
    
    
    def download_auto(self):
        return {
             'type' : 'ir.actions.act_url',
             'url': '/web/binary/download_product_upload_file?model=import.product.wizard&id=%s'%(self.id),
             'target': 'new',
             }
        
    def test(self):
        self._verify_and_process_sheet()