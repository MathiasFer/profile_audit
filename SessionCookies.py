from playwright.sync_api import sync_playwright

class InstagramSessionManager:
    def __init__(self, auth_file="auth.json"):
        self.auth_file = auth_file

    def guardar_sesion(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            print("👉 Abre Instagram y loguéate manualmente...")
            page.goto("https://www.instagram.com/", timeout=30000)

            # Tiempo para login manual (ajústalo)
            page.wait_for_timeout(30000)

            # Guardar cookies + localStorage
            context.storage_state(path=self.auth_file)
            print(f"✅ Sesión guardada en {self.auth_file}")

            browser.close()

if __name__ == "__main__":
    manager = InstagramSessionManager()
    manager.guardar_sesion()