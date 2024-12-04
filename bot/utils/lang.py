import gettext 
from pathlib import Path

import logging 

domain = 'bot'
localedir = 'locales'

def get_i18n_string(s, lang) -> str:
    logging.info("lang: " + lang)
    if lang in ['ru']:
        logging.info("Getting translations from: " + str(Path(__file__).parent.parent / localedir))
        language_translations = gettext.translation(domain, Path(__file__).parent.parent / localedir, languages=[lang])
        language_translations.install()
        logging.info(gettext.gettext(s))
        return gettext.gettext(s)
    logging.info("Getting default translations from: localedir")
    language_translations = gettext.translation(domain, localedir, languages=['en'])
    language_translations.install()
    
    return gettext.gettext(s)