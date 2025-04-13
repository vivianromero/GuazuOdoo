# -*- coding: utf-8 -*-
""""
Created on 25/04/2018
@author: Yerandy Reyes Fabregat
"""
from odoo import api, fields, models


class MrpPayrollWizard(models.TransientModel):
    _name = 'guazu.mrp.payroll.wizard'
    _description = 'Payroll Wizard'

    initial_date = fields.Date(string="Fecha inicial", required=True)
    final_date = fields.Date(string="Fecha final", required=True)
    group_by_workshop = fields.Boolean(string="Agrupar por áreas de producción", default=True)
    workshop_ids = fields.Many2many("guazu.mrp.workshop", string="Áreas de Producción")

    @api.multi
    def print_report_pdf(self):
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'guazu.mrp.payroll.report',
            'form': self.read()[0]
        }
        return self.env['report'].get_action(self, 'guazu_mrp.report_mrp_payroll', data=datas)
        # odoo 11
        # return self.env.ref('guazu_mrp.action_report_mrp_payroll').report_action([], data=datas)

    @api.multi
    def print_report_html(self):
        from json import JSONEncoder
        encoder = JSONEncoder()
        
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'guazu.mrp.payroll.report',
            'form': self.read()[0]
        }
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/html/%s/%s?options=%s' % ('guazu_mrp.report_mrp_payroll', self.id, encoder.encode(datas)),
        }