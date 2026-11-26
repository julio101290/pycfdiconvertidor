import io
import os
import platform
import subprocess
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import qrcode
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_DISPONIBLE = True
except ImportError:
    DND_DISPONIBLE = False


# ==========================================
# CATÁLOGOS BÁSICOS SAT (CFDI 4.0)
# ==========================================
CAT_TIPO_COMPROBANTE = {
    "I": "Ingreso",
    "E": "Egreso",
    "T": "Traslado",
    "N": "Nómina",
    "P": "Pago",
}

CAT_METODO_PAGO = {
    "PUE": "Pago en una sola exhibición",
    "PPD": "Pago en parcialidades o diferido",
}

CAT_FORMA_PAGO = {
    "01": "Efectivo",
    "02": "Cheque nominativo",
    "03": "Transferencia electrónica de fondos",
    "04": "Tarjeta de crédito",
    "05": "Monedero electrónico",
    "06": "Dinero electrónico",
    "08": "Vales de despensa",
    "12": "Dación en pago",
    "15": "Condonación",
    "17": "Compensación",
    "28": "Tarjeta de débito",
    "29": "Tarjeta de servicios",
    "30": "Aplicación de anticipos",
    "31": "Intermediario pagos",
    "99": "Por definir",
}

CAT_EXPORTACION = {
    "01": "No aplica",
    "02": "Definitiva con clave A1",
    "03": "Temporal",
    "04": "Definitiva con clave distinta a A1",
}

CAT_OBJETO_IMP = {
    "01": "No objeto de impuesto",
    "02": "Sí objeto de impuesto",
    "03": "Sí objeto del impuesto y no obligado al desglose",
    "04": "Sí objeto del impuesto y no causa impuesto",
    "05": "Sí objeto del impuesto, IVA crédito PODEBI",
}

CAT_IMPUESTO = {
    "001": "ISR",
    "002": "IVA",
    "003": "IEPS",
}

CAT_REGIMEN = {
    "601": "General de Ley Personas Morales",
    "603": "Personas Morales con Fines no Lucrativos",
    "605": "Sueldos y Salarios e Ingresos Asimilados a Salarios",
    "606": "Arrendamiento",
    "608": "Demás ingresos",
    "612": "Personas Físicas con Actividades Empresariales y Profesionales",
    "616": "Sin obligaciones fiscales",
    "621": "Incorporación Fiscal",
    "625": "Actividades Empresariales con ingresos a través de Plataformas Tecnológicas",
    "626": "Régimen Simplificado de Confianza",
}

CAT_USO_CFDI = {
    "G01": "Adquisición de mercancías",
    "G02": "Devoluciones, descuentos o bonificaciones",
    "G03": "Gastos en general",
    "I01": "Construcciones",
    "I04": "Equipo de computo y accesorios",
    "I08": "Otra maquinaria y equipo",
    "D01": "Honorarios médicos, dentales y gastos hospitalarios",
    "D04": "Donativos",
    "S01": "Sin efectos fiscales",
    "CP01": "Pagos",
    "CN01": "Nómina",
}


def desc_catalogo(catalogo, clave):
    if not clave:
        return ""
    desc = catalogo.get(clave)
    return f"{clave} - {desc}" if desc else clave


def fmt_num(valor, decimales=2):
    if valor in (None, ""):
        return ""
    try:
        return f"{float(valor):,.{decimales}f}"
    except ValueError:
        return str(valor)


def cortar_texto_largo(texto, ancho=105):
    if not texto:
        return ""
    seguro = escape(str(texto))
    return "<br/>".join(seguro[i:i + ancho] for i in range(0, len(seguro), ancho))


