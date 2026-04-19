import os
import json
from ReactionsScraper import InstagramScraper
from analizador_benford import AuditorInstagram
from analizador_engagement import AnalizadorEngagementPro

class OrquestadorAuditoria:
    """
    Clase principal que coordina el proceso completo: 
    Scraping de datos, Auditoria Benford y Analisis de Engagement.
    """
    def __init__(self, username):
        """
        Inicializa el orquestador con el nombre de usuario a analizar.
        
        Args:
            username (str): Nombre del perfil de Instagram (ej. 'midu.dev').
        """
        self.username = username
        self.profile_url = f"https://www.instagram.com/{username}/"
        self.data_file = f"data_{username}.json"
        
    def ejecutar_proceso_completo(self):
        """
        Ejecuta todas las fases de la auditoria de forma secuencial.
        """
        print(f"--- Iniciando Auditoria Completa para: @{self.username} ---")
        
        # FASE 1: Scraping de datos
        print("\n[FASE 1]: Extraccion de datos desde Instagram...")
        scraper = InstagramScraper()
        try:
            datos = scraper.scrape_account(self.profile_url)
            if not datos:
                print("Error: No se pudieron obtener datos del perfil. Verifica la sesion.")
                return
            
            scraper.save_to_json(datos, self.data_file)
        except Exception as e:
            print(f"Error durante el scraping: {e}")
            return

        # FASE 2: Analisis de Benford
        print("\n[FASE 2]: Ejecutando Auditoria de Benford...")
        try:
            auditor_benford = AuditorInstagram(self.data_file)
            auditor_benford.ejecutar_auditoria(self.username)
        except Exception as e:
            print(f"Error en analisis Benford: {e}")

        # FASE 3: Analisis de Engagement
        print("\n[FASE 3]: Ejecutando Analisis de Engagement...")
        try:
            analizador_engagement = AnalizadorEngagementPro(self.data_file)
            analizador_engagement.ejecutar_analisis(self.username)
        except Exception as e:
            print(f"Error en analisis de engagement: {e}")

        print(f"\n--- Auditoria finalizada con exito ---")
        print(f"Los reportes PDF han sido generados para el usuario {self.username}.")
        
        # Opcional: Limpiar archivo de datos temporal
        # os.remove(self.data_file)

if __name__ == "__main__":
    # Puedes cambiar el usuario aqui o pedirlo por consola
    target_user = input("Introduce el nombre de usuario de Instagram a analizar: ").strip()
    
    if target_user:
        orquestador = OrquestadorAuditoria(target_user)
        orquestador.ejecutar_proceso_completo()
    else:
        print("Nombre de usuario no valido.")
