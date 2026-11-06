import os
from odoo import http


class ErpFrontend(http.Controller):

    @http.route('/erp-ui', type='http', auth='user')
    def index(self, **kw):
        path = os.path.join(os.path.dirname(__file__), '..', 'views', 'index.html')
        with open(path, encoding='utf-8') as f:
            return http.Response(f.read(), content_type='text/html; charset=utf-8')
