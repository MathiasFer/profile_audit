import os
from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, self.report_title, 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def __init__(self, title):
        super().__init__()
        self.report_title = title
        self.set_auto_page_break(auto=True, margin=15)

    def add_plot(self, image_path):
        if os.path.exists(image_path):
            # Centrar la imagen
            self.image(image_path, x=10, w=190)
            self.ln(10)

    def add_analysis(self, text):
        self.set_font('Arial', '', 12)
        # Limpiar texto de emojis problemáticos para FPDF estándar si es necesario
        # Aunque fpdf2 soporta fuentes Unicode, para simplificar usamos Arial estándar
        clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
        self.multi_cell(0, 10, clean_text)

def generate_pdf_report(filename, title, plot_path, analysis_text):
    pdf = PDFReport(title)
    pdf.add_page()
    pdf.add_plot(plot_path)
    pdf.add_page() # El análisis en una nueva página para mejor lectura
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Análisis de la IA (Groq):", 0, 1)
    pdf.ln(5)
    pdf.add_analysis(analysis_text)
    pdf.output(filename)
    print(f"✅ Reporte PDF generado: {filename}")
