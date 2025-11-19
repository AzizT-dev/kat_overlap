# -*- coding: utf-8 -*-
"""
KAT Analysis – Theme Manager
Light/dark theme management

Author: Aziz T.
Copyright: (C) 2025 KaT - All rights reserved
License: GPLv3
Version: 1.0.0
"""


def get_light_style():
    """Returns light style"""
    return """
    QDialog {background-color: #f5f7fa;font-family: 'Segoe UI', Arial, sans-serif; color: #2c3e50;}
    QGroupBox {font-weight: bold; font-size: 12px;color: #2c3e50; border: 1px solid #e1e8ed; border-radius: 8px; margin-top: 10px; padding-top: 10px; background-color: white;}
    QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 8px 0 8px; color: #34495e;}
    QLabel {color: #2c3e50; font-size: 11px;font-weight: 500;}
    QComboBox {border: 1px solid #dcdfe6;border-radius: 6px; padding: 8px 12px;background-color: white; min-width: 150px;font-size: 11px;color: #2c3e50;}
    QComboBox:hover {border-color: #409eff;}
    QPushButton {background-color: #409eff;color: white;border: none;border-radius: 6px;
        padding: 10px 20px;font-weight: 600;font-size: 12px;min-height: 15px;}
    QPushButton:hover {background-color: #337ecc;}
    QPushButton:pressed {background-color: #2a6cb3;}
    QPushButton:disabled {background-color: #c0c4cc;color: #909399;}
    QPushButton#cancel_btn {background-color: #6c757d;}
    QPushButton#cancel_btn:hover {background-color: #5a6268;}
    QPushButton#export_btn {background-color: #28a745;}
    QPushButton#export_btn:hover {background-color: #218838;}
    QPushButton#zoom_btn {background-color: #ffc107;color: #212529;}
    QPushButton#zoom_btn:hover {background-color: #e0a800;}
    QPushButton#correct_btn {background-color: #17a2b8;}
    QPushButton#correct_btn:hover {background-color: #138496;}
    QTableWidget {border: 1px solid #e1e8ed;border-radius: 8px;background-color: white;gridline-color: #f0f0f0;font-size: 11px;color: #2c3e50;}
    QTableWidget::item {padding: 8px;border-bottom: 1px solid #f0f0f0;}
    QHeaderView::section {
        background-color: #f8f9fa;
        color: #2c3e50;
        font-weight: bold;
        border: none;
        padding: 12px 8px;
        font-size: 11px;
        border-bottom: 1px solid #e1e8ed;
    }
    QTextEdit {
        border: 1px solid #e1e8ed;
        border-radius: 6px;
        padding: 8px;
        background-color: white;
        font-size: 11px;
    }
    QProgressBar {
        border: 1px solid #e1e8ed;
        border-radius: 6px;
        text-align: center;
        background-color: white;
    }
    QProgressBar::chunk {
        background-color: #409eff;
        border-radius: 4px;
    }
    QCheckBox { spacing: 8px; }
    QCheckBox::indicator { width: 16px; height: 16px; }
    """


def get_dark_style():
    """Returns dark style"""
    return """
    QDialog {background-color: #1a1d23; font-family: 'Segoe UI', Arial, sans-serif; color: #e4e6eb;}
    QGroupBox {font-weight: bold; font-size: 12px; color: #e4e6eb; border: 1px solid #3a3f48;
        border-radius: 8px; margin-top: 10px; padding-top: 10px; background-color: #2d323b;}
    QGroupBox::title {subcontrol-origin: margin; left: 10px; padding: 0 8px 0 8px; color: #e4e6eb;}
    QLabel {color: #e4e6eb; font-size: 11px; font-weight: 500;}
    QComboBox {border: 1px solid #3a3f48; border-radius: 6px; padding: 8px 12px;
        background-color: #2d323b; min-width: 150px; font-size: 11px; color: #e4e6eb;}
    QComboBox:hover {border-color: #409eff;}
    QPushButton {background-color: #409eff; color: white; border: none; border-radius: 6px;
        padding: 10px 20px; font-weight: 600; font-size: 12px; min-height: 15px;}
    QPushButton:hover {background-color: #337ecc;}
    QPushButton:pressed {background-color: #2a6cb3;}
    QPushButton:disabled {background-color: #5a6268; color: #a0a4a8;}
    QPushButton#cancel_btn {background-color: #6c757d;}
    QPushButton#cancel_btn:hover {background-color: #5a6268;}
    QPushButton#export_btn {background-color: #28a745;}
    QPushButton#export_btn:hover {background-color: #218838;}
    QPushButton#zoom_btn {background-color: #ffc107; color: #212529;}
    QPushButton#zoom_btn:hover {background-color: #e0a800;}
    QPushButton#correct_btn {background-color: #17a2b8;}
    QPushButton#correct_btn:hover {background-color: #138496;}
    QTableWidget {border: 1px solid #3a3f48; border-radius: 8px; background-color: #2d323b;
        gridline-color: #3a3f48; font-size: 11px; color: #e4e6eb;}
    QTableWidget::item {padding: 8px; border-bottom: 1px solid #3a3f48;}
    QHeaderView::section {
        background-color: #343a46;
        color: #e4e6eb;
        font-weight: bold;
        border: none;
        padding: 12px 8px;
        font-size: 11px;
        border-bottom: 1px solid #3a3f48;
    }
    QTextEdit {
        border: 1px solid #3a3f48;
        border-radius: 6px;
        padding: 8px;
        background-color: #2d323b;
        font-size: 11px;
        color: #e4e6eb;
    }
    QProgressBar {
        border: 1px solid #3a3f48;
        border-radius: 6px;
        text-align: center;
        background-color: #2d323b;
    }
    QProgressBar::chunk {
        background-color: #409eff;
        border-radius: 4px;
    }
    QCheckBox { spacing: 8px; color: #e4e6eb; }
    QCheckBox::indicator { width: 16px; height: 16px; }
    """