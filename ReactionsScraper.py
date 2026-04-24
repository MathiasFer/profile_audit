import json
import re
from playwright.sync_api import sync_playwright

class IGUnifiedScraper:
    def __init__(self, auth_file="auth.json"):
        self.auth_file = auth_file
        self.posts_data = {}
        self.current_post = None

    # 🎯 Interceptor global
    def handle_response(self, response):
        url = response.url

        try:
            data = response.json()
        except:
            return

        # 📊 INFO GENERAL DEL POST / REEL
        if "graphql" in url or "media" in url:
            try:
                items = []

                if "items" in data:
                    items = data["items"]
                elif "data" in data:
                    return

                for item in items:
                    code = item.get("code")
                    if not code:
                        continue

                    self.posts_data[code] = self.posts_data.get(code, {})

                    self.posts_data[code].update({
                        "shortcode": code,
                        "likes": item.get("like_count", 0),
                        "comments_count": item.get("comment_count", 0),
                        "views": item.get("play_count") or item.get("view_count"),
                        "comments": self.posts_data[code].get("comments", [])
                    })

            except:
                pass

    def clean_description(self, text):
        if not text:
            return text

        # Elimina cualquier etiqueta HTML que se cuele en la captura.
        text = re.sub(r"<[^>]+>", "", text)
        # Deja la descripcion en una sola linea sin saltos.
        text = re.sub(r"\s+", " ", text)
        return text.strip()

        # 💬 COMENTARIOS
        if "comments/" in url:
            try:
                code = self.current_post
                if not code:
                    return

                self.posts_data[code]["comments"] = []

                for c in data.get("comments", [])[:12]:
                    self.posts_data[code]["comments"].append({
                        "user": c.get("user", {}).get("username"),
                        "text": c.get("text"),
                        "likes": c.get("comment_like_count", 0),
                        "verified": c.get("user", {}).get("is_verified", False)
                    })

                print(f"💬 Comentarios OK: {code}")

            except:
                pass

    # 🧠 FIX REAL AQUÍ (caption + hashtags robusto)
    def extract_caption(self, page):
        try:
            # Esperar caption
            page.wait_for_selector("h1._ap3a", timeout=5000)

            caption_element = page.locator("h1._ap3a").first

            # Texto completo
            description = caption_element.inner_text()
            description = self.clean_description(description)

            # Hashtags desde <a>
            hashtag_elements = caption_element.locator("a").all()
            hashtags = []

            for tag in hashtag_elements:
                text = tag.inner_text()
                if text.startswith("#"):
                    hashtags.append(text)

            return {
                "description": description,
                "hashtags": hashtags
            }

        except Exception as e:
            print("⚠️ Fallback caption activado")

            # fallback por si Instagram cambia clases
            try:
                alt = page.locator("article h1").first
                description = alt.inner_text()
                description = self.clean_description(description)

                hashtags = re.findall(r"#\w+", description)

                return {
                    "description": description,
                    "hashtags": hashtags
                }
            except:
                return {
                    "description": None,
                    "hashtags": []
                }

    def scrape(self, username):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            context = browser.new_context(storage_state=self.auth_file)
            page = context.new_page()

            page.on("response", self.handle_response)

            print(f"🌐 Entrando a @{username}")
            page.goto(f"https://www.instagram.com/{username}/")
            page.wait_for_timeout(5000)

            # 🔗 obtener primeras 12 publicaciones
            links = page.locator("a[href*='/p/'], a[href*='/reel/']").all()

            for i in range(min(12, len(links))):
                try:
                    print(f"➡️ Post {i+1}/12")

                    links[i].click(force=True)
                    page.wait_for_timeout(3000)

                    url = page.url
                    code = url.split("/")[-2]
                    self.current_post = code

                    self.posts_data[code] = self.posts_data.get(code, {})
                    self.posts_data[code]["shortcode"] = code

                    # 📄 caption FIX aplicado
                    caption_data = self.extract_caption(page)
                    self.posts_data[code].update(caption_data)

                    page.keyboard.press("Escape")
                    page.wait_for_timeout(1000)

                except:
                    print(f"⚠️ Error en post {i+1}")

            browser.close()

        return list(self.posts_data.values())

    def save(self, data, filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"\n✅ JSON guardado en {filename}")


if __name__ == "__main__":
    print("🚀 IG Scraper PRO (FIX captions)")

    user = input("👤 Usuario: ").strip()
    if user.startswith("@"):
        user = user[1:]

    scraper = IGUnifiedScraper()
    data = scraper.scrape(user)

    scraper.save(data, f"{user}_dataset.json")

    print("\n🔥 Preview:")
    print(json.dumps(data[:2], indent=4, ensure_ascii=False))