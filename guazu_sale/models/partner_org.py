# -*- coding: utf-8 -*-
""""
Created on 12/07/2018
@author: Yerandy Reyes Fabregat
"""

from odoo import fields, models, api, exceptions, _

class PartnerOrg(models.Model):
    _name = "guazu.partner.org"

    name = fields.Char(size=256, string="Organismo", required=True)
