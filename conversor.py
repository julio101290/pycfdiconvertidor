
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import xml.etree.ElementTree as ET
import qrcode
from PIL import Image
import io
import platform
import subprocess

carpeta_destino = ""
logotipo_path = ""

def parse_cfdi(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        namespaces = {
            'cfdi': 'http://www.sat.gob.mx/cfd/4',
            'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'
        }

        emisor = root.find('cfdi:Emisor', namespaces)
        receptor = root.find('cfdi:Receptor', namespaces)
        conceptos = root.findall('.//cfdi:Concepto', namespaces)
        timbre = root.find('.//tfd:TimbreFiscalDigital', namespaces)

        return {
            "Emisor": emisor.attrib if emisor is not None else {},
            "Receptor": receptor.attrib if receptor is not None else {},
            "Conceptos": [c.attrib for c in conceptos],
            "Timbre": timbre.attrib if timbre is not None else {},
            "Comprobante": root.attrib
        }
    except Exception as e:
        return {"error": str(e)}

def generar_pdf(datos, salida_pdf, logotipo_path=None):
    c = canvas.Canvas(salida_pdf, pagesize=letter)
    width, height = letter
    y = height - 30

    if logotipo_path and os.path.isfile(logotipo_path):
        try:
            logo = ImageReader(logotipo_path)
            c.drawImage(logo, 30, y - 60, width=100, height=50, preserveAspectRatio=True)
        except:
            pass

    uuid = datos.get("Timbre", {}).get("UUID", "UUID no disponible")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(150, y - 20, f"UUID: {uuid}")

    def draw_table(title, data, start_y):
        y = start_y
        c.setFont("Helvetica-Bold", 10)
        c.drawString(30, y, title)
        y -= 15
        c.setFont("Helvetica", 8)
        for key, value in data.items():
            if y < 100:
                c.showPage()
                y = height - 50
            text = f"{key}: {value}"
            lines = split_text(text, 90)
            for line in lines:
                c.drawString(40, y, line)
                y -= 12
        return y

    def split_text(text, max_chars):
        return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

    y = draw_table("Datos del Emisor", datos.get("Emisor", {}), y - 70)
    y = draw_table("Datos del Receptor", datos.get("Receptor", {}), y - 20)

    c.setFont("Helvetica-Bold", 10)
    c.drawString(30, y - 10, "Conceptos:")
    y -= 25
    c.setFont("Helvetica", 8)
    for concepto in datos.get("Conceptos", []):
        if y < 100:
            c.showPage()
            y = height - 50
        desc = concepto.get("Descripcion", "")
        clave = concepto.get("ClaveProdServ", "")
        clave_uni = concepto.get("ClaveUnidad", "")
        cantidad = concepto.get("Cantidad", "")
        unidad = concepto.get("Unidad", "")
        valor = concepto.get("ValorUnitario", "")
        importe = concepto.get("Importe", "")
        line = f"{cantidad} {unidad} | {clave} / {clave_uni} | {desc} | ${valor} = ${importe}"
        lines = split_text(line, 100)
        for l in lines:
            c.drawString(40, y, l)
            y -= 12

    y -= 10
    c.setFont("Helvetica-Bold", 9)
    for k, v in datos.get("Timbre", {}).items():
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(30, y, f"{k}: {v}")
        y -= 12

    qr_data = f"UUID: {uuid}"
    qr = qrcode.make(qr_data)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)
    qr_image = ImageReader(buffer)
    c.drawImage(qr_image, width - 120, 40, 80, 80)

    c.save()

def seleccionar_archivos():
    archivos = filedialog.askopenfilenames(filetypes=[("Archivos XML", "*.xml")])
    if archivos:
        lista_archivos.delete(0, tk.END)
        for archivo in archivos:
            lista_archivos.insert(tk.END, archivo)

def seleccionar_carpeta():
    global carpeta_destino
    carpeta_destino = filedialog.askdirectory()
    if carpeta_destino:
        etiqueta_carpeta.config(text=carpeta_destino)

def seleccionar_logotipo():
    global logotipo_path
    logotipo_path = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png;*.jpg;*.jpeg")])
    if logotipo_path:
        etiqueta_logo.config(text=os.path.basename(logotipo_path))

def abrir_carpeta_destino():
    if carpeta_destino:
        try:
            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(carpeta_destino)
            elif sistema == "Darwin":
                subprocess.Popen(["open", carpeta_destino])
            else:
                subprocess.Popen(["xdg-open", carpeta_destino])
        except Exception as e:
            messagebox.showerror("Error", "No se pudo abrir la carpeta:{str(e)}")
    else:
        messagebox.showwarning("Aviso", "Primero selecciona una carpeta de destino.")

def convertir_archivos():
    total = lista_archivos.size()
    barra["maximum"] = total
    barra["value"] = 0
    for i in range(total):
        path = lista_archivos.get(i)
        try:
            datos = parse_cfdi(path)
            if "error" in datos:
                raise Exception(datos["error"])
            nombre = os.path.splitext(os.path.basename(path))[0] + ".pdf"
            salida = os.path.join(carpeta_destino, nombre)
            generar_pdf(datos, salida, logotipo_path)
            estado.insert(tk.END, f"{nombre}: Éxito\n")
        except Exception as e:
            estado.insert(tk.END, f"{os.path.basename(path)}: Error - {str(e)}\n")
        barra["value"] += 1
        ventana.update_idletasks()

ventana = tk.Tk()
ventana.title("Convertidor CFDI 4.0 a PDF")
ventana.geometry("700x500")

frame = tk.Frame(ventana)
frame.pack(pady=10)

tk.Button(frame, text="Agregar Archivos XML", command=seleccionar_archivos).grid(row=0, column=0, padx=5)
tk.Button(frame, text="Seleccionar Carpeta Destino", command=seleccionar_carpeta).grid(row=0, column=1, padx=5)
tk.Button(frame, text="Agregar Logotipo", command=seleccionar_logotipo).grid(row=0, column=2, padx=5)
tk.Button(frame, text="Abrir Carpeta de Destino", command=abrir_carpeta_destino).grid(row=0, column=3, padx=5)

etiqueta_carpeta = tk.Label(ventana, text="Carpeta destino no seleccionada")
etiqueta_carpeta.pack()

etiqueta_logo = tk.Label(ventana, text="Sin logotipo")
etiqueta_logo.pack()

lista_archivos = tk.Listbox(ventana, width=80, height=6)
lista_archivos.pack(pady=10)

tk.Button(ventana, text="Convertir a PDF", command=convertir_archivos).pack()

barra = ttk.Progressbar(ventana, orient="horizontal", length=600, mode="determinate")
barra.pack(pady=5)

estado = tk.Text(ventana, height=10, width=90)
estado.pack()

ventana.mainloop()
