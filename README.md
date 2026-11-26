<div align="center">

<!-- BANNER ANIMADO RETRO TERMINAL -->
<a href="https://github.com/julio101290/pycfdiconvertidor">
  <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=700&size=22&duration=3000&pause=1000&color=00F3FF&background=090A10&center=true&vCenter=true&width=760&height=65&lines=%5B+CYBER_CFDI+v4.0+%5D+%2F%2F+SAT+XML+TO+PDF+ENGINE;CONVIERTE+CIENTOS+DE+FACTURAS+XML+EN+SEGUNDOS;100%25+LOCAL+%7C+DRAG+%26+DROP+%7C+OPEN+SOURCE" alt="CYBER_CFDI v4.0 Banner" />
</a>

```text
 ██████╗██╗   ██╗██████╗ ███████╗██████╗       ██████╗███████╗██████╗ ██╗
██╔════╝╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗     ██╔════╝██╔════╝██╔══██╗██║
██║      ╚████╔╝ ██████╔╝█████╗  ██████╔╝     ██║     █████╗  ██║  ██║██║
██║       ╚██╔╝  ██╔══██╗██╔══╝  ██╔══██╗     ██║     ██╔══╝  ██║  ██║██║
╚██████╗   ██║   ██████╔╝███████╗██║  ██║     ╚██████╗██║     ██████╔╝██║
 ╚═════╝   ╚═╝   ╚═════╝ ╚══════╝╚═╝  ╚═╝      ╚═════╝╚═╝     ╚═════╝ ╚═╝
                 >> CONVERTIDOR MASIVO CFDI 4.0 / 3.3 A PDF <<
```

<p>
  <img src="https://img.shields.io/badge/PYTHON-3.8%2B-00F3FF?style=for-the-badge&logo=python&logoColor=00F3FF&labelColor=090A10" alt="Python 3.8+"/>
  <img src="https://img.shields.io/badge/SAT_MÉXICO-CFDI_4.0_%26_3.3-FF007F?style=for-the-badge&labelColor=090A10" alt="CFDI 4.0 & 3.3"/>
  <img src="https://img.shields.io/badge/PDF_ENGINE-REPORTLAB-39FF14?style=for-the-badge&labelColor=090A10" alt="ReportLab"/>
  <img src="https://img.shields.io/badge/UI-RETRO_CYBERPUNK-FFB800?style=for-the-badge&labelColor=090A10" alt="Retro Cyberpunk UI"/>
  <img src="https://img.shields.io/badge/OS-LINUX_%7C_WIN_%7C_MAC-00F3FF?style=for-the-badge&labelColor=090A10" alt="Multiplataforma"/>
</p>

<p>
  <a href="https://github.com/julio101290/pycfdiconvertidor/stargazers"><img src="https://img.shields.io/github/stars/julio101290/pycfdiconvertidor?style=flat-square&color=FF007F&labelColor=090A10" alt="GitHub Stars"/></a>
  <a href="https://github.com/julio101290/pycfdiconvertidor/network/members"><img src="https://img.shields.io/github/forks/julio101290/pycfdiconvertidor?style=flat-square&color=00F3FF&labelColor=090A10" alt="GitHub Forks"/></a>
  <a href="https://github.com/julio101290/pycfdiconvertidor/issues"><img src="https://img.shields.io/github/issues/julio101290/pycfdiconvertidor?style=flat-square&color=FFB800&labelColor=090A10" alt="GitHub Issues"/></a>
</p>

**Aplicación de escritorio Open Source en Python para convertir lotes masivos de archivos XML (CFDI 4.0 y 3.3 del SAT) a representaciones impresas en PDF con QR oficial verificable, soporte Drag & Drop y una interfaz Retro Cyberpunk.**

</div>

---

## ⚡ `// 01. ¿POR QUÉ USAR PYCFDICONVERTIDOR?`

Olvídate de subir tus facturas a convertidores web llenos de publicidad, límites diarios o riesgos de privacidad. **`pycfdiconvertidor`** ejecuta todo **100% en local** sobre tu equipo:

