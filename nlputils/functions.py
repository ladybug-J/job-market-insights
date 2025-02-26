import scapy

def lemmatize_description(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    words = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]  # Lemmatization & stopword removal
    return words