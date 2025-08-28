"""
Accepting Locale Preferences: API Patterns
Accept-Language HTTP Header
Most web/mobile clients send the Accept-Language header to specify language and regional preferences.

GET /products
Accept-Language: es-ES, fr-FR;q=0.8, en;q=0.7
Your API can read this header and serve the right localized content.

2. Query Params or User Profile Settings
Some APIs let users set language via explicit query parameter or user account setting:

GET /products?lang=de
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

SUPPORTED_LANGUAGES = ["en", "es", "fr"]

MESSAGES = {
    "en": {"greeting": "Hello", "price": "Price"},
    "es": {"greeting": "Hola", "price": "Precio"},
    "fr": {"greeting": "Bonjour", "price": "Prix"},
}

@app.middleware("http")
async def detect_language(request: Request, call_next):
    lang = request.headers.get("accept-language", "en").split(",")[0].split("-")[0]
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"
    request.state.lang = lang
    response = await call_next(request)
    return response

# Serving Localized Responses
@app.get("/greetings")
async def greet(request: Request):
    lang = request.state.lang
    msg = MESSAGES[lang]["greeting"]
    return {"greeting": msg}


'''
Handling Complex Language Preferences with Babel
'''
from babel import Locale
from babel.core import negotiate_locale
import re


def parse_accept_language(accept_language_header):
    """
    Properly parse Accept-Language header with quality values
    """
    if not accept_language_header:
        return []

    languages = []
    for item in accept_language_header.split(','):
        item = item.strip()

        if ';q=' in item:
            lang, quality = item.split(';q=', 1)
            try:
                quality = float(quality)
            except ValueError:
                quality = 1.0
        else:
            lang = item
            quality = 1.0

        lang = lang.strip()
        languages.append((lang, quality))

    # Sort by quality (highest first)
    languages.sort(key=lambda x: x[1], reverse=True)
    return languages

def manual_language_negotiation(accept_language_header, available_languages):
    """
    Manual language negotiation that respects quality values
    """
    parsed_langs = parse_accept_language(accept_language_header)

    for lang, quality in parsed_langs:
        # Try exact match first
        if lang in available_languages:
            return lang

        # Try with country code removed (e.g., es-ES -> es)
        if '-' in lang:
            base_lang = lang.split('-')[0]
            if base_lang in available_languages:
                return base_lang

        # Try wildcard match
        if lang == '*' and available_languages:
            return available_languages[0]

    return None

@app.get("/greetings2")
async def greet(request: Request):
    accept_header = request.headers.get("accept-language", "")
    lang = manual_language_negotiation(accept_header, SUPPORTED_LANGUAGES)   # or "en"
    request.state.lang = lang
    msg = MESSAGES[lang]["greeting"]
    return {"greeting": msg}

"""
Libraries for i18n/l10n

Babel: Formatting dates, numbers, currencies, and messages.
python-gettext: Standard translation lifecycle and portable PO/MO files.
Flask-Babel, Django i18n: For web apps, patterns can be adapted for API usage.
"""

from babel.dates import format_datetime
from babel.numbers import format_currency

from datetime import datetime

@app.get("/order")
async def get_order(request: Request):
    lang = request.state.lang
    now = datetime.now()
    price = 99.99

    formatted_date = format_datetime(now, locale=lang)
    formatted_price = format_currency(price, "USD", locale=lang)
    return {
        "date": formatted_date,
        "price": formatted_price,
    }

def main():
    import uvicorn
    uvicorn.run(
        "multilang_demo:app",
        host="localhost",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()