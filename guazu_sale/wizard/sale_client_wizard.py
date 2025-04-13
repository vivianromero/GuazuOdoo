# -*- coding: utf-8 -*-
""""
Created on 28/05/2018
@author: Yerandy Reyes Fabregat
"""
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError, AccessError


class SaleClientWizard(models.TransientModel):
    _name = 'guazu.sale.client.wizard'
    _description = 'Client Wizard'

    name = fields.Char(string="Nombre",required=False)
    reup = fields.Char(string="Código REUP", required=False)
    client_org_ids = fields.Many2many("guazu.partner.org", "guazu_sale_client_org_rel", "wizard_id","id", string="Organismo", required=False)
    contrato = fields.Char(string="Número de Contrato", required=False)
    client_state_ids = fields.Many2many("res.country.state","partner_state_rel", "wizard_id","id",string="Provincia", required=False)
    active = fields.Boolean("Activos", default=True)
    noactive = fields.Boolean("No Activos", default=False)
    date1 = fields.Date("Fecha inicial")
    date2 = fields.Date("Fecha final")
    order_by = fields.Selection(
        [('name', 'Nombre'),
         ('organismo', 'Organismo'),
         ('expire_contract_date', 'Vencimiento del Contrato'),
         ],
        default='name')

    @api.multi
    def print_report_pdf(self):
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'guazu.sale.client.report',
            'form': self.read()[0]
        }
        return self.env['report'].get_action(self, 'guazu_sale.report_sale_client', data=datas)
        # odoo 11
        # return self.env.ref('guazu_stock.action_report_stock_existence').report_action([], data=datas)
    
    @api.multi
    def print_report_html(self):
        from json import JSONEncoder
        encoder = JSONEncoder()
        
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])

        datas = {
            'ids': active_ids,
            'model': 'guazu.sale.client.report',
            'form': self.read()[0],
        }
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/html/%s/%s?options=%s' % ('guazu_sale.report_sale_client', self.id, encoder.encode(datas)),
        }