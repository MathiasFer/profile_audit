import os
from fpdf import FPDF

class PDFReport(FPDF):
    """
    Clase para la generacion de reportes PDF personalizados.
    """
    def header(self):
        """Define el encabezado de las paginas del reporte."""
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, self.report_title, 0, 1, 'C')
        self.ln(5)

    def footer(self):
        """Define el pie de pagina de las paginas del reporte."""
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def __init__(self, title):
        """
        Inicializa el reporte con un titulo.
        
        Args:
            title (str): Titulo del reporte.
        """
        super().__init__()
        self.report_title = title
        self.set_auto_page_break(auto=True, margin=15)

    def add_plot(self, image_path):
        """
        Agrega un grafico (imagen) al reporte.
        
        Args:
            image_path (str): Ruta al archivo de imagen.
        """
        if os.path.exists(image_path):
            self.image(image_path, x=10, w=190)
            self.ln(10)

    def add_analysis(self, text):
        """
        Agrega el texto del analisis, limpiando caracteres no compatibles.
        
        Args:
            text (str): Texto del analisis generado por la IA.
        """
        self.set_font('Arial', '', 12)
        # Limpiar texto de caracteres especiales para FPDF estandar
        clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
        self.multi_cell(0, 10, clean_text)

def generate_pdf_report(filename, title, plot_path, analysis_text):
    """
    Funcion de utilidad para generar un reporte PDF completo.
    
    Args:
        filename (str): Nombre del archivo PDF de salida.
        title (str): Titulo principal del reporte.
        plot_path (str): Ruta al grafico generado.
        analysis_text (str): Texto del analisis detallado.
    """
    pdf = PDFReport(title)
    pdf.add_page()
    pdf.add_plot(plot_path)
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Analisis de la IA (Groq):", 0, 1)
    pdf.ln(5)
    pdf.add_analysis(analysis_text)
    pdf.output(filename)
    print(f"Reporte PDF generado: {filename}")
