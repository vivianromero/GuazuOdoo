# -*- coding: utf-8 -*-
""""
Created on 12/07/2018
@author: Yerandy Reyes Fabregat
"""

from odoo import fields, models, api, exceptions, _

class ProductSex(models.Model):
    _name = "guazu.product.sex"

    name = fields.Char(size=256, string="Nombre", required=True)
    image = fields.Binary(string="Ícono")
    
