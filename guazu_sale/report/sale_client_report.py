# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, exceptions,  _
from odoo.tools import float_utils
from odoo.exceptions import UserError, AccessError,ValidationError

class SaleClientReport(models.AbstractModel):
    _name = 'report.guazu_sale.report_sale_client'

    @api.model
    def get_lines(self,name,reup,client_org_ids,client_state_ids,date1,date2,active,noactive,contrato,order_by):
        res = []

        order = """ order by res_partner."""+order_by+""",res_partner.name """
        if order_by == 'organismo':
            order = """ order by """ + order_by+""",res_partner.name """

        where = " where customer=TRUE"

        if date1 and not date2:
            where += """ and (res_partner.expire_contract_date) >= '"""+date1+"""'"""

        if not date1 and date2:
            where += """ and (res_partner.expire_contract_date) <= '"""+date2+"""'"""

        if date1 and date2:
            where += """ and (res_partner.expire_contract_date BETWEEN '""" + date1 + """' AND '""" + date2 + """')"""


        if len(client_org_ids) > 1:
            where += " and org.id in " + str(tuple(client_org_ids))
        if len(client_org_ids) == 1:
            where += " and org.id = " + str(client_org_ids[0])

        if len(client_state_ids) > 1:
            where += " and state.id in " + str(tuple(client_state_ids))
        if len(client_state_ids) == 1:
            where += " and state.id = " + str(client_state_ids[0])

        if active and not noactive:
            where += " and res_partner.active = TRUE"

        if not active and noactive:
            where += " and res_partner.active = FALSE"


        if name:
            where += """ and res_partner.name like '%"""+name+"""%'"""

        if reup:
            where += """ and res_partner.reup like '%"""+reup+"""%'"""

        if contrato:
            where += """ and res_partner.number_contract like '%"""+contrato+"""%'"""

        self.env.cr.execute(""" select res_partner.name,res_partner.reup,res_partner.number_contract, res_partner.expire_contract_date,
                                                org.name as organismo,state.name as state
                                             from res_partner res_partner
                                              LEFT JOIN guazu_partner_org org ON (res_partner.org_id=org.id)
                                              LEFT JOIN res_country_state state ON (res_partner.state_id=state.id)
                                              """+where+order)
        data = self.env.cr.dictfetchall()
        clientes = []
        for d in data:
            clientes.append({
                'name': d['name'],
                'reup': d['reup'],
                'organismo':d['organismo'],
                'state': d['state'],
                'number_contract': d['number_contract'],
                'expire_contract_date': d['expire_contract_date']
            })
            # if existence:
        res.append({'clientes': clientes})
        return res


    @api.model
    def get_orgs(self, client_org_ids):
        if not client_org_ids:
            return ['Todos los Organismos']

        orgs = self.env["guazu.partner.org"].search([('id', 'in', client_org_ids)])
        res = []
        for org in orgs:
            res.append(org.name_get()[0][1])

        return res

    @api.model
    def get_states(self, client_state_ids):
        if not client_state_ids:
            return ['Todas las Provincias']

        states = self.env["res.country.state"].search([('id', 'in', client_state_ids)])
        res = []
        for state in states:
            res.append(state.name_get()[0][1])
        return res

    @api.model
    def render_html(self, docids, data=None):
        name = data['form']['name']
        reup = data['form']['reup']
        client_org_ids = data['form']['client_org_ids']
        contrato = data['form']['contrato']
        client_state_ids = data['form']['client_state_ids']
        date1 = data['form']['date1']
        date2 = data['form']['date2']
        active = data['form']['active']
        noactive = data['form']['noactive']
        contrato = data['form']['contrato']
        order_by = data['form']['order_by']

        docargs = {
            'data': data,
            'name': name,
            'reup':reup,
            'orgs': self.get_orgs(client_org_ids),
            'contrato': contrato,
            'states': self.get_states(client_state_ids),
            'date1': date1,
            'date2': date2,
            'active':active,
            'noactive':noactive,
            'contrato': contrato,
            'order_by': order_by,
            'lines': self.get_lines(name,reup,client_org_ids,client_state_ids,date1,date2,active,noactive,contrato,order_by)
        }
        return self.env['report'].render('guazu_sale.report_sale_client', values=docargs)