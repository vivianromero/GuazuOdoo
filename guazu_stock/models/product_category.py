# -*- coding: utf-8 -*-
""""
Created on 11/07/2018
@author: Yerandy Reyes Fabregat
"""

from odoo import fields, models, api, exceptions, _


class ProductCategory(models.Model):
    _name = "product.category"
    _inherit = "product.category"
    _rec_name = 'complete_name'

    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)

    short_name = fields.Char(
        'Short Name', compute='_compute_short_name',
        store=True)

    @api.depends('name', 'parent_id.short_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.short_name, category.name)
            else:
                category.complete_name = category.name

    @api.depends('name', 'parent_id.short_name')
    def _compute_short_name(self):
        for category in self:
            if category.parent_id:
                category.short_name = '%s / %s' % (category.parent_id.short_name, category.name[0:3])
            else:
                category.short_name = category.name[0:3]
