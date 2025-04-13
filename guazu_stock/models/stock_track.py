# -*- coding: utf-8 -*-
""""
Created on 15/10/2018
@author: Yerandy Reyes Fabregat
"""

from odoo import fields, models, api, exceptions, _

class StockTrack(models.Model):
    _name = "guazu.stock.track"

    name = fields.Char(size=256, string="Nombre", required=True)