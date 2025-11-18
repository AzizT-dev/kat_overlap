# -*- coding: utf-8 -*-
"""
KAT Overlap Plugin
"""

def classFactory(iface):
    from .kat_overlap import KATOverlap
    return KATOverlap(iface)