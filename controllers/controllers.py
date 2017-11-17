# -*- coding: utf-8 -*-
from odoo import http,models, fields, api
from odoo.http import request

class Hqkpi(http.Controller):
    @http.route('/hq/kpi/', auth='public')
    def delete_data(self, *args,**kw):
        table = request.params['table']
        request.env.cr.execute("""delete from %s WHERE
        to_char(belong_date, 'YYYY-mm-DD') = to_char(now(), 'YYYY-mm-DD')""" % table)

