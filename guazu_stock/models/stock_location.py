# -*- coding: utf-8 -*-
""""
Created on 25/04/2018
@author: Yerandy Reyes Fabregat
"""

from odoo import fields, models, api


class StockLocation(models.Model):
    _name = "guazu.stock.location"

    code = fields.Char('Código', size=64, required=True)
    name = fields.Char('Nombre', size=300, required=True)
    type = fields.Selection([('storage', 'Almacenamiento'), ('production', 'Producción'), ('external', 'Externa'),('workshop','Taller')],
                            default='storage', required=True, string="Tipo")
    address = fields.Char('Dirección')
    _sql_constraints = [('code_uniq', 'unique (code)', "El código de la ubicación debe ser único."),
                        ('name_uniq', 'unique (name)', "El nombre de la ubicación debe ser único."),]

    @api.onchange("type")
    def onchange_type(self):
        if self.type == 'storage':
            pass

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        records = self.browse()

        if name and operator in ['=', 'ilike']:
            records = self.search([('code', '=', name)] + args, limit=limit)

        if not records:
            records = self.search([('name', operator, name)] + args, limit=limit)

        return records.name_get()

    _sql_constraints = [('name_uniq_location', 'unique(name)', 'El nombre debe ser único')]