# ==========================================
# PARSER XML CFDI 4.0 / 3.3
# ==========================================
def parse_cfdi(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Detectar versión del namespace CFDI
        if "cfd/4" in root.tag:
            ns_cfdi = "http://www.sat.gob.mx/cfd/4"
        else:
            ns_cfdi = "http://www.sat.gob.mx/cfd/3"

        ns = {
            "cfdi": ns_cfdi,
            "tfd": "http://www.sat.gob.mx/TimbreFiscalDigital",
        }

        emisor_el = root.find("cfdi:Emisor", ns)
        receptor_el = root.find("cfdi:Receptor", ns)
        timbre_el = root.find(".//tfd:TimbreFiscalDigital", ns)

        conceptos = []
        for c_el in root.findall("cfdi:Conceptos/cfdi:Concepto", ns):
            c_data = dict(c_el.attrib)
            traslados_c = [
                dict(t.attrib)
                for t in c_el.findall("cfdi:Impuestos/cfdi:Traslados/cfdi:Traslado", ns)
            ]
            retenciones_c = [
                dict(r.attrib)
                for r in c_el.findall("cfdi:Impuestos/cfdi:Retenciones/cfdi:Retencion", ns)
            ]
            c_data["Traslados"] = traslados_c
            c_data["Retenciones"] = retenciones_c
            conceptos.append(c_data)

        impuestos_el = root.find("cfdi:Impuestos", ns)
        impuestos_totales = dict(impuestos_el.attrib) if impuestos_el is not None else {}
        impuestos_detalle = []

        if impuestos_el is not None:
            for t in impuestos_el.findall("cfdi:Traslados/cfdi:Traslado", ns):
                item = dict(t.attrib)
                item["Tipo"] = "Traslado"
                impuestos_detalle.append(item)
            for r in impuestos_el.findall("cfdi:Retenciones/cfdi:Retencion", ns):
                item = dict(r.attrib)
                item["Tipo"] = "Retención"
                impuestos_detalle.append(item)

        return {
            "Comprobante": dict(root.attrib),
            "Emisor": dict(emisor_el.attrib) if emisor_el is not None else {},
            "Receptor": dict(receptor_el.attrib) if receptor_el is not None else {},
            "Conceptos": conceptos,
            "ImpuestosTotales": impuestos_totales,
            "ImpuestosDetalle": impuestos_detalle,
            "Timbre": dict(timbre_el.attrib) if timbre_el is not None else {},
        }
    except Exception as e:
        return {"error": str(e)}


# ==========================================
# CANVAS CON PIE DE PÁGINA (PÁGINA X DE Y)
# ==========================================
class CFDIReportCanvas(canvas.Canvas):
    def __init__(self, *args, uuid_text="", version="4.0", **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []
        self.uuid_text = uuid_text
        self.version = version

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(num_pages)
            super().showPage()
        super().save()

    def _draw_footer(self, page_count):
        width, _ = letter
        self.saveState()
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(12 * mm, 16 * mm, width - 12 * mm, 16 * mm)

        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#475569"))
        self.drawCentredString(
            width / 2,
            12 * mm,
            f"Este documento es una representación impresa de un Comprobante Fiscal Digital a través de Internet versión {self.version}",
        )
        self.setFont("Helvetica-Bold", 7)
        self.drawCentredString(
            width / 2,
            8.2 * mm,
            f"UUID: {self.uuid_text}  -  Página {self._pageNumber} de {page_count}",
        )
        self.restoreState()


# ==========================================
# GENERADOR DE PDF ESTILO SAT CFDI 4.0
# ==========================================
def generar_pdf(datos, salida_pdf, logotipo_path=None):
    comp = datos.get("Comprobante", {})
    emisor = datos.get("Emisor", {})
    receptor = datos.get("Receptor", {})
    timbre = datos.get("Timbre", {})
    conceptos = datos.get("Conceptos", [])
    imp_totales = datos.get("ImpuestosTotales", {})
    imp_detalle = datos.get("ImpuestosDetalle", [])

    uuid = timbre.get("UUID", "NO DISPONIBLE")
    version = comp.get("Version", "4.0")

    doc = SimpleDocTemplate(
        salida_pdf,
        pagesize=letter,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=20 * mm,
        title=f"CFDI {uuid}",
    )

    styles = getSampleStyleSheet()
    c_oscuro = colors.HexColor("#1E293B")
    c_gris_bg = colors.HexColor("#F1F5F9")
    c_borde = colors.HexColor("#CBD5E1")
    c_acento = colors.HexColor("#0F172A")

    st_titulo_sec = ParagraphStyle(
        "TituloSec",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        textColor=colors.white,
        leading=10,
    )
    st_normal = ParagraphStyle(
        "NormalCFDI",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        textColor=c_oscuro,
        leading=9.5,
    )
    st_small = ParagraphStyle(
        "SmallCFDI",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.8,
        textColor=c_oscuro,
        leading=8.5,
    )
    st_mono = ParagraphStyle(
        "MonoCFDI",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=6.2,
        textColor=c_oscuro,
        leading=7.6,
    )
    st_uuid = ParagraphStyle(
        "UuidHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=c_acento,
        leading=11,
    )
    st_th = ParagraphStyle(
        "TableHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.2,
        textColor=colors.white,
        alignment=TA_CENTER,
        leading=9,
    )
    st_td_c = ParagraphStyle("TdC", parent=st_normal, alignment=TA_CENTER, fontSize=7.2)
    st_td_r = ParagraphStyle("TdR", parent=st_normal, alignment=TA_RIGHT, fontSize=7.2)

    elementos = []
    ancho_util = 190 * mm

    # --- URL OFICIAL DE VERIFICACIÓN SAT + QR ---
    sello_cfd = timbre.get("SelloCFD", comp.get("Sello", ""))
    ultimos_8 = sello_cfd[-8:] if len(sello_cfd) >= 8 else sello_cfd
    url_verificacion = (
        "https://verificacfdi.facturaelectronica.sat.gob.mx/default.aspx"
        f"?id={uuid}"
        f"&re={emisor.get('Rfc', '')}"
        f"&rr={receptor.get('Rfc', '')}"
        f"&tt={comp.get('Total', '0.00')}"
        f"&fe={ultimos_8}"
    )

    qr_img = qrcode.make(url_verificacion)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    rl_qr = RLImage(qr_buffer, width=34 * mm, height=34 * mm)

    # Columna izquierda del encabezado (Logo opcional + QR)
    col_izq_header = []
    if logotipo_path and os.path.isfile(logotipo_path):
        try:
            rl_logo = RLImage(logotipo_path, width=34 * mm, height=16 * mm, kind="proportional")
            col_izq_header.append(rl_logo)
            col_izq_header.append(Spacer(1, 2 * mm))
        except Exception:
            pass
    col_izq_header.append(rl_qr)

    # Columna derecha del encabezado (Datos del comprobante y certificación)
    meta_col1 = [
        f"<b>Tipo:</b> {escape(desc_catalogo(CAT_TIPO_COMPROBANTE, comp.get('TipoDeComprobante', '')))}",
        f"<b>Serie:</b> {escape(comp.get('Serie', '(sin serie)'))} &nbsp;&nbsp; <b>Folio:</b> {escape(comp.get('Folio', '(sin folio)'))}",
        f"<b>Lugar de expedición:</b> {escape(comp.get('LugarExpedicion', ''))}",
        f"<b>Fecha:</b> {escape(comp.get('Fecha', ''))}",
        f"<b>Forma de pago:</b> {escape(desc_catalogo(CAT_FORMA_PAGO, comp.get('FormaPago', '')))}",
        f"<b>Método de pago:</b> {escape(desc_catalogo(CAT_METODO_PAGO, comp.get('MetodoPago', '')))}",
        f"<b>Condiciones de pago:</b> {escape(comp.get('CondicionesDePago', '(ninguna)'))}",
    ]
    meta_col2 = [
        f"<b>Certificado emisor:</b> {escape(comp.get('NoCertificado', ''))}",
        f"<b>Certificado SAT:</b> {escape(timbre.get('NoCertificadoSAT', ''))}",
        f"<b>RFC proveedor:</b> {escape(timbre.get('RfcProvCertif', ''))}",
        f"<b>Fecha certificación:</b> {escape(timbre.get('FechaTimbrado', ''))}",
        f"<b>Exportación:</b> {escape(desc_catalogo(CAT_EXPORTACION, comp.get('Exportacion', '')))}",
    ]

    meta_grid = Table(
        [
            [Paragraph(f"UUID: {escape(uuid)}", st_uuid), ""],
            [
                Paragraph("<br/>".join(meta_col1), st_small),
                Paragraph("<br/>".join(meta_col2), st_small),
            ],
        ],
        colWidths=[76 * mm, 72 * mm],
    )
    meta_grid.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (1, 0)),
                ("BACKGROUND", (0, 0), (1, 0), c_gris_bg),
                ("BOX", (0, 0), (-1, -1), 0.6, c_borde),
                ("LINEBELOW", (0, 0), (1, 0), 0.6, c_borde),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    header_tbl = Table([[col_izq_header, meta_grid]], colWidths=[40 * mm, 150 * mm])
    header_tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    elementos.append(header_tbl)
    elementos.append(Spacer(1, 4 * mm))

    # --- EMISOR Y RECEPTOR ---
    emisor_lines = [
        f"<b>{escape(emisor.get('Nombre', ''))}</b>",
        f"<b>RFC:</b> {escape(emisor.get('Rfc', ''))}",
        f"<b>Régimen fiscal:</b> {escape(desc_catalogo(CAT_REGIMEN, emisor.get('RegimenFiscal', '')))}",
    ]
    receptor_lines = [
        f"<b>{escape(receptor.get('Nombre', ''))}</b>",
        f"<b>RFC:</b> {escape(receptor.get('Rfc', ''))}",
        f"<b>Uso del CFDI:</b> {escape(desc_catalogo(CAT_USO_CFDI, receptor.get('UsoCFDI', '')))}",
        f"<b>Domicilio fiscal receptor:</b> {escape(receptor.get('DomicilioFiscalReceptor', ''))}",
        f"<b>Régimen fiscal receptor:</b> {escape(desc_catalogo(CAT_REGIMEN, receptor.get('RegimenFiscalReceptor', '')))}",
    ]

    partes_tbl = Table(
        [
            [Paragraph("Emisor", st_titulo_sec), "", Paragraph("Receptor", st_titulo_sec)],
            [
                Paragraph("<br/>".join(emisor_lines), st_small),
                "",
                Paragraph("<br/>".join(receptor_lines), st_small),
            ],
        ],
        colWidths=[93 * mm, 4 * mm, 93 * mm],
    )
    partes_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), c_acento),
                ("BACKGROUND", (2, 0), (2, 0), c_acento),
                ("BOX", (0, 0), (0, 1), 0.6, c_borde),
                ("BOX", (2, 0), (2, 1), 0.6, c_borde),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, 1), 5),
                ("RIGHTPADDING", (0, 0), (0, 1), 5),
                ("LEFTPADDING", (2, 0), (2, 1), 5),
                ("RIGHTPADDING", (2, 0), (2, 1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elementos.append(partes_tbl)
    elementos.append(Spacer(1, 4 * mm))

    # --- CONCEPTOS ---
    total_conceptos = len(conceptos)
    for idx, c in enumerate(conceptos, start=1):
        desc = escape(c.get("Descripcion", ""))
        no_id = escape(c.get("NoIdentificacion", "(ninguno)"))
        clave_sat = escape(c.get("ClaveProdServ", ""))
        obj_imp = escape(desc_catalogo(CAT_OBJETO_IMP, c.get("ObjetoImp", "")))
        clave_uni = escape(c.get("ClaveUnidad", ""))
        unidad = escape(c.get("Unidad", "(ninguna)"))
        cantidad = fmt_num(c.get("Cantidad", "0"), 2)
        v_unit = fmt_num(c.get("ValorUnitario", "0"), 2)
        descuento = fmt_num(c.get("Descuento"), 2) if c.get("Descuento") else "(ninguno)"
        importe = fmt_num(c.get("Importe", "0"), 2)

        detalles_c = [
            f"<b>Descripción:</b> {desc}",
            f"<b>No. identificación:</b> {no_id} &nbsp;|&nbsp; <b>Clave SAT:</b> {clave_sat} &nbsp;|&nbsp; "
            f"<b>Objeto de impuesto:</b> {obj_imp} &nbsp;|&nbsp; <b>Clave Unidad:</b> {clave_uni} &nbsp;|&nbsp; <b>Unidad:</b> {unidad}",
            f"<b>Cantidad:</b> {cantidad} &nbsp;|&nbsp; <b>Valor unitario:</b> ${v_unit} &nbsp;|&nbsp; "
            f"<b>Descuento:</b> {descuento} &nbsp;|&nbsp; <b>Importe:</b> <b>${importe}</b>",
        ]

        for t in c.get("Traslados", []):
            detalles_c.append(
                f"<i>Traslado</i> — <b>Impuesto:</b> {escape(desc_catalogo(CAT_IMPUESTO, t.get('Impuesto', '')))} &nbsp;|&nbsp; "
                f"<b>Base:</b> {fmt_num(t.get('Base'))} &nbsp;|&nbsp; <b>Tipo factor:</b> {escape(t.get('TipoFactor', ''))} &nbsp;|&nbsp; "
                f"<b>Tasa o cuota:</b> {escape(t.get('TasaOCuota', ''))} &nbsp;|&nbsp; <b>Importe:</b> {fmt_num(t.get('Importe'))}"
            )
        for r in c.get("Retenciones", []):
            detalles_c.append(
                f"<i>Retención</i> — <b>Impuesto:</b> {escape(desc_catalogo(CAT_IMPUESTO, r.get('Impuesto', '')))} &nbsp;|&nbsp; "
                f"<b>Base:</b> {fmt_num(r.get('Base'))} &nbsp;|&nbsp; <b>Tipo factor:</b> {escape(r.get('TipoFactor', ''))} &nbsp;|&nbsp; "
                f"<b>Tasa o cuota:</b> {escape(r.get('TasaOCuota', ''))} &nbsp;|&nbsp; <b>Importe:</b> {fmt_num(r.get('Importe'))}"
            )

        c_tbl = Table(
            [
                [Paragraph(f"Concepto: {idx} de {total_conceptos}", st_titulo_sec)],
                [Paragraph("<br/>".join(detalles_c), st_small)],
            ],
            colWidths=[ancho_util],
        )
        c_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#334155")),
                    ("BOX", (0, 0), (-1, -1), 0.6, c_borde),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ]
            )
        )
        elementos.append(KeepTogether([c_tbl, Spacer(1, 2.5 * mm)]))

    # --- TABLA DE IMPUESTOS ---
    if imp_detalle:
        filas_imp = [
            [
                Paragraph("Tipo", st_th),
                Paragraph("Base", st_th),
                Paragraph("Impuesto", st_th),
                Paragraph("Tipo factor", st_th),
                Paragraph("Tasa o cuota", st_th),
                Paragraph("Importe", st_th),
            ]
        ]
        for imp in imp_detalle:
            filas_imp.append(
                [
                    Paragraph(escape(imp.get("Tipo", "")), st_td_c),
                    Paragraph(fmt_num(imp.get("Base")) if imp.get("Base") else "-", st_td_r),
                    Paragraph(escape(desc_catalogo(CAT_IMPUESTO, imp.get("Impuesto", ""))), st_td_c),
                    Paragraph(escape(imp.get("TipoFactor", "-")), st_td_c),
                    Paragraph(escape(imp.get("TasaOCuota", "-")), st_td_r),
                    Paragraph(fmt_num(imp.get("Importe")), st_td_r),
                ]
            )

        sec_imp_head = Table([[Paragraph("Impuestos", st_titulo_sec)]], colWidths=[ancho_util])
        sec_imp_head.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), c_acento),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        imp_tbl = Table(
            filas_imp,
            colWidths=[28 * mm, 32 * mm, 36 * mm, 28 * mm, 34 * mm, 32 * mm],
        )
        imp_tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#475569")),
                    ("GRID", (0, 0), (-1, -1), 0.5, c_borde),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_gris_bg]),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        elementos.append(KeepTogether([sec_imp_head, imp_tbl, Spacer(1, 3.5 * mm)]))

    # --- TABLA DE TOTALES ---
    sec_tot_head = Table([[Paragraph("Totales", st_titulo_sec)]], colWidths=[ancho_util])
    sec_tot_head.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), c_acento),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    tot_tbl = Table(
        [
            [
                Paragraph("Moneda", st_th),
                Paragraph("Tipo de cambio", st_th),
                Paragraph("Subtotal", st_th),
                Paragraph("Descuentos", st_th),
                Paragraph("Imp. trasladados", st_th),
                Paragraph("Imp. retenidos", st_th),
                Paragraph("Total", st_th),
            ],
            [
                Paragraph(escape(comp.get("Moneda", "MXN")), st_td_c),
                Paragraph(escape(comp.get("TipoCambio", "1")), st_td_c),
                Paragraph(fmt_num(comp.get("SubTotal", "0")), st_td_r),
                Paragraph(fmt_num(comp.get("Descuento")) if comp.get("Descuento") else "0.00", st_td_r),
                Paragraph(fmt_num(imp_totales.get("TotalImpuestosTrasladados")) or "0.00", st_td_r),
                Paragraph(fmt_num(imp_totales.get("TotalImpuestosRetenidos")) or "0.00", st_td_r),
                Paragraph(f"<b>{fmt_num(comp.get('Total', '0'))}</b>", st_td_r),
            ],
        ],
        colWidths=[20 * mm, 24 * mm, 29 * mm, 26 * mm, 31 * mm, 30 * mm, 30 * mm],
    )
    tot_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#475569")),
                ("BACKGROUND", (6, 1), (6, 1), c_gris_bg),
                ("GRID", (0, 0), (-1, -1), 0.5, c_borde),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ]
        )
    )
    elementos.append(KeepTogether([sec_tot_head, tot_tbl, Spacer(1, 4 * mm)]))

    # --- DATOS FISCALES (SELLOS Y CADENA ORIGINAL TFD) ---
    sello_sat = timbre.get("SelloSAT", "")
    cadena_tfd = (
        f"||{timbre.get('Version', '1.1')}|{uuid}|{timbre.get('FechaTimbrado', '')}|"
        f"{timbre.get('RfcProvCertif', '')}|{sello_cfd}|{timbre.get('NoCertificadoSAT', '')}||"
    )

    fiscales_body = [
        Paragraph("<b>Sello digital del CFDI:</b>", st_small),
        Paragraph(cortar_texto_largo(sello_cfd, 110), st_mono),
        Spacer(1, 1.5 * mm),
        Paragraph("<b>Sello del SAT:</b>", st_small),
        Paragraph(cortar_texto_largo(sello_sat, 110), st_mono),
        Spacer(1, 1.5 * mm),
        Paragraph("<b>Cadena original del complemento de certificación digital del SAT:</b>", st_small),
        Paragraph(cortar_texto_largo(cadena_tfd, 110), st_mono),
        Spacer(1, 1.5 * mm),
        Paragraph("<b>Verificación SAT:</b>", st_small),
        Paragraph(cortar_texto_largo(url_verificacion, 110), st_mono),
    ]

    fiscales_tbl = Table(
        [
            [Paragraph("Datos fiscales", st_titulo_sec)],
            [fiscales_body],
        ],
        colWidths=[ancho_util],
    )
    fiscales_tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), c_acento),
                ("BOX", (0, 0), (-1, -1), 0.6, c_borde),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elementos.append(KeepTogether([fiscales_tbl]))

    doc.build(
        elementos,
        canvasmaker=lambda *args, **kwargs: CFDIReportCanvas(
            *args, uuid_text=uuid, version=version, **kwargs
        ),
    )


