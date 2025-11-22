# -*- coding: utf-8 -*-
"""
KAT Overlap Analysis Plugin
Main plugin initialization

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""

def classFactory(iface):
    """Load KATOverlap class from kat_overlap module"""
    from .kat_overlap import KATOverlap
    return KATOverlap(iface)