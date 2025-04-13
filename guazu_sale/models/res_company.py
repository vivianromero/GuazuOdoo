# -*- coding: utf-8 -*-
""""
Created on 25/03/2019
@author: Vivian Romero
"""

from odoo import fields, models, api
#from odoo.tools import pycompat


class Company(models.Model):
    _inherit = "res.company"

    currency_sales_id = fields.Many2one('res.currency', string='Moneda para la venta', required=True, default=lambda self: self._get_user_currency())
