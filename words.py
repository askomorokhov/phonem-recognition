"""20 picture cards. Emoji are used as pictures to keep the demo self-contained;
replace with real images in the production app.

Words are lowercase because Vosk models output lowercase text.
"""

LANGUAGES = {
    "en": "English",
    "uk": "Українська",
    "es": "Español",
    "it": "Italiano",
    "de": "Deutsch",
}

WORDS = [
    {"id": "apple",  "picture": "🍎", "en": "apple",  "uk": "яблуко",   "es": "manzana", "it": "mela",     "de": "apfel"},
    {"id": "car",    "picture": "🚗", "en": "car",    "uk": "машина",   "es": "coche",   "it": "macchina", "de": "auto"},
    {"id": "cat",    "picture": "🐈", "en": "cat",    "uk": "кіт",      "es": "gato",    "it": "gatto",    "de": "katze"},
    {"id": "dog",    "picture": "🐕", "en": "dog",    "uk": "собака",   "es": "perro",   "it": "cane",     "de": "hund"},
    {"id": "house",  "picture": "🏠", "en": "house",  "uk": "будинок",  "es": "casa",    "it": "casa",     "de": "haus"},
    {"id": "sun",    "picture": "☀️", "en": "sun",    "uk": "сонце",    "es": "sol",     "it": "sole",     "de": "sonne"},
    {"id": "tree",   "picture": "🌳", "en": "tree",   "uk": "дерево",   "es": "árbol",   "it": "albero",   "de": "baum"},
    {"id": "ball",   "picture": "⚽", "en": "ball",   "uk": "м'яч",     "es": "pelota",  "it": "palla",    "de": "ball"},
    {"id": "fish",   "picture": "🐟", "en": "fish",   "uk": "риба",     "es": "pez",     "it": "pesce",    "de": "fisch"},
    {"id": "book",   "picture": "📖", "en": "book",   "uk": "книга",    "es": "libro",   "it": "libro",    "de": "buch"},
    {"id": "flower", "picture": "🌸", "en": "flower", "uk": "квітка",   "es": "flor",    "it": "fiore",    "de": "blume"},
    {"id": "bird",   "picture": "🐦", "en": "bird",   "uk": "птах",     "es": "pájaro",  "it": "uccello",  "de": "vogel"},
    {"id": "bread",  "picture": "🍞", "en": "bread",  "uk": "хліб",     "es": "pan",     "it": "pane",     "de": "brot"},
    {"id": "milk",   "picture": "🥛", "en": "milk",   "uk": "молоко",   "es": "leche",   "it": "latte",    "de": "milch"},
    {"id": "chair",  "picture": "🪑", "en": "chair",  "uk": "стілець",  "es": "silla",   "it": "sedia",    "de": "stuhl"},
    {"id": "key",    "picture": "🔑", "en": "key",    "uk": "ключ",     "es": "llave",   "it": "chiave",   "de": "schlüssel"},
    {"id": "moon",   "picture": "🌙", "en": "moon",   "uk": "місяць",   "es": "luna",    "it": "luna",     "de": "mond"},
    {"id": "water",  "picture": "💧", "en": "water",  "uk": "вода",     "es": "agua",     "it": "acqua",   "de": "wasser"},
    {"id": "cup",    "picture": "☕", "en": "cup",    "uk": "чашка",    "es": "taza",    "it": "tazza",    "de": "tasse"},
    {"id": "clock",  "picture": "⏰", "en": "clock",  "uk": "годинник", "es": "reloj",   "it": "orologio", "de": "uhr"},
]
