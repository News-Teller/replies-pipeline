from languages import *

def get_keywords(text, lang):
    result = []
    pos_tag = ['PROPN', 'ADJ', 'NOUN', 'VERB']
    doc = spacy_models[lang](text.lower())
    for token in doc:
        if(token.text in spacy_models[lang].Defaults.stop_words or token.text in punctuation or len(token.text) < 2):
            continue
        if(token.pos_ in pos_tag):
            result.append(token.text)
    return list(set(result))