| Módulo | Capacidad |
| :--- | :--- |
| **🖱️ Drag & Drop Recursivo** | Arrastra archivos `.xml` individuales o **carpetas completas con subcarpetas** directamente a la ventana. Filtra automáticamente y evita duplicados. |
| **🧾 PDF Profesional Estilo SAT** | Generado con **ReportLab Platypus**: limpio, estructurado en tablas, con saltos de página inteligentes y numeración `Página X de Y`. |
| **📱 Código QR Oficial del SAT** | Construye automáticamente la URL oficial de verificación (`verificacfdi.facturaelectronica.sat.gob.mx`) con UUID, RFC Emisor/Receptor, Total y últimos 8 dígitos del sello. |
| **📚 Catálogos SAT Integrados** | Decodifica automáticamente claves de Tipo de Comprobante, Forma/Método de Pago, Régimen Fiscal, Uso de CFDI, Exportación, Objeto de Impuesto e Impuestos (IVA/ISR/IEPS). |
| **🎨 Personalización con Logo** | Agrega el logotipo de tu empresa o despacho (`PNG`/`JPG`) escalado proporcionalmente en el encabezado. |
| **🌆 Consola Retro Cyberpunk** | Interfaz oscura neón con barra de progreso en tiempo real y terminal integrada con logs por color (`[OK]`, `[ERR]`, avisos). |
| **🔒 Privacidad Absoluta** | Cero nube, cero telemetría, cero marcas de agua. Funciona totalmente sin conexión a internet. |

---

## 📸 `// 02. VISTAZO EN ACCIÓN`

<div align="center">
  <table>
    <tr>
      <td align="center"><b>🖥️ Interfaz Retro Cyberpunk (<code>conversor.py</code>)</b></td>
      <td align="center"><b>📄 Representación Impresa Estilo SAT</b></td>
    </tr>
    <tr>
      <td><<img width="874" height="695" alt="image" src="https://github.com/user-attachments/assets/7d762797-0fe0-4a56-b7bc-92cc93ff2eb4" />
</td>
      <td><img width="783" height="953" alt="image" src="https://github.com/user-attachments/assets/10b496e9-622f-4f0a-948b-dad179d148f9" />
</td>
    </tr>
  </table>
</div>

> *💡 Nota: Guarda tus capturas como `assets/interfaz.png` y `assets/ejemplo_pdf.png` dentro del repositorio para que se muestren automáticamente en esta tabla.*

---

## 🧾 `// 03. ESTRUCTURA DEL PDF GENERADO`

Cada comprobante generado incluye las secciones clave de una representación impresa oficial:

```text
┌──────────────────────────────────────────────────────────────────────┐
│  [ LOGO OPCIONAL ]  │  UUID: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX    │
│  [   CÓDIGO QR   ]  │  Tipo, Serie, Folio, Lugar, Fecha, Pago        │
│  [ VERIFICACIÓN  ]  │  Certificado Emisor/SAT, RFC PAC, Exportación  │
├─────────────────────────────────┬────────────────────────────────────┤
│  EMISOR                         │  RECEPTOR                          │
│  Razón Social, RFC, Régimen     │  Nombre, RFC, Uso CFDI, CP, Rég.   │
├─────────────────────────────────┴────────────────────────────────────┤
│  CONCEPTOS (Concepto 1 de N)                                         │
│  Descripción, Clave SAT, Unidad, ObjetoImp, Cantidad, P.U., Importe  │
│  └─ Desglose de Traslados y Retenciones por partida                  │
├──────────────────────────────────────────────────────────────────────┤
│  RESUMEN DE IMPUESTOS  &  TABLA DE TOTALES (Moneda, TC, Sub, Total)  │
├──────────────────────────────────────────────────────────────────────┤
│  DATOS FISCALES                                                      │
│  Sello Digital CFDI | Sello SAT | Cadena Original TFD | URL SAT      │
└──────────────────────────────────────────────────────────────────────┘
   Representación impresa de un CFDI versión 4.0  —  Página 1 de 1
```

---

## ⚙️ `// 04. INSTALACIÓN RÁPIDA`

### Requisitos previos
* **Python 3.8+** con `tkinter` habilitado. *(En algunas distros Linux como Ubuntu/Debian: `sudo apt install python3-tk`; en Arch/CachyOS: `sudo pacman -S tk`)*.

### 1. Clona el repositorio
```bash
git clone https://github.com/julio101290/pycfdiconvertidor.git
cd pycfdiconvertidor
```

### 2. Crea y activa un entorno virtual (recomendado)
```bash
python -m venv venv

# En Linux / macOS:
source venv/bin/activate

# En Windows (PowerShell / CMD):
venv\Scripts\activate
```

