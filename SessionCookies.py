from playwright.sync_api import sync_playwright

class InstagramSessionManager:
    """
    Gestiona la sesion de Instagram para permitir el scraping sin bloqueos constantes,
    guardando el estado de autenticacion localmente.
    """
    def __init__(self, auth_file="auth.json"):
        """
        Inicializa el gestor de sesion.
        
        Args:
            auth_file (str): Nombre del archivo donde se guardara la sesion.
        """
        self.auth_file = auth_file

    def guardar_sesion(self):
        """
        Abre el navegador para que el usuario inicie sesion manualmente y guarda el estado.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            print("Abre Instagram y logueate manualmente...")
            page.goto("https://www.instagram.com/", timeout=30000)

            # Tiempo para login manual (30 segundos)
            # Se puede incrementar si el usuario tarda mas.
            print("Esperando 30 segundos para que completes el login...")
            page.wait_for_timeout(30000)

            # Guardar cookies y localStorage
            context.storage_state(path=self.auth_file)
            print(f"Sesion guardada correctamente en {self.auth_file}")

            browser.close()

if __name__ == "__main__":
    manager = InstagramSessionManager()
    manager.guardar_sesion()
