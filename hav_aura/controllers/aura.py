import json
import logging
from typing import List, Optional

from odoo import http
from odoo.tools import config
from requests import codes

_logger = logging.getLogger(__name__)

ODOO_CONFIG_TOKEN_KEY = 'hav_metadata_token'
DATABASE_EXPIRATION_REASON_KEY = 'database.expiration_date'
DATABASE_EXPIRATION_DATE_KEY = 'database.expiration_reason'


class AuraController(http.Controller):

    @http.route(['/hav/metadata'], type='http', auth="public")
    def get_metadata(self, api_key=None):
        token_check_code = self._verify_access_token(api_key)
        if token_check_code == 1:
            _logger.info('Aura metadata: Unauthorized')
            return http.Response(status=codes.unauthorized)
        if token_check_code == 2:
            _logger.warning('Aura metadata: Odoo Conf Token not configured')
            return http.Response(status=codes.not_found)
        if token_check_code != 0:
            _logger.warning('Aura metadata: Token validation code unknown')
            return

        data = self._build_json_data()
        return http.Response(json.dumps(data), headers=self._get_headers(), status=codes.ok)

    def _verify_access_token(self, http_access_token: str) -> int:
        """Verifies http access token against token configured in odoo conf

        Returns codes as int:
        0 - token is correct
        1 - token is not correct
        2 - metadata token in odoo conf is not configured
        """
        if not (odoo_conf_access_token := self._get_odoo_conf_access_token()):
            return 2

        return 0 if odoo_conf_access_token == http_access_token else 1

    @staticmethod
    def _get_odoo_conf_access_token():
        """Retrieves api token from odoo conf"""
        return config.get(ODOO_CONFIG_TOKEN_KEY)

    def _build_json_data(self) -> dict:
        """Prepares metadata dictionary"""
        data = {
            'user_count': self._get_user_count(),
            'installed_modules': self._get_installed_modules(),
        }
        if expiration_data := self._get_database_expiration():
            data.update(expiration_data)

        return data

    @staticmethod
    def _get_headers() -> dict:
        """Returns headers for json http response"""
        return {"Content-Type": "application/json"}

    @staticmethod
    def _get_user_count() -> int:
        """Returns number of active registered users in odoo system"""
        return http.request.env['res.users'].sudo().search_count([])

    @staticmethod
    def _get_installed_modules() -> List[str]:
        """Returns list of all installed modules"""
        return [
            module['name']
            for module
            in http.request.env['ir.module.module'].sudo().search_read([('state', '=', 'installed')], fields=['name'])
        ]

    def _get_database_expiration(self) -> Optional[dict]:
        """Returns dictionary with database expiration data based on database.expiration_date
        and database_expiration_reason system parameters. If not set - returns None"""
        expiration_reason = http.request.env['ir.config_parameter'].sudo().get_param(DATABASE_EXPIRATION_REASON_KEY)
        expiration_date = http.request.env['ir.config_parameter'].sudo().get_param(DATABASE_EXPIRATION_DATE_KEY)

        if expiration_reason and expiration_date:
            return {
                'expiration': {
                    'reason': expiration_reason,
                    'date': expiration_date
                }
            }
