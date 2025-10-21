"""
Servicio para generación de PDFs de cotizaciones
"""
import os
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class PDFService:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
        # Crear directorio para PDFs si no existe
        self.pdf_dir = "generated_pdfs"
        os.makedirs(self.pdf_dir, exist_ok=True)

    def setup_custom_styles(self):
        """Configurar estilos personalizados para el PDF"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=self.styles['Normal'],
            fontSize=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c3e50')
        ))

    async def generate_quote_pdf(self, quote_data: Dict[str, Any]) -> str:
        """
        Generar PDF de cotización
        
        Args:
            quote_data: Diccionario con datos de la cotización
            
        Returns:
            str: Ruta al archivo PDF generado
        """
        try:
            # Generar nombre único para el PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            quote_number = quote_data.get("quote_number", f"Q{timestamp}")
            filename = f"cotizacion_{quote_number}_{timestamp}.pdf"
            filepath = os.path.join(self.pdf_dir, filename)
            
            logger.info("Generating PDF", filename=filename)
            
            # Crear documento PDF
            doc = SimpleDocTemplate(
                filepath,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Construir contenido del PDF
            story = []
            
            # Header de la empresa
            story.extend(self._build_company_header())
            
            # Información de la cotización
            story.extend(self._build_quote_info(quote_data))
            
            # Tabla de productos
            story.extend(self._build_products_table(quote_data.get("items", [])))
            
            # Totales
            story.extend(self._build_totals_section(quote_data))
            
            # Footer con términos y condiciones
            story.extend(self._build_footer())
            
            # Generar PDF
            doc.build(story)
            
            logger.info("PDF generated successfully", filepath=filepath)
            return filepath
            
        except Exception as e:
            logger.error("Error generating PDF", error=str(e))
            raise

    def _build_company_header(self) -> List:
        """Construir header de la empresa"""
        content = []
        
        # Logo y nombre de la empresa (por ahora solo texto)
        company_info = Paragraph(
            "<b>COMPUTEL</b><br/>Papelería y Artículos de Oficina<br/>📞 (55) 1234-5678 | 📧 info@computel.com",
            self.styles['CompanyHeader']
        )
        content.append(company_info)
        content.append(Spacer(1, 20))
        
        # Título del documento
        title = Paragraph("COTIZACIÓN", self.styles['CustomTitle'])
        content.append(title)
        content.append(Spacer(1, 20))
        
        return content

    def _build_quote_info(self, quote_data: Dict) -> List:
        """Construir sección de información de la cotización"""
        content = []
        
        # Información básica en tabla
        quote_info_data = [
            ['Cotización No.:', quote_data.get("quote_number", "N/A")],
            ['Fecha:', datetime.now().strftime("%d/%m/%Y")],
            ['Válida hasta:', quote_data.get("valid_until", "30 días")],
            ['Cliente:', quote_data.get("client_name", "Cliente")],
        ]
        
        quote_info_table = Table(quote_info_data, colWidths=[2*inch, 3*inch])
        quote_info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        content.append(quote_info_table)
        content.append(Spacer(1, 30))
        
        return content

    def _build_products_table(self, items: List[Dict]) -> List:
        """Construir tabla de productos"""
        content = []
        
        # Header de la sección
        section_header = Paragraph("PRODUCTOS COTIZADOS", self.styles['SectionHeader'])
        content.append(section_header)
        
        # Datos de la tabla
        table_data = [
            ['Cantidad', 'Descripción', 'Precio Unit.', 'Total']
        ]
        
        for item in items:
            table_data.append([
                str(item.get("quantity", 1)),
                item.get("product_name", "Producto"),
                f"${item.get('unit_price', 0):.2f}",
                f"${item.get('total_price', 0):.2f}"
            ])
        
        # Crear tabla
        products_table = Table(table_data, colWidths=[1*inch, 3.5*inch, 1.25*inch, 1.25*inch])
        products_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Descripción alineada a la izquierda
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'), # Precios alineados a la derecha
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#34495e')),
            
            # Padding
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            
            # Filas alternadas
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        content.append(products_table)
        content.append(Spacer(1, 30))
        
        return content

    def _build_totals_section(self, quote_data: Dict) -> List:
        """Construir sección de totales"""
        content = []
        
        # Datos de totales
        subtotal = quote_data.get("subtotal", 0)
        tax_rate = quote_data.get("tax_rate", 16)
        tax_amount = quote_data.get("tax_amount", 0)
        total = quote_data.get("total", 0)
        
        totals_data = [
            ['', '', 'Subtotal:', f"${subtotal:.2f}"],
            ['', '', f'IVA ({tax_rate}%):', f"${tax_amount:.2f}"],
            ['', '', '', ''],  # Línea en blanco
            ['', '', 'TOTAL:', f"${total:.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[1*inch, 3.5*inch, 1.25*inch, 1.25*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (2, 0), (2, -2), 'Helvetica'),
            ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (2, 0), (-1, -2), 10),
            ('FONTSIZE', (2, -1), (-1, -1), 12),
            ('LINEABOVE', (2, -1), (-1, -1), 2, colors.black),
            ('BACKGROUND', (2, -1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        
        content.append(totals_table)
        content.append(Spacer(1, 40))
        
        return content

    def _build_footer(self) -> List:
        """Construir footer con términos y condiciones"""
        content = []
        
        # Términos y condiciones
        terms_title = Paragraph("TÉRMINOS Y CONDICIONES", self.styles['SectionHeader'])
        content.append(terms_title)
        
        terms_text = """
        • Los precios están expresados en pesos mexicanos e incluyen IVA.<br/>
        • Esta cotización tiene una vigencia de 30 días a partir de la fecha de emisión.<br/>
        • Los precios pueden variar sin previo aviso.<br/>
        • Tiempo de entrega: 3-5 días hábiles una vez confirmado el pedido.<br/>
        • Forma de pago: Efectivo, transferencia bancaria o tarjeta de crédito.<br/>
        • Para realizar su pedido, favor de confirmar por WhatsApp o teléfono.
        """
        
        terms_paragraph = Paragraph(terms_text, self.styles['Normal'])
        content.append(terms_paragraph)
        content.append(Spacer(1, 20))
        
        # Contacto
        contact_text = """
        <b>¡Gracias por su preferencia!</b><br/>
        Para cualquier duda o para confirmar su pedido, contáctenos:<br/>
        📞 Teléfono: (55) 1234-5678<br/>
        📱 WhatsApp: (55) 1234-5678<br/>
        📧 Email: ventas@computel.com
        """
        
        contact_paragraph = Paragraph(contact_text, self.styles['Normal'])
        content.append(contact_paragraph)
        
        return content


# Instancia global del servicio
pdf_service = PDFService()