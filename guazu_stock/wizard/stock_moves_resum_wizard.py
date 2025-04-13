# -*- coding: utf-8 -*-
""""
Created on 29/10/2018
@author: Yerandy Reyes Fabregat
"""
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError, AccessError


class StockMovesResumWizard(models.TransientModel):
    _name = 'guazu.stock.moves.resum.wizard'
    _description = 'Moves Resumen Wizard'

    group_by = fields.Selection([('sex', 'Sexo'), ('categ', 'Categoría de los Productos')],default='categ',string="Agrupar por")
    start_date = fields.Date("Fecha inicial")
    end_date = fields.Date("Fecha final")
    category_ids = fields.Many2many("product.category", "guazu_stock_moves_resum_category_rel", "wizard_id", "category_id", string="Categorías",  required=False)
    location_ids = fields.Many2many("guazu.stock.location", "guazu_stock_moves_resum_location_rel", "wizard_id", "location_id", string="Ubicación", domain=[('type', '=', 'storage')],required=True)
    product_sex_ids = fields.Many2many("guazu.product.sex", "guazu_stock_moves_resum_sex_rel", "wizard_id","id", string="Sexos", required=False)


    @api.multi
    def print_report_pdf(self):
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'guazu.stock.moves.resum.report',
            'form': self.read()[0],
        }
        return self.env['report'].get_action(self, 'guazu_stock.report_stock_moves_resum', data=datas)
        # odoo 11
        # return self.env.ref('guazu_stock.action_report_stock_moves_resum').report_action([], data=datas)

    @api.multi
    def print_report_html(self):
        from json import JSONEncoder
        encoder = JSONEncoder()
        
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'guazu.stock.moves.resum.report',
            'form': self.read()[0],
            # 'access_price':access_price
        }
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/html/%s/%s?options=%s' % ('guazu_stock.report_stock_moves_resum', self.id, encoder.encode(datas)),
        }