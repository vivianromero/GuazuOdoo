# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_location_id = fields.Many2one('guazu.stock.location', 'Ubicación de ventas por facturación')
    sale_warehouse_id = fields.Many2one('guazu.stock.location', 'Almacén de ventas por defecto')
    sale_warehouse_promocion_id = fields.Many2one('guazu.stock.location', 'Ubicación de ventas por promoción')
    sale_warehouse_consignacion_id = fields.Many2one('guazu.stock.location', 'Almacén de ventas por consignación')
    sale_warehouse_ferias_id = fields.Many2one('guazu.stock.location', 'Almacén de ventas por ferias')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res.update({'sale_location_id': int(self.env['ir.config_parameter'].get_param("guazu_sale.location_id")),
                    'sale_warehouse_id': int(self.env['ir.config_parameter'].get_param("guazu_sale.warehouse_id")),
                    'sale_warehouse_promocion_id': int(self.env['ir.config_parameter'].get_param("guazu_sale.warehouse_promocion_id")),
                    'sale_warehouse_consignacion_id': int(self.env['ir.config_parameter'].get_param("guazu_sale.warehouse_consignacion_id")),
                    'sale_warehouse_ferias_id': int(self.env['ir.config_parameter'].get_param("guazu_sale.warehouse_ferias_id"))
                    })
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param("guazu_sale.location_id", self.sale_location_id.id or '')
        self.env['ir.config_parameter'].set_param("guazu_sale.warehouse_id", self.sale_warehouse_id.id or '')
        self.env['ir.config_parameter'].set_param("guazu_sale.warehouse_promocion_id", self.sale_warehouse_promocion_id.id or '')
        self.env['ir.config_parameter'].set_param("guazu_sale.warehouse_consignacion_id", self.sale_warehouse_consignacion_id.id or '')
        self.env['ir.config_parameter'].set_param("guazu_sale.warehouse_ferias_id", self.sale_warehouse_ferias_id.id or '')
