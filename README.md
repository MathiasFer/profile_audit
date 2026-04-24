# Reactions Scraper (rama enfocada)

Esta rama está enfocada únicamente en `ReactionsScraper.py`.

## Objetivo

Extraer información de posts/reels de Instagram:

- shortcode
- likes
- comments_count
- views
- comments
- description
- hashtags

## Notas de la rama

- El `.gitignore` está configurado para ignorar todo por defecto.
- Solo se permiten para control de versiones: `ReactionsScraper.py`, `README.md` y `.gitignore`.
- `main.py` y el resto de archivos quedan fuera en esta rama.

## Ejecución rápida

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
2. Ejecuta:
   ```bash
   python ReactionsScraper.py
   ```

## Importante

Usa esta herramienta respetando los términos de uso de la plataforma y con fines legítimos.
