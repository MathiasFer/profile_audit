import json
from playwright.sync_api import sync_playwright

class InstagramScraper:
    """
    Clase para extraer datos de publicaciones (posts y reels) de perfiles de Instagram
    utilizando Playwright para interceptar respuestas de la API.
    """
    def __init__(self, auth_file="auth.json"):
        """
        Inicializa el scraper con el archivo de sesion.
        
        Args:
            auth_file (str): Ruta al archivo JSON con las cookies y estado de sesion.
        """
        self.auth_file = auth_file
        self.data = {}  # Dataset unico por shortcode
        self._attached_pages = set()

    def handle_response(self, response):
        """
        Manejador de respuestas para interceptar y procesar datos JSON de Instagram.
        
        Args:
            response: Objeto de respuesta de Playwright.
        """
        content_type = response.headers.get("content-type", "").lower()

        if "json" not in content_type and "graphql" not in response.url:
            return

        try:
            data = response.json()

            # Procesamiento de POSTS (feed principal)
            if "data" in data and "xdt_api__v1__feed__user_timeline_graphql_connection" in data["data"]:
                edges = data["data"]["xdt_api__v1__feed__user_timeline_graphql_connection"].get("edges", [])

                for item in edges:
                    node = item.get("node", {})
                    code = node.get("code")

                    if not code:
                        continue

                    # Solo posts estaticos (no videos aqui para evitar duplicidad)
                    if node.get("video_versions") is not None:
                        continue

                    # Si ya existe como reel, no se sobreescribe
                    if code in self.data and self.data[code]["type"] == "reel":
                        continue

                    self.data[code] = {
                        "shortcode": code,
                        "type": "post",
                        "likes": node.get("like_count", 0),
                        "comments": node.get("comment_count", 0),
                        "views": None
                    }

                print(f"Posts acumulados: {len([d for d in self.data.values() if d['type']=='post'])}")

            # Procesamiento de REELS
            if "data" in data and "xdt_api__v1__clips__user__connection_v2" in data["data"]:
                edges = data["data"]["xdt_api__v1__clips__user__connection_v2"].get("edges", [])

                for item in edges:
                    media = item.get("node", {}).get("media", {})
                    code = media.get("code")

                    if not code:
                        continue

                    # Los Reels proporcionan conteo de reproducciones (views)
                    self.data[code] = {
                        "shortcode": code,
                        "type": "reel",
                        "likes": media.get("like_count", 0),
                        "comments": media.get("comment_count", 0),
                        "views": media.get("play_count", 0)
                    }

                print(f"Reels acumulados: {len([d for d in self.data.values() if d['type']=='reel'])}")

        except Exception:
            pass

    def scroll_section(self, page, url, max_scrolls=6, label=""):
        """
        Realiza scroll automatico en una seccion especifica para cargar mas contenido.
        
        Args:
            page: Pagina de Playwright.
            url (str): URL a la que navegar.
            max_scrolls (int): Numero maximo de scrolls a realizar.
            label (str): Etiqueta para los mensajes de log.
        """
        print(f"\nScrapeando {label.upper()}...")

        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        prev_count = len(self.data)
        no_change = 0

        for i in range(max_scrolls):
            print(f"Scroll {i+1} ({label})")

            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(3000)

            current_count = len(self.data)

            if current_count == prev_count:
                no_change += 1
                print(f"Sin nuevos datos ({no_change})")
            else:
                no_change = 0

            if no_change >= 2:
                print("Deteniendo scroll (no hay mas contenido)")
                break

            prev_count = current_count

    def scrape_account(self, profile_url):
        """
        Ejecuta el proceso completo de scraping para una cuenta.
        
        Args:
            profile_url (str): URL del perfil de Instagram.
            
        Returns:
            list: Lista de diccionarios con los datos extraidos.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.auth_file)
            page = context.new_page()

            if id(page) not in self._attached_pages:
                page.on("response", self.handle_response)
                self._attached_pages.add(id(page))

            # Scrapear Posts
            self.scroll_section(page, profile_url, label="posts")

            # Scrapear Reels
            reels_url = profile_url.rstrip("/") + "/reels/"
            self.scroll_section(page, reels_url, label="reels")

            browser.close()

        result = list(self.data.values())
        print(f"\nDATASET FINAL: {len(result)}")
        return result

    def save_to_json(self, data, filename="instagram_data.json"):
        """
        Guarda los datos extraidos en un archivo JSON.
        
        Args:
            data (list): Datos a guardar.
            filename (str): Nombre del archivo de salida.
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\nDatos guardados correctamente en: {filename}")

if __name__ == "__main__":
    scraper = InstagramScraper()
    url = "https://www.instagram.com/midu.dev/"
    data = scraper.scrape_account(url)
    scraper.save_to_json(data)
    print("\n--- PRIMEROS 5 RESULTADOS ---")
    print(json.dumps(data[:5], indent=4))
