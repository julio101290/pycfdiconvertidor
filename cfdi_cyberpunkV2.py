#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CFDI 4.0 XML -> PDF
Interfaz Cyberpunk Retro + arrastrar y soltar archivos XML.

Instalación:
    pip install -r requirements.txt

Ejecutar:
    python cfdi_cyberpunk.py

El arrastrar y soltar utiliza tkinterdnd2. Si no está instalado, la aplicación
sigue funcionando mediante el botón "Agregar XML".
"""

import os
import re
import sys
import io
import platform
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False
    TkinterDnD = None

import qrcode
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, KeepTogether
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


# ---------------------------------------------------------------------------
# Configuración visual
# ---------------------------------------------------------------------------
APP_BG = "#090D1A"
PANEL_BG = "#111A2E"
PANEL_ALT = "#17243B"
CYAN = "#35F2F2"
MAGENTA = "#FF3CAC"
PURPLE = "#9B5DE5"
TEXT = "#E8F7FF"
MUTED = "#91A8BD"
GREEN = "#43F5A5"
RED = "#FF5577"

DESTINO = ""
LOGO_PATH = ""
archivos = []


# ---------------------------------------------------------------------------
# Utilidades CFDI
# ---------------------------------------------------------------------------
def local_name(tag):
    """Obtiene el nombre local de una etiqueta XML, sin namespace."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def child(element, name):
    if element is None:
        return None
    for item in list(element):
        if local_name(item.tag) == name:
            return item
    return None


def children(element, name):
    if element is None:
        return []
    return [item for item in list(element) if local_name(item.tag) == name]


def descendants(element, name):
    if element is None:
        return []
    return [item for item in element.iter() if local_name(item.tag) == name]


def attr(element, key, default=""):
    return element.attrib.get(key, default) if element is not None else default


def money(value):
    try:
        return f"${Decimal(str(value or '0')):,.2f}"
    except (InvalidOperation, ValueError):
        return str(value or "")


def safe_filename(value):
    value = re.sub(r'[\\/:*?"<>|]+', "_", value)
    return value.strip(" .") or "CFDI"


