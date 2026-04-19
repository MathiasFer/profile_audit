from playwright.sync_api import sync_playwright

def test_sesion(auth_file="auth.json"):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=auth_file)
        page = context.new_page()

        page.goto("https://www.instagram.com/", wait_until="domcontentloaded")

        page.wait_for_timeout(5000)

        # Verificamos si aparece el input de login
        login_input = page.locator("input[name='username']")

        if login_input.count() > 0:
            print("❌ NO estás logueado (falló la sesión)")
        else:
            print("✅ Sesión activa, estás dentro")

        browser.close()

if __name__ == "__main__":
    test_sesion()