# ==========================================
# INTERFAZ RETRO CYBERPUNK (TKINTER + DND)
# ==========================================
class CyberCFDIApp:
    # Paleta Retro Cyberpunk
    BG_MAIN = "#090A10"
    BG_PANEL = "#121521"
    BG_INPUT = "#0D101A"
    NEON_CYAN = "#00F3FF"
    NEON_PINK = "#FF007F"
    NEON_GREEN = "#39FF14"
    NEON_AMBER = "#FFB800"
    TEXT_LIGHT = "#E2E8F0"
    TEXT_DIM = "#64748B"

    def __init__(self, root):
        self.root = root
        self.root.title("CYBER_CFDI // 4.0 XML -> PDF CONVERTER")
        self.root.geometry("880x660")
        self.root.minsize(780, 580)
        self.root.configure(bg=self.BG_MAIN)

        self.carpeta_destino = ""
        self.logotipo_path = ""
        self.archivos_xml = []

        self.font_mono = self._detectar_fuente()
        self._configurar_estilos()
        self._construir_ui()

        if DND_DISPONIBLE:
            self._activar_dnd()
            self._log(">> MÓDULO DRAG & DROP [ACTIVO] - Arrastra tus XML o carpetas aquí.", "cyan")
        else:
            self._log(
                ">> AVISO: Instala 'tkinterdnd2' (pip install tkinterdnd2) para habilitar arrastrar y soltar.",
                "amber",
            )

    def _detectar_fuente(self):
        sistema = platform.system()
        if sistema == "Windows":
            return "Consolas"
        if sistema == "Darwin":
            return "Menlo"
        return "DejaVu Sans Mono"

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Cyber.Horizontal.TProgressbar",
            troughcolor=self.BG_INPUT,
            bordercolor=self.NEON_CYAN,
            background=self.NEON_PINK,
            lightcolor=self.NEON_PINK,
            darkcolor=self.NEON_PINK,
            thickness=16,
        )

    def _crear_boton_cyber(self, parent, texto, comando, borde=None, texto_color=None):
        borde = borde or self.NEON_CYAN
        texto_color = texto_color or borde
        btn = tk.Button(
            parent,
            text=texto,
            command=comando,
            bg=self.BG_PANEL,
            fg=texto_color,
            activebackground=borde,
            activeforeground=self.BG_MAIN,
            font=(self.font_mono, 9, "bold"),
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=borde,
            highlightcolor=borde,
            padx=12,
            pady=6,
            cursor="hand2",
        )
        btn.bind("<Enter>", lambda e: btn.configure(bg=borde, fg=self.BG_MAIN))
        btn.bind("<Leave>", lambda e: btn.configure(bg=self.BG_PANEL, fg=texto_color))
        return btn

    def _construir_ui(self):
        # --- BANNER SUPERIOR ---
        header = tk.Frame(self.root, bg=self.BG_MAIN)
        header.pack(fill="x", padx=18, pady=(14, 6))

        tk.Label(
            header,
            text="[ CYBER_CFDI v4.0 ]",
            bg=self.BG_MAIN,
            fg=self.NEON_CYAN,
            font=(self.font_mono, 18, "bold"),
        ).pack(side="left")

        tk.Label(
            header,
            text="// SAT XML-TO-PDF ENGINE",
            bg=self.BG_MAIN,
            fg=self.NEON_PINK,
            font=(self.font_mono, 11, "bold"),
        ).pack(side="left", padx=(8, 0), pady=(5, 0))

        tk.Frame(self.root, bg=self.NEON_PINK, height=2).pack(fill="x", padx=18, pady=(0, 10))

        # --- BARRA DE BOTONES ---
        toolbar = tk.Frame(self.root, bg=self.BG_MAIN)
        toolbar.pack(fill="x", padx=18, pady=4)

        self._crear_boton_cyber(toolbar, "+ AGREGAR XML", self.seleccionar_archivos, self.NEON_CYAN).pack(
            side="left", padx=(0, 8)
        )
        self._crear_boton_cyber(toolbar, "CARPETA SALIDA", self.seleccionar_carpeta, self.NEON_CYAN).pack(
            side="left", padx=(0, 8)
        )
        self._crear_boton_cyber(toolbar, "LOGOTIPO", self.seleccionar_logotipo, self.NEON_AMBER).pack(
            side="left", padx=(0, 8)
        )
        self._crear_boton_cyber(toolbar, "ABRIR SALIDA", self.abrir_carpeta_destino, self.NEON_GREEN).pack(
            side="left", padx=(0, 8)
        )
        self._crear_boton_cyber(toolbar, "LIMPIAR COLA", self.limpiar_lista, self.NEON_PINK).pack(
            side="right"
        )

        # --- PANEL DE RUTAS ---
        info_frame = tk.Frame(
            self.root,
            bg=self.BG_PANEL,
            highlightthickness=1,
            highlightbackground="#1E293B",
        )
        info_frame.pack(fill="x", padx=18, pady=8)

        self.lbl_carpeta = tk.Label(
            info_frame,
            text="DESTINO : [Misma carpeta de cada XML]",
            bg=self.BG_PANEL,
            fg=self.TEXT_LIGHT,
            font=(self.font_mono, 8),
            anchor="w",
        )
        self.lbl_carpeta.pack(fill="x", padx=10, pady=(6, 2))

        self.lbl_logo = tk.Label(
            info_frame,
            text="LOGOTIPO: [Ninguno seleccionado]",
            bg=self.BG_PANEL,
            fg=self.TEXT_DIM,
            font=(self.font_mono, 8),
            anchor="w",
        )
        self.lbl_logo.pack(fill="x", padx=10, pady=(0, 6))

        # --- ZONA DRAG & DROP / COLA DE ARCHIVOS ---
        drop_header = tk.Frame(self.root, bg=self.BG_MAIN)
        drop_header.pack(fill="x", padx=18, pady=(4, 2))

        tk.Label(
            drop_header,
            text=">> COLA DE PROCESAMIENTO (ARRASTRA Y SUELTA ARCHIVOS .XML O CARPETAS)",
            bg=self.BG_MAIN,
            fg=self.NEON_CYAN,
            font=(self.font_mono, 8, "bold"),
        ).pack(side="left")

        self.lbl_contador = tk.Label(
            drop_header,
            text="[0 ARCHIVOS]",
            bg=self.BG_MAIN,
            fg=self.NEON_PINK,
            font=(self.font_mono, 8, "bold"),
        )
        self.lbl_contador.pack(side="right")

        list_container = tk.Frame(
            self.root,
            bg=self.NEON_CYAN,
            padx=1,
            pady=1,
        )
        list_container.pack(fill="both", expand=True, padx=18, pady=(0, 10))

        self.lista_archivos = tk.Listbox(
            list_container,
            bg=self.BG_INPUT,
            fg=self.NEON_GREEN,
            selectbackground=self.NEON_PINK,
            selectforeground=self.BG_MAIN,
            font=(self.font_mono, 9),
            relief="flat",
            bd=0,
            activestyle="none",
        )
        scroll_lista = tk.Scrollbar(list_container, command=self.lista_archivos.yview)
        self.lista_archivos.configure(yscrollcommand=scroll_lista.set)
        self.lista_archivos.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scroll_lista.pack(side="right", fill="y")

        # --- BOTÓN PRINCIPAL DE EJECUCIÓN Y BARRA DE PROGRESO ---
        action_frame = tk.Frame(self.root, bg=self.BG_MAIN)
        action_frame.pack(fill="x", padx=18, pady=4)

        self.btn_convertir = self._crear_boton_cyber(
            action_frame,
            "[ >> EJECUTAR CONVERSIÓN A PDF << ]",
            self.convertir_archivos,
            self.NEON_PINK,
            self.NEON_PINK,
        )
        self.btn_convertir.configure(font=(self.font_mono, 11, "bold"), pady=8)
        self.btn_convertir.pack(fill="x")

        self.barra = ttk.Progressbar(
            self.root,
            style="Cyber.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
        )
        self.barra.pack(fill="x", padx=18, pady=(8, 8))

        # --- CONSOLA DE LOGS ---
        tk.Label(
            self.root,
            text=">> TERMINAL DE SALIDA",
            bg=self.BG_MAIN,
            fg=self.TEXT_DIM,
            font=(self.font_mono, 8, "bold"),
            anchor="w",
        ).pack(fill="x", padx=18)

        log_container = tk.Frame(self.root, bg="#1E293B", padx=1, pady=1)
        log_container.pack(fill="both", expand=False, padx=18, pady=(2, 14))

        self.estado = tk.Text(
            log_container,
            height=9,
            bg=self.BG_INPUT,
            fg=self.TEXT_LIGHT,
            insertbackground=self.NEON_CYAN,
            font=(self.font_mono, 8),
            relief="flat",
            bd=0,
            state="disabled",
        )
        self.estado.tag_config("cyan", foreground=self.NEON_CYAN)
        self.estado.tag_config("green", foreground=self.NEON_GREEN)
        self.estado.tag_config("pink", foreground=self.NEON_PINK)
        self.estado.tag_config("amber", foreground=self.NEON_AMBER)

        scroll_log = tk.Scrollbar(log_container, command=self.estado.yview)
        self.estado.configure(yscrollcommand=scroll_log.set)
        self.estado.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        scroll_log.pack(side="right", fill="y")

    def _activar_dnd(self):
        self.lista_archivos.drop_target_register(DND_FILES)
        self.lista_archivos.dnd_bind("<<Drop>>", self._al_soltar_archivos)
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self._al_soltar_archivos)

    def _al_soltar_archivos(self, event):
        rutas = self.root.tk.splitlist(event.data)
        self._agregar_rutas(rutas)

    def _agregar_rutas(self, rutas):
        agregados = 0
        for ruta in rutas:
            ruta = ruta.strip()
            if os.path.isdir(ruta):
                for raiz, _, archivos in os.walk(ruta):
                    for nombre in archivos:
                        if nombre.lower().endswith(".xml"):
                            full = os.path.join(raiz, nombre)
                            if full not in self.archivos_xml:
                                self.archivos_xml.append(full)
                                self.lista_archivos.insert(tk.END, full)
                                agregados += 1
            elif os.path.isfile(ruta) and ruta.lower().endswith(".xml"):
                if ruta not in self.archivos_xml:
                    self.archivos_xml.append(ruta)
                    self.lista_archivos.insert(tk.END, ruta)
                    agregados += 1

        self.lbl_contador.config(text=f"[{len(self.archivos_xml)} ARCHIVOS]")
        if agregados:
            self._log(f"+ {agregados} archivo(s) XML añadidos a la cola.", "cyan")
        else:
            self._log("! No se detectaron archivos .xml nuevos.", "amber")

    def _log(self, mensaje, tag="cyan"):
        self.estado.configure(state="normal")
        self.estado.insert(tk.END, f"{mensaje}\n", tag)
        self.estado.see(tk.END)
        self.estado.configure(state="disabled")

    def seleccionar_archivos(self):
        archivos = filedialog.askopenfilenames(filetypes=[("Archivos XML CFDI", "*.xml")])
        if archivos:
            self._agregar_rutas(archivos)

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.carpeta_destino = carpeta
            self.lbl_carpeta.config(text=f"DESTINO : {carpeta}", fg=self.NEON_GREEN)
            self._log(f">> Carpeta destino configurada: {carpeta}", "cyan")

    def seleccionar_logotipo(self):
        ruta = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
        if ruta:
            self.logotipo_path = ruta
            self.lbl_logo.config(text=f"LOGOTIPO: {os.path.basename(ruta)}", fg=self.NEON_AMBER)
            self._log(f">> Logotipo cargado: {os.path.basename(ruta)}", "amber")

    def limpiar_lista(self):
        self.archivos_xml.clear()
        self.lista_archivos.delete(0, tk.END)
        self.lbl_contador.config(text="[0 ARCHIVOS]")
        self.barra["value"] = 0
        self._log(">> Cola de archivos reiniciada.", "pink")

    def abrir_carpeta_destino(self):
        destino = self.carpeta_destino
        if not destino and self.archivos_xml:
            destino = os.path.dirname(self.archivos_xml[0])
        if not destino:
            messagebox.showwarning("Aviso", "Primero selecciona una carpeta de destino o agrega un XML.")
            return
        try:
            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(destino)
            elif sistema == "Darwin":
                subprocess.Popen(["open", destino])
            else:
                subprocess.Popen(["xdg-open", destino])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")

    def convertir_archivos(self):
        total = len(self.archivos_xml)
        if total == 0:
            messagebox.showwarning("Cola vacía", "Arrastra o agrega al menos un archivo XML.")
            return

        self.barra["maximum"] = total
        self.barra["value"] = 0
        exitos = 0
        errores = 0

        self._log(f"\n=== INICIANDO LOTE: {total} CFDI(s) ===", "cyan")
        for path in self.archivos_xml:
            nombre_base = os.path.splitext(os.path.basename(path))[0] + ".pdf"
            destino_dir = self.carpeta_destino or os.path.dirname(path)
            salida_pdf = os.path.join(destino_dir, nombre_base)

            try:
                datos = parse_cfdi(path)
                if "error" in datos:
                    raise RuntimeError(datos["error"])
                generar_pdf(datos, salida_pdf, self.logotipo_path)
                self._log(f"[OK]  {nombre_base}", "green")
                exitos += 1
            except Exception as e:
                self._log(f"[ERR] {os.path.basename(path)} -> {e}", "pink")
                errores += 1

            self.barra["value"] += 1
            self.root.update_idletasks()

        self._log(f"=== FINALIZADO | Éxitos: {exitos} | Errores: {errores} ===", "amber")


if __name__ == "__main__":
    ventana = TkinterDnD.Tk() if DND_DISPONIBLE else tk.Tk()
    app = CyberCFDIApp(ventana)
    ventana.mainloop()
