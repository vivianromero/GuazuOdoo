# -*- coding: utf-8 -*-
{
    'name': 'Cobros',
    'version': '0.1',
    'category': 'Guazu',
    "sequence": 2,
    'complexity': "easy",
    'description': """

    """,
    'author': "Yerandy Reyes & Vivian Romero",
    'website': '',
    'depends': ["guazu_sale"],
    'init_xml': [],
    'data': [
        
        "security/payment_security.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
		"views/filial_view.xml",
        "views/payment_views.xml",
		
    ],
    'demo_xml': [],
    'test': [
    ],
    'installable': True,
    #'auto_install': False,
    'application': True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