def parse_cfdi(xml_path):
    """Lee CFDI 4.0 sin depender de un prefijo de namespace específico."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        if local_name(root.tag) != "Comprobante":
            raise ValueError("El XML no parece ser un CFDI: no se encontró Comprobante.")

        emisor = child(root, "Emisor")
        receptor = child(root, "Receptor")
        complemento = child(root, "Complemento")
        timbre = next(
            (node for node in descendants(complemento, "TimbreFiscalDigital")),
            None
        )

        conceptos_node = child(root, "Conceptos")
        conceptos = []
        for concepto in children(conceptos_node, "Concepto"):
            impuestos_node = child(concepto, "Impuestos")
            traslados = []
            retenciones = []

            for traslado in descendants(child(impuestos_node, "Traslados"), "Traslado"):
                traslados.append(dict(traslado.attrib))
            for retencion in descendants(child(impuestos_node, "Retenciones"), "Retencion"):
                retenciones.append(dict(retencion.attrib))

            conceptos.append({
                "attrs": dict(concepto.attrib),
                "traslados": traslados,
                "retenciones": retenciones,
            })

        impuestos = child(root, "Impuestos")
        traslados_globales = [
            dict(x.attrib) for x in descendants(child(impuestos, "Traslados"), "Traslado")
        ]
        retenciones_globales = [
            dict(x.attrib) for x in descendants(child(impuestos, "Retenciones"), "Retencion")
        ]

        return {
            "Comprobante": dict(root.attrib),
            "Emisor": dict(emisor.attrib) if emisor is not None else {},
            "Receptor": dict(receptor.attrib) if receptor is not None else {},
            "Conceptos": conceptos,
            "Timbre": dict(timbre.attrib) if timbre is not None else {},
            "Impuestos": {
                "attrs": dict(impuestos.attrib) if impuestos is not None else {},
                "traslados": traslados_globales,
                "retenciones": retenciones_globales,
            },
            "Archivo": str(xml_path),
        }
    except ET.ParseError as exc:
        return {"error": f"XML inválido: {exc}"}
    except Exception as exc:
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Generación PDF
# ---------------------------------------------------------------------------
def build_pdf_styles():
    base = getSampleStyleSheet()
    return {
        "normal": ParagraphStyle(
            "CFDINormal", parent=base["Normal"], fontName="Helvetica",
            fontSize=7.1, leading=9, textColor=colors.HexColor("#20242B"),
            spaceAfter=1
        ),
        "small": ParagraphStyle(
            "CFDISmall", parent=base["Normal"], fontName="Helvetica",
            fontSize=6.1, leading=7.5, textColor=colors.HexColor("#20242B"),
            wordWrap="CJK"
        ),
        "tiny": ParagraphStyle(
            "CFDITiny", parent=base["Normal"], fontName="Helvetica",
            fontSize=5.4, leading=6.5, textColor=colors.HexColor("#20242B"),
            wordWrap="CJK"
        ),
        "white_center": ParagraphStyle(
            "CFDIWhiteCenter", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=8, leading=10, alignment=TA_CENTER,
            textColor=colors.white
        ),
        "section": ParagraphStyle(
            "CFDISection", parent=base["Normal"], fontName="Helvetica-Bold",
            fontSize=8, leading=10, textColor=colors.white
        ),
        "right": ParagraphStyle(
            "CFDIRight", parent=base["Normal"], fontName="Helvetica",
            fontSize=7, leading=9, alignment=TA_RIGHT
        ),
        "center": ParagraphStyle(
            "CFDICenter", parent=base["Normal"], fontName="Helvetica",
            fontSize=7, leading=9, alignment=TA_CENTER
        ),
    }


def p(text, style):
    text = str(text if text is not None else "")
    # Escapar contenido XML/HTML para Paragraph.
    from xml.sax.saxutils import escape
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def section_bar(title, width):
    t = Table([[p(title, build_pdf_styles()["section"])]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#30343B")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#30343B")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def field_lines(data, labels=None):
    """Convierte atributos en líneas legibles, omitiendo campos vacíos."""
    labels = labels or {}
    result = []
    for key, value in data.items():
        if value is None or str(value).strip() == "":
            continue
        result.append(f"<b>{labels.get(key, key)}:</b> {value}")
    return result


def sat_verification_url(datos):
    comp = datos.get("Comprobante", {})
    emisor = datos.get("Emisor", {})
    receptor = datos.get("Receptor", {})
    timbre = datos.get("Timbre", {})
    uuid = timbre.get("UUID", "")
    total = comp.get("Total", "")
    sello = timbre.get("SelloCFD", "")
    fe = sello[-8:] if sello else ""
    params = {
        "id": uuid,
        "re": emisor.get("Rfc", ""),
        "rr": receptor.get("Rfc", ""),
        "tt": total,
        "fe": fe,
    }
    return "https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx?" + urlencode(params)


def generar_pdf(datos, salida_pdf, logotipo_path=None):
    styles = build_pdf_styles()
    page_w, page_h = letter
    margin = 11 * mm
    usable_w = page_w - 2 * margin

    doc = SimpleDocTemplate(
        salida_pdf, pagesize=letter,
        rightMargin=margin, leftMargin=margin,
        topMargin=9 * mm, bottomMargin=17 * mm,
        title=f"CFDI {datos.get('Timbre', {}).get('UUID', '')}",
        author="Convertidor CFDI Cyberpunk"
    )
    story = []

    comp = datos.get("Comprobante", {})
    emisor = datos.get("Emisor", {})
    receptor = datos.get("Receptor", {})
    timbre = datos.get("Timbre", {})
    uuid = timbre.get("UUID", "UUID no disponible")

    # Encabezado: QR y resumen del comprobante.
    qr_buffer = io.BytesIO()
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=5, border=2)
    qr.add_data(sat_verification_url(datos))
    qr.make(fit=True)
    qr.make_image(fill_color="black", back_color="white").save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_img = RLImage(qr_buffer, width=35*mm, height=35*mm)

    tipo_codigo = comp.get("TipoDeComprobante", "")
    tipo_nombre = {"I": "Ingreso", "E": "Egreso", "T": "Traslado", "N": "Nómina", "P": "Pago"}.get(tipo_codigo, "")
    metadata = [
        f"Tipo: {tipo_codigo} - {tipo_nombre}" if tipo_nombre else f"Tipo: {tipo_codigo}",
        f"Serie: {comp.get('Serie', '')}     Folio: {comp.get('Folio', '')}",
        f"Lugar de expedición: {comp.get('LugarExpedicion', '')}",
        f"Fecha: {comp.get('Fecha', '')}",
        f"Forma de pago: {comp.get('FormaPago', '')}",
        f"Método de pago: {comp.get('MetodoPago', '')}",
        f"Condiciones de pago: {comp.get('CondicionesDePago', '')}",
        f"Certificado emisor: {comp.get('NoCertificado', '')}",
        f"Certificado SAT: {timbre.get('NoCertificadoSAT', '')}",
        f"RFC proveedor: {timbre.get('RfcProvCertif', '')}",
        f"Fecha de certificación: {timbre.get('FechaTimbrado', '')}",
        f"Exportación: {comp.get('Exportacion', '')}",
    ]
    from xml.sax.saxutils import escape
    meta_text = "<br/>".join(escape(line) for line in metadata)
    meta_para = Paragraph(meta_text, ParagraphStyle(
        "meta", parent=styles["center"], fontSize=6.7, leading=8.2
    ))

    header = Table([[qr_img, meta_para]], colWidths=[40*mm, usable_w-40*mm])
    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#555555")),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(Table([[p(f"UUID: {uuid}", styles["white_center"])]], colWidths=[usable_w],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#30343B")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])))
    story.append(header)
    story.append(Spacer(1, 3))

    # Logotipo opcional, pequeño y sin desplazar el contenido.
    if logotipo_path and os.path.isfile(logotipo_path):
        try:
            logo = ImageReader(logotipo_path)
            iw, ih = logo.getSize()
            maxw, maxh = 30*mm, 14*mm
            scale = min(maxw/iw, maxh/ih)
            logo_flow = RLImage(logotipo_path, width=iw*scale, height=ih*scale)
            story.extend([logo_flow, Spacer(1, 2)])
        except Exception:
            pass

    # Emisor y receptor.
    for title, data, order in [
        ("Emisor", emisor, ["Nombre", "Rfc", "RegimenFiscal", "FacAtrAdquirente"]),
        ("Receptor", receptor, ["Nombre", "Rfc", "UsoCFDI", "DomicilioFiscalReceptor", "RegimenFiscalReceptor"]),
    ]:
        story.append(section_bar(title, usable_w))
        lines = []
        for key in order:
            if data.get(key):
                lines.append(f"<b>{key}:</b> {data[key]}")
        for key, value in data.items():
            if key not in order and value:
                lines.append(f"<b>{key}:</b> {value}")
        story.append(Table([[Paragraph("<br/>".join(lines) or "Sin información", styles["normal"])]],
            colWidths=[usable_w], style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#777777")),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])))
        story.append(Spacer(1, 3))

    # Conceptos, una fila por concepto.
    conceptos = datos.get("Conceptos", [])
    story.append(section_bar(f"Conceptos: {len(conceptos)}", usable_w))
    concept_rows = [[
        p("Cant.", styles["white_center"]), p("Clave SAT / Unidad", styles["white_center"]),
        p("Descripción", styles["white_center"]), p("Valor unitario", styles["white_center"]),
        p("Importe", styles["white_center"])
    ]]
    for item in conceptos:
        a = item["attrs"]
        descripcion = a.get("Descripcion", "")
        extras = []
        if a.get("NoIdentificacion"):
            extras.append("No identificación: " + a["NoIdentificacion"])
        if a.get("ObjetoImp"):
            extras.append("Objeto impuesto: " + a["ObjetoImp"])
        from xml.sax.saxutils import escape
        desc = escape(descripcion) + (("<br/><font size='5'>" + escape(" | ".join(extras)) + "</font>") if extras else "")
        concept_rows.append([
            p(a.get("Cantidad", ""), styles["small"]),
            p(f"{a.get('ClaveProdServ', '')} / {a.get('ClaveUnidad', '')} {a.get('Unidad', '')}", styles["small"]),
            Paragraph(desc, styles["small"]),
            p(money(a.get("ValorUnitario", "")), styles["small"]),
            p(money(a.get("Importe", "")), styles["small"]),
        ])
    concept_table = Table(concept_rows, colWidths=[
        13*mm, 29*mm, usable_w-13*mm-29*mm-23*mm-23*mm, 23*mm, 23*mm
    ], repeatRows=1)
    concept_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#30343B")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#777777")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (1, -1), "CENTER"),
        ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(concept_table)
    story.append(Spacer(1, 3))

    # Impuestos trasladados y retenidos.
    imp = datos.get("Impuestos", {})
    tax_rows = [[
        p("Tipo", styles["white_center"]), p("Base", styles["white_center"]),
        p("Impuesto", styles["white_center"]), p("Factor", styles["white_center"]),
        p("Tasa o cuota", styles["white_center"]), p("Importe", styles["white_center"])
    ]]
    for tipo, key in [("Traslado", "traslados"), ("Retención", "retenciones")]:
        for tax in imp.get(key, []):
            tax_rows.append([
                p(tipo, styles["small"]), p(money(tax.get("Base")), styles["small"]),
                p(tax.get("Impuesto", ""), styles["small"]),
                p(tax.get("TipoFactor", ""), styles["small"]),
                p(tax.get("TasaOCuota", ""), styles["small"]),
                p(money(tax.get("Importe")), styles["small"]),
            ])
    if len(tax_rows) > 1:
        story.append(section_bar("Impuestos", usable_w))
        tax_table = Table(tax_rows, colWidths=[22*mm, 25*mm, 27*mm, 25*mm, 34*mm, usable_w-133*mm], repeatRows=1)
        tax_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#30343B")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#777777")),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(tax_table)
        story.append(Spacer(1, 3))

    # Totales.
    story.append(section_bar("Totales", usable_w))
    total_data = [[
        p("Moneda", styles["center"]), p("Tipo de cambio", styles["center"]),
        p("Subtotal", styles["center"]), p("Descuento", styles["center"]),
        p("Impuestos trasladados", styles["center"]), p("Impuestos retenidos", styles["center"]),
        p("Total", styles["center"])
    ], [
        p(comp.get("Moneda", ""), styles["center"]),
        p(comp.get("TipoCambio", "1"), styles["center"]),
        p(money(comp.get("SubTotal")), styles["center"]),
        p(money(comp.get("Descuento", "0")), styles["center"]),
        p(money(imp.get("attrs", {}).get("TotalImpuestosTrasladados", "0")), styles["center"]),
        p(money(imp.get("attrs", {}).get("TotalImpuestosRetenidos", "0")), styles["center"]),
        p(money(comp.get("Total")), styles["center"]),
    ]]
    widths = [18*mm, 23*mm, 25*mm, 22*mm, 31*mm, 29*mm, usable_w-148*mm]
    totals_table = Table(total_data, colWidths=widths)
    totals_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E7E9EC")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#777777")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 3))

    # Información fiscal: sellos y cadena original.
    story.append(section_bar("Datos fiscales", usable_w))
    fiscal_parts = []
    cadena_tfd = timbre.get("CadenaOriginal", "")
    if not cadena_tfd and timbre:
        # Cadena original del complemento TimbreFiscalDigital 1.1.
        cadena_tfd = "||1.1|{}|{}|{}|{}|{}||".format(
            timbre.get("UUID", ""), timbre.get("FechaTimbrado", ""),
            timbre.get("RfcProvCertif", ""), timbre.get("SelloCFD", ""),
            timbre.get("NoCertificadoSAT", "")
        )
    for label, value in [
        ("Sello CFDI", timbre.get("SelloCFD", "")),
        ("Sello SAT", timbre.get("SelloSAT", "")),
        ("Cadena TFD", cadena_tfd),
    ]:
        if value:
            fiscal_parts.append(Paragraph(f"<b>{label}:</b> {value}", styles["tiny"]))
    if not fiscal_parts:
        fiscal_parts.append(p("No se encontró información del Timbre Fiscal Digital.", styles["small"]))
    fiscal_table = Table([[fiscal_parts]], colWidths=[usable_w])
    fiscal_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#777777")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(fiscal_table)

    verify = sat_verification_url(datos)
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        f"<b>Verificación SAT:</b> <link href='{verify}' color='blue'>{verify}</link>",
        styles["tiny"]
    ))

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawCentredString(
            page_w / 2, 8*mm,
            "Este documento es una representación impresa de un Comprobante Fiscal Digital a través de Internet."
        )
        canvas.drawCentredString(
            page_w / 2, 5*mm,
            f"UUID: {uuid}  |  Página {document.page}"
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)


# ---------------------------------------------------------------------------
# Interfaz Cyberpunk
# ---------------------------------------------------------------------------
class CyberpunkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NEON // CFDI CONVERTER 4.0")
        self.root.geometry("1040x720")
        self.root.minsize(850, 620)
        self.root.configure(bg=APP_BG)

        self._setup_style()
        self._build_ui()

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Cyber.Horizontal.TProgressbar",
            troughcolor="#202A40", background=CYAN,
            bordercolor="#202A40", lightcolor=CYAN, darkcolor=CYAN,
            thickness=13
        )

    def _label(self, parent, text, **kwargs):
        return tk.Label(parent, text=text, bg=kwargs.pop("bg", PANEL_BG),
                        fg=kwargs.pop("fg", TEXT), font=kwargs.pop("font", ("Consolas", 10)),
                        **kwargs)

    def _button(self, parent, text, command, accent=CYAN, **kwargs):
        btn = tk.Button(
            parent, text=text, command=command,
            bg="#17243B", fg=accent, activebackground=accent,
            activeforeground="#07111E", relief="flat", bd=0,
            font=("Consolas", 10, "bold"), padx=13, pady=10,
            cursor="hand2", **kwargs
        )
        btn.bind("<Enter>", lambda _e: btn.configure(highlightthickness=1, highlightbackground=accent))
        btn.bind("<Leave>", lambda _e: btn.configure(highlightthickness=0))
        return btn

    def _build_ui(self):
        header = tk.Frame(self.root, bg=APP_BG)
        header.pack(fill="x", padx=24, pady=(20, 10))
        self._label(header, "◢ NEON // CFDI CONVERTER", bg=APP_BG,
                    fg=CYAN, font=("Consolas", 22, "bold")).pack(anchor="w")
        self._label(header, "XML → PDF  |  CFDI 4.0  |  BATCH PROCESSING SYSTEM",
                    bg=APP_BG, fg=MAGENTA, font=("Consolas", 9)).pack(anchor="w", pady=(4, 0))

        top = tk.Frame(self.root, bg=PANEL_BG, highlightbackground=PURPLE, highlightthickness=1)
        top.pack(fill="x", padx=24, pady=8)
        actions = tk.Frame(top, bg=PANEL_BG)
        actions.pack(fill="x", padx=12, pady=12)
        self._button(actions, "＋ AGREGAR XML", self.add_files).pack(side="left", padx=4)
        self._button(actions, "▣ DESTINO", self.select_folder, accent=MAGENTA).pack(side="left", padx=4)
        self._button(actions, "◈ LOGOTIPO", self.select_logo, accent=PURPLE).pack(side="left", padx=4)
        self._button(actions, "↗ ABRIR DESTINO", self.open_folder, accent=GREEN).pack(side="left", padx=4)
        self._button(actions, "✕ LIMPIAR", self.clear_files, accent=RED).pack(side="right", padx=4)

        self.folder_label = self._label(top, "DESTINO: no seleccionado", fg=MUTED, font=("Consolas", 9))
        self.folder_label.pack(anchor="w", padx=17, pady=(0, 4))
        self.logo_label = self._label(top, "LOGO: ninguno", fg=MUTED, font=("Consolas", 9))
        self.logo_label.pack(anchor="w", padx=17, pady=(0, 12))

        body = tk.Frame(self.root, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=24, pady=8)

        left = tk.Frame(body, bg=PANEL_BG, highlightbackground=CYAN, highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._label(left, "/// ARCHIVOS EN COLA", fg=CYAN,
                    font=("Consolas", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 7))

        self.drop_area = tk.Frame(left, bg="#0D1729", highlightbackground=MAGENTA, highlightthickness=1)
        self.drop_area.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._label(self.drop_area, "⬇", bg="#0D1729", fg=MAGENTA,
                    font=("Consolas", 30, "bold")).pack(pady=(24, 0))
        self._label(self.drop_area, "ARRASTRA TUS XML AQUÍ", bg="#0D1729", fg=CYAN,
                    font=("Consolas", 13, "bold")).pack(pady=(4, 3))
        self._label(self.drop_area, "o utiliza el botón AGREGAR XML", bg="#0D1729",
                    fg=MUTED, font=("Consolas", 9)).pack(pady=(0, 12))

        list_frame = tk.Frame(self.drop_area, bg="#0D1729")
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.file_list = tk.Listbox(
            list_frame, bg="#080F1D", fg=TEXT, selectbackground="#263E5C",
            selectforeground=CYAN, relief="flat", bd=0,
            font=("Consolas", 9), activestyle="none",
            highlightthickness=1, highlightbackground="#263E5C"
        )
        self.file_list.pack(side="left", fill="both", expand=True)
        scroll = tk.Scrollbar(list_frame, command=self.file_list.yview,
                              bg=PANEL_BG, troughcolor="#080F1D")
        scroll.pack(side="right", fill="y")
        self.file_list.configure(yscrollcommand=scroll.set)

        if DND_AVAILABLE:
            self.drop_area.drop_target_register(DND_FILES)
            self.drop_area.dnd_bind("<<Drop>>", self.on_drop)
            self.file_list.drop_target_register(DND_FILES)
            self.file_list.dnd_bind("<<Drop>>", self.on_drop)
            self.drop_hint = "DRAG & DROP ACTIVO"
        else:
            self.drop_hint = "Para activar drag & drop: pip install tkinterdnd2"
        self._label(left, self.drop_hint, fg=GREEN if DND_AVAILABLE else MAGENTA,
                    font=("Consolas", 8)).pack(anchor="w", padx=14, pady=(0, 10))

        right = tk.Frame(body, bg=PANEL_BG, width=280,
                         highlightbackground=MAGENTA, highlightthickness=1)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        self._label(right, "/// CONTROL", fg=MAGENTA,
                    font=("Consolas", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 15))
        self._button(right, "▶  CONVERTIR A PDF", self.convert,
                     accent=GREEN).pack(fill="x", padx=13, pady=5)
        self._button(right, "−  QUITAR SELECCIONADO", self.remove_selected,
                     accent=RED).pack(fill="x", padx=13, pady=5)
        self._label(right, "PROGRESO DEL PROCESO", fg=CYAN,
                    font=("Consolas", 8, "bold")).pack(anchor="w", padx=14, pady=(22, 5))
        self.progress = ttk.Progressbar(right, style="Cyber.Horizontal.TProgressbar",
                                         mode="determinate")
        self.progress.pack(fill="x", padx=14)
        self.progress_label = self._label(right, "0 / 0 archivos", fg=MUTED,
                                           font=("Consolas", 8))
        self.progress_label.pack(anchor="e", padx=14, pady=(4, 12))
        self._label(right, "SALIDA DEL SISTEMA", fg=CYAN,
                    font=("Consolas", 8, "bold")).pack(anchor="w", padx=14, pady=(8, 5))
        self.log = tk.Text(right, bg="#080F1D", fg=GREEN, insertbackground=CYAN,
                           relief="flat", bd=0, font=("Consolas", 8),
                           wrap="word", height=15, highlightthickness=1,
                           highlightbackground="#263E5C")
        self.log.pack(fill="both", expand=True, padx=13, pady=(0, 13))
        self.log.configure(state="disabled")

        footer = self._label(self.root, "SYSTEM READY  //  CYBERPUNK RETRO EDITION",
                             bg=APP_BG, fg=PURPLE, font=("Consolas", 8))
        footer.pack(anchor="e", padx=26, pady=(0, 10))

    def write_log(self, text, color=None):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def add_paths(self, paths):
        added = 0
        for path in paths:
            path = os.path.abspath(os.path.expanduser(path))
            if os.path.isfile(path) and path.lower().endswith(".xml") and path not in archivos:
                archivos.append(path)
                self.file_list.insert("end", f"  ◇  {os.path.basename(path)}")
                added += 1
        if added:
            self.write_log(f"[+] {added} XML agregado(s)")
        else:
            self.write_log("[!] No se agregaron archivos XML nuevos.")

    def on_drop(self, event):
        try:
            paths = self.root.tk.splitlist(event.data)
            self.add_paths(paths)
        except Exception as exc:
            self.write_log(f"[ERROR DROP] {exc}")
        return event.action

    def add_files(self):
        paths = filedialog.askopenfilenames(
            title="Seleccionar CFDI XML",
            filetypes=[("Archivos XML", "*.xml"), ("Todos los archivos", "*.*")]
        )
        if paths:
            self.add_paths(paths)

    def remove_selected(self):
        selected = list(self.file_list.curselection())
        for index in reversed(selected):
            self.file_list.delete(index)
            del archivos[index]
        if selected:
            self.write_log(f"[-] {len(selected)} archivo(s) retirado(s)")

    def clear_files(self):
        archivos.clear()
        self.file_list.delete(0, "end")
        self.progress["value"] = 0
        self.progress_label.configure(text="0 / 0 archivos")
        self.write_log("[i] Cola limpiada")

    def select_folder(self):
        global DESTINO
        path = filedialog.askdirectory(title="Seleccionar carpeta de salida")
        if path:
            DESTINO = path
            self.folder_label.configure(text=f"DESTINO: {path}", fg=GREEN)
            self.write_log(f"[+] Destino: {path}")

    def select_logo(self):
        global LOGO_PATH
        path = filedialog.askopenfilename(
            title="Seleccionar logotipo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("Todos", "*.*")]
        )
        if path:
            LOGO_PATH = path
            self.logo_label.configure(text=f"LOGO: {os.path.basename(path)}", fg=GREEN)
            self.write_log("[+] Logotipo seleccionado")

    def open_folder(self):
        if not DESTINO:
            messagebox.showwarning("Destino requerido", "Selecciona primero una carpeta de destino.")
            return
        try:
            if platform.system() == "Windows":
                os.startfile(DESTINO)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", DESTINO])
            else:
                subprocess.Popen(["xdg-open", DESTINO])
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta:\n{exc}")

    def convert(self):
        if not archivos:
            messagebox.showwarning("Sin archivos", "Agrega uno o más XML para comenzar.")
            return
        if not DESTINO:
            messagebox.showwarning("Destino requerido", "Selecciona la carpeta donde se guardarán los PDF.")
            return

        os.makedirs(DESTINO, exist_ok=True)
        total = len(archivos)
        self.progress.configure(maximum=total, value=0)
        exitos = 0
        errores = 0
        self.write_log("── INICIANDO CONVERSIÓN ──")

        for index, path in enumerate(list(archivos), start=1):
            nombre = os.path.basename(path)
            try:
                datos = parse_cfdi(path)
                if "error" in datos:
                    raise ValueError(datos["error"])
                uuid = datos.get("Timbre", {}).get("UUID", "")
                base = Path(path).stem
                if uuid:
                    base = f"{base}_{uuid[:8]}"
                salida = os.path.join(DESTINO, safe_filename(base) + ".pdf")
                generar_pdf(datos, salida, LOGO_PATH or None)
                exitos += 1
                self.write_log(f"[OK] {nombre} → {os.path.basename(salida)}")
            except Exception as exc:
                errores += 1
                self.write_log(f"[ERROR] {nombre}: {exc}")

            self.progress.configure(value=index)
            self.progress_label.configure(text=f"{index} / {total} archivos")
            self.root.update_idletasks()

        self.write_log(f"── FINALIZADO: {exitos} OK | {errores} ERROR ──")
        messagebox.showinfo(
            "Proceso terminado",
            f"Conversión finalizada.\n\nCorrectos: {exitos}\nErrores: {errores}\n\nDestino:\n{DESTINO}"
        )


def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    CyberpunkApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
