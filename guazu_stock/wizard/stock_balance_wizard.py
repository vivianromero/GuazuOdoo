# -*- coding: utf-8 -*-
""""
Created on 09/11/2018
@author: Yerandy Reyes Fabregat
"""
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError, AccessError


class StockBalanceWizard(models.TransientModel):
    _name = 'guazu.stock.balance.wizard'
    _description = 'Balance Wizard'

    start_date = fields.Date("Fecha inicial")
    end_date = fields.Date("Fecha final")
    category_ids = fields.Many2many("product.category", "guazu_stock_balance_category_rel", "wizard_id",
                                    "category_id", string="Categorías", required=False)
    location_ids = fields.Many2many("guazu.stock.location", "guazu_stock_balance_location_rel", "wizard_id", "location_id", string="Ubicaciones", domain=[('type', '=', 'storage')], required=False)
    attribute_value_ids = fields.Many2many("product.attribute.value", "guazu_stock_balance_attribute_rel","wizard_id","value_id", string="Atributos", required=False)
    product_color_ids = fields.Many2many("guazu.product.color", "guazu_stock_balance_color_rel", "wizard_id",
                                         "id", string="Colores", required=False)
    product_sex_ids = fields.Many2many("guazu.product.sex", "guazu_stock_balance_sex_rel", "wizard_id",
                                       "id", string="Sexos", required=False)
    product_material_ids = fields.Many2many("guazu.product.material", "guazu_stock_balance_material_rel",
                                            "wizard_id",
                                            "id", string="Materiales", required=False)
    product_template_ids = fields.Many2many("product.template", "guazu_stock_balance_product_template_rel",
                                            "wizard_id",
                                            "id", string="Productos", required=False)
    show_variants = fields.Boolean("Mostrar todas las variantes", default=False)
    # show_import = fields.Boolean("Mostrar importes", default=False)

    @api.multi  # peuds susarlo con api one o con api multi en dependencia con api one no tienes que recorrer los grupos y con api multi si
    def busco_acc_precio(self):  # puedes usarlo en el write o un metodo auxiliar
        user = self.env['res.users'].search([('id', '=', self.env.user.id)])  # usuario loggeado
        resul = False
        for group in user.groups_id:
            group_name = group.name
            if group_name == 'Existencia Visor':
                resul = True
        return resul

    @api.multi  # peuds susarlo con api one o con api multi en dependencia con api one no tienes que recorrer los grupos y con api multi si
    def ventas_location(self):  # puedes usarlo en el write o un metodo auxiliar
        return  self.env["ir.config_parameter"].sudo().get_param('guazu_sale.warehouse_id')

    @api.multi
    def valida_datos(self):
        id_ventas = self.ventas_location()
        if not id_ventas:
            raise UserError(_('No se ha definido el almacén por defecto para las ventas'))

        if not int(id_ventas) in self.read()[0]['location_ids']:
            raise UserError(_('Usted tiene acceso sólo a la información del almacén de ventas'))
        return True
		
    @api.multi
    def print_report_pdf(self):
        access_price = self.busco_acc_precio()
        if not access_price:
            self.valida_datos()
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'guazu.stock.balance.report',
            'form': self.read()[0],
            'access_price':access_price
        }
        return self.env['report'].get_action(self, 'guazu_stock.report_stock_balance', data=datas)
        # odoo 11
        # return self.env.ref('guazu_stock.action_report_stock_balance').report_action([], data=datas)
    
    @api.multi
    def print_report_html(self):
        access_price = self.busco_acc_precio()
        if not access_price:
            self.valida_datos()
			
        from json import JSONEncoder
        encoder = JSONEncoder()
        
        self.ensure_one()
        active_ids = self.env.context.get('active_ids', [])
        datas = {
            'ids': active_ids,
            'model': 'guazu.stock.balance.report',
            'form': self.read()[0],
            'access_price':access_price
        }
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': '/report/html/%s/%s?options=%s' % ('guazu_stock.report_stock_balance', self.id, encoder.encode(datas)),
        }