### 3. Instala las dependencias
```bash
pip install reportlab qrcode pillow tkinterdnd2
```
> *Nota: Si `tkinterdnd2` no está instalado en tu sistema, `conversor.py` iniciará normalmente en modo clásico usando el botón `+ AGREGAR XML`.*

### 4. Ejecuta el motor
```bash
python conversor.py
```

---

## 🕹️ `// 05. MODO DE USO`

1. **Carga tus XML:** Arrastra y suelta archivos `.xml` o carpetas completas dentro de la cola (o usa **`+ AGREGAR XML`**).
2. **Configura (opcional):**
   * Pulsa **`CARPETA SALIDA`** para definir dónde guardar los PDFs *(si lo dejas vacío, cada PDF se guarda junto a su XML original)*.
   * Pulsa **`LOGOTIPO`** para incrustar tu logo en el encabezado.
3. **Ejecuta:** Da clic en **`[ >> EJECUTAR CONVERSIÓN A PDF << ]`**, monitorea el avance en la terminal inferior y abre tus archivos con **`ABRIR SALIDA`**.

---

## 🗺️ `// 06. ROADMAP`

- [x] Parser XML compatible con CFDI 4.0 y 3.3
- [x] Interfaz Retro Cyberpunk con consola de logs a color
- [x] Soporte Drag & Drop recursivo para archivos y carpetas
- [x] Generación de PDF tabular estilo SAT con QR verificable y pie de página `Página X de Y`
- [ ] Soporte visual dedicado para **Complemento de Pagos 2.0**
- [ ] Soporte para recibos de **Nómina 1.2**
- [ ] Integración de secciones para **Carta Porte**
- [ ] Exportación del resumen del lote a **Excel (`.xlsx`) / CSV**

---

## 🤝 `// 07. CONTRIBUIR`

¡Las contribuciones, reportes de bugs y Pull Requests son bienvenidos!
1. Haz un **Fork** del proyecto.
2. Crea tu rama (`git checkout -b feature/nueva-mejora`).
3. Haz commit de tus cambios (`git commit -m 'Agrega soporte para Complemento X'`).
4. Haz push a tu rama (`git push origin feature/nueva-mejora`).
5. Abre un **Pull Request**.

---

## 📡 `// 08. COMUNIDAD Y ENLACES OFICIALES`

Desarrollado por **Julio César Leyva Rodríguez (Cesar Systems)**. Si este proyecto te ahorró horas de trabajo, ¡deja una ⭐ en el repositorio y pásate por la comunidad!

<div align="center">
  <a href="https://cesarsystems.com.mx/"><img src="https://img.shields.io/badge/WEB-CESARSYSTEMS.COM.MX-00F3FF?style=for-the-badge&logo=googlechrome&logoColor=00F3FF&labelColor=090A10" alt="Web"/></a>
  <a href="https://www.youtube.com/@cesarsystems"><img src="https://img.shields.io/badge/YOUTUBE-@CESARSYSTEMS-FF007F?style=for-the-badge&logo=youtube&logoColor=FF007F&labelColor=090A10" alt="YouTube CesarSystems"/></a>
  <a href="https://www.youtube.com/@rasec555"><img src="https://img.shields.io/badge/YOUTUBE-@RASEC555-FF007F?style=for-the-badge&logo=youtube&logoColor=FF007F&labelColor=090A10" alt="YouTube rasec555"/></a>
  <a href="https://t.me/CesarSystems"><img src="https://img.shields.io/badge/TELEGRAM-COMUNIDAD-00F3FF?style=for-the-badge&logo=telegram&logoColor=00F3FF&labelColor=090A10" alt="Telegram"/></a>
  <a href="https://patreon.com/cesarsystems"><img src="https://img.shields.io/badge/PATREON-APOYAR_PROYECTO-FFB800?style=for-the-badge&logo=patreon&logoColor=FFB800&labelColor=090A10" alt="Patreon"/></a>
  <a href="https://github.com/julio101290"><img src="https://img.shields.io/badge/GITHUB-JULIO101290-39FF14?style=for-the-badge&logo=github&logoColor=39FF14&labelColor=090A10" alt="GitHub"/></a>
</div>

---

<div align="center">
  <sub>Hecho con 🐍 Python y café | Licencia MIT — Libre para usar, modificar y compartir</sub>
</div>
