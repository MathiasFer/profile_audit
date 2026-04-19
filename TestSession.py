from playwright.sync_api import sync_playwright

def test_sesion(auth_file="auth.json"):
    """
    Verifica si el archivo de sesion actual permite entrar a Instagram sin loguearse.
    
    Args:
        auth_file (str): Ruta al archivo de sesion JSON.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=auth_file)
        page = context.new_page()

        print("Navegando a Instagram para verificar sesion...")
        page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        # Verificamos si aparece el input de login para determinar si la sesion es valida
        login_input = page.locator("input[name='username']")

        if login_input.count() > 0:
            print("Error: NO estas logueado (la sesion ha expirado o no es valida)")
        else:
            print("Exito: Sesion activa, estas dentro de la plataforma")

        browser.close()

if __name__ == "__main__":
    test_sesion()
