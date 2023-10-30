from requests import codes
from unittest.mock import patch
from datetime import datetime
from odoo.tests.common import HttpCase

from ..controllers.aura import AuraController, DATABASE_EXPIRATION_REASON_KEY, DATABASE_EXPIRATION_DATE_KEY

class TestAuraMetadataEndpoint(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.valid_key = 'valid_api_key_token'
        cls.route = '/hav/metadata?api_key={}'
        cls.number_of_users = cls.env['res.users'].search_count([])
        cls.number_of_installed_modules = cls.env['ir.module.module'].search_count([('state', '=', 'installed')])
        cls.expiration_date = datetime.now().date()
        cls.expiration_reason = 'this is good reason'

    def prepare_database_params(self, should_exists=False):
        """Makes sure that database system parameters are prepared / removed"""
        IrConfigParameter = self.env['ir.config_parameter']
        date = IrConfigParameter.search([('key', '=', DATABASE_EXPIRATION_DATE_KEY)])
        reason = IrConfigParameter.search([('key', '=', DATABASE_EXPIRATION_REASON_KEY)])

        if should_exists:
            create_vals = []

            if not date:
                create_vals.append({'key': DATABASE_EXPIRATION_DATE_KEY, 'value': self.expiration_date})
            else:
                date.write({'value': self.expiration_date})

            if not reason:
                create_vals.append({'key': DATABASE_EXPIRATION_REASON_KEY, 'value': self.expiration_reason})
            else:
                reason.write({'value': self.expiration_reason})

            if create_vals:
                IrConfigParameter.create(create_vals)
        else:
            if date:
                date.unlink()
            if reason:
                reason.unlink()

    def test_authentication_odoo_conf_key_not_set(self):
        """Test whether response with code 'not found' is returned when api key is not configured in odoo.conf"""
        with patch.object(AuraController, '_get_odoo_conf_access_token', return_value=None):
            response = self.url_open(self.route.format(self.valid_key))

        self.assertEqual(response.status_code, codes.not_found, "Expected 'not found' status code")

    def test_authentication_api_key_not_correct(self):
        """Test whether response with code 'unauthorized' is returned when api key is not correct"""
        with patch.object(AuraController, '_get_odoo_conf_access_token', return_value=self.valid_key):
            response = self.url_open(self.route.format('not_valid_api_key'))

        self.assertEqual(response.status_code, codes.unauthorized, "Expected 'unauthorized' status code")

    def test_payload_without_database_expiration(self):
        """Test whether after successful authentication correct payload is returned - without database system parameters
        set"""
        self.prepare_database_params(should_exists=False)

        with patch.object(AuraController, '_get_odoo_conf_access_token', return_value=self.valid_key):
            response = self.url_open(self.route.format(self.valid_key))

        self.assertEqual(response.status_code, codes.ok, 'Expected "ok" status code')
        response_data = response.json()

        self.assertTrue('user_count' in response_data, 'Expected "user_count" key in response data')
        self.assertEqual(response_data.get('user_count'), self.number_of_users)

        self.assertTrue('installed_modules' in response_data, 'Expected "installed_modules" key in response data')
        self.assertEqual(len(response_data.get('installed_modules', 0)), self.number_of_installed_modules)

        self.assertFalse('expiration' in response_data, '"expiration" key should not be present in response data')

    def test_payload_with_database_expiration(self):
        """Test whether after successful authentication correct payload is returned - with database system parameters
        set"""
        self.prepare_database_params(should_exists=True)
        with patch.object(AuraController, '_get_odoo_conf_access_token', return_value=self.valid_key):
            response = self.url_open(self.route.format(self.valid_key))

        self.assertEqual(response.status_code, codes.ok, 'Expected "ok" status code')
        response_data = response.json()

        self.assertTrue('user_count' in response_data, 'Expected "user_count" key in response data')
        self.assertEqual(response_data.get('user_count'), self.number_of_users)

        self.assertTrue('installed_modules' in response_data, 'Expected "installed_modules" key in response data')
        self.assertEqual(len(response_data.get('installed_modules', 0)), self.number_of_installed_modules)

        self.assertTrue('expiration' in response_data, 'Expected "expiration" key in response data')
        self.assertTrue('reason' in response_data['expiration'])
        self.assertEqual(response_data['expiration']['reason'], self.expiration_reason)
        self.assertTrue('date' in response_data['expiration'])
        self.assertEqual(response_data['expiration']['date'], str(self.expiration_date))
