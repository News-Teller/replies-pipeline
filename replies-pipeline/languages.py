import spacy
from string import punctuation

import de_core_news_md
import en_core_web_md
import es_core_news_md
import fr_core_news_md
import it_core_news_md
import pt_core_news_md

spacy_de = de_core_news_md.load()
spacy_en = en_core_web_md.load()
spacy_es = es_core_news_md.load()
spacy_fr = fr_core_news_md.load()
spacy_it = it_core_news_md.load()
spacy_pt = pt_core_news_md.load()

spacy_models = {
    'de' : spacy_de,
    'en' : spacy_en,
    'es' : spacy_es,
    'fr' : spacy_fr,
    'it' : spacy_it,
    'pt' : spacy_pt,
    #'el' : 'el_core_news_sm',
    #'ja' : 'ja_core_news_sm',
    #'pl' : 'pl_core_news_sm',
}