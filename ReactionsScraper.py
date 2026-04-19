import json
from playwright.sync_api import sync_playwright

class InstagramScraper:
    def __init__(self, auth_file="auth.json"):
        self.auth_file = auth_file

        self.data = {}  # 🔥 dataset único por shortcode
        self._attached_pages = set()

    def handle_response(self, response):
        content_type = response.headers.get("content-type", "").lower()

        if "json" not in content_type and "graphql" not in response.url:
            return

        try:
            data = response.json()

            # =========================================
            # 🔹 POSTS (feed principal)
            # =========================================
            if "data" in data and "xdt_api__v1__feed__user_timeline_graphql_connection" in data["data"]:
                edges = data["data"]["xdt_api__v1__feed__user_timeline_graphql_connection"].get("edges", [])

                for item in edges:
                    node = item.get("node", {})
                    code = node.get("code")

                    if not code:
                        continue

                    # 🔥 SOLO POSTS (no videos)
                    if node.get("video_versions") is not None:
                        continue

                    # 🔥 SI YA EXISTE COMO REEL → NO LO SOBREESCRIBAS
                    if code in self.data and self.data[code]["type"] == "reel":
                        continue

                    self.data[code] = {
                        "shortcode": code,
                        "type": "post",
                        "likes": node.get("like_count", 0),
                        "comments": node.get("comment_count", 0),
                        "views": None
                    }

                print(f"📸 Posts acumulados: {len([d for d in self.data.values() if d['type']=='post'])}")

            # =========================================
            # 🔹 REELS (donde SÍ hay views)
            # =========================================
            if "data" in data and "xdt_api__v1__clips__user__connection_v2" in data["data"]:
                edges = data["data"]["xdt_api__v1__clips__user__connection_v2"].get("edges", [])

                for item in edges:
                    media = item.get("node", {}).get("media", {})
                    code = media.get("code")

                    if not code:
                        continue

                    # 🔥 SI YA EXISTE COMO POST → LO SOBREESCRIBE (REEL ES MEJOR)
                    self.data[code] = {
                        "shortcode": code,
                        "type": "reel",
                        "likes": media.get("like_count", 0),
                        "comments": media.get("comment_count", 0),
                        "views": media.get("play_count", 0)
                    }

                print(f"🎬 Reels acumulados: {len([d for d in self.data.values() if d['type']=='reel'])}")

        except Exception:
            pass

    # =========================================
    # 🔹 SCROLL INTELIGENTE
    # =========================================
    def scroll_section(self, page, url, max_scrolls=6, label=""):
        print(f"\n🔎 Scrapeando {label.upper()}...")

        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)

        prev_count = len(self.data)
        no_change = 0

        for i in range(max_scrolls):
            print(f"🔽 Scroll {i+1} ({label})")

            page.mouse.wheel(0, 3000)
            page.wait_for_timeout(3000)

            current_count = len(self.data)

            if current_count == prev_count:
                no_change += 1
                print(f"⚠️ Sin nuevos datos ({no_change})")
            else:
                no_change = 0

            if no_change >= 2:
                print("⛔ Deteniendo scroll (no hay más contenido)")
                break

            prev_count = current_count

    # =========================================
    # 🔹 MAIN
    # =========================================
    def scrape_account(self, profile_url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(storage_state=self.auth_file)
            page = context.new_page()

            if id(page) not in self._attached_pages:
                page.on("response", self.handle_response)
                self._attached_pages.add(id(page))

            # 🔹 POSTS
            self.scroll_section(page, profile_url, label="posts")

            # 🔹 REELS
            reels_url = profile_url.rstrip("/") + "/reels/"
            self.scroll_section(page, reels_url, label="reels")

            browser.close()

        result = list(self.data.values())

        print(f"\n📊 DATASET FINAL: {len(result)}")

        return result

    def save_to_json(self, data, filename="instagram_data.json"):
        """Guarda los datos en un archivo JSON con formato indentado."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\n📁 Datos guardados correctamente en: {filename}")


# =========================================
# 🔹 TEST
# =========================================
if __name__ == "__main__":
    scraper = InstagramScraper()

    url = "https://www.instagram.com/midu.dev/"

    data = scraper.scrape_account(url)

    # 🔹 Guardar en JSON
    scraper.save_to_json(data)

    print("\n--- PRIMEROS 5 RESULTADOS ---")
    print(json.dumps(data[:5], indent=4))
