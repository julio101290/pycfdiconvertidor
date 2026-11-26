# 🧾 Convertidor CFDI 4.0 a PDF

Convierte tus archivos XML CFDI 4.0 del SAT a PDF de forma masiva, rápida y con una interfaz gráfica amigable. Este proyecto en Python te permite visualizar todos los datos fiscales importantes, incluyendo el UUID, el emisor, receptor, productos, claves SAT, unidades de medida, y más.



---

## ✨ Características

- ✅ Convierte múltiples XML CFDI 4.0 a archivos PDF
- ✅ Incluye logotipo personalizado
- ✅ Muestra todos los datos del Emisor, Receptor y Timbre Fiscal Digital
- ✅ Clave del SAT y Unidad de Medida visible por producto
- ✅ Barra de progreso de conversión
- ✅ Botón para abrir la carpeta de destino
- ✅ Continuación automática si un archivo falla

---

## 🖥️ Interfaz Gráfica

- Carga múltiples archivos XML
- Selecciona carpeta destino
- Agrega logotipo empresarial
- Sigue el estado de cada archivo

---

## 🐍 Requisitos

- Python 3.8 o superior

### 📦 Instalación de dependencias

```bash
pip install reportlab qrcode[pil] Pillow
```

## 🚀 Cómo usarlo
  Clona este repositorio:

```bash
  git clone https://github.com/tuusuario/convertidor-cfdi-pdf.git
  cd convertidor-cfdi-pdf

```
## Ejecuta el script:

```bash
python convertidor_cfdi_pdf.py
```

## Usa la interfaz para:

Agregar tus XML

Seleccionar carpeta destino

Agregar logotipo

Presionar "Convertir a PDF"

## 📂 Archivos Generados
Archivos .pdf con los datos fiscales

Los archivos van a la carpeta de destino elegida

## 🔐 Seguridad
Este convertidor funciona totalmente local, lo que garantiza la privacidad de tus documentos fiscales. No hay conexión a internet ni envío de datos.

## 📸 Capturas (opcional)
<img width="882" height="688" alt="image" src="https://github.com/user-attachments/assets/b1915e79-84b9-4f11-b6df-9065116e5869" />



## 🤝 Contribuciones
¿Quieres mejorar el formato, agregar timbre digital con QR, o generar ejecutables para Windows/Linux? ¡Contribuye o abre un issue!

## 📄 Licencia
MIT License
