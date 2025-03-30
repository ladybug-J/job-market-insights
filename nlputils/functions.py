import scapy
from collections import Counter


def lemmatize_description(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    words = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]  # Lemmatization & stopword removal
    return words

def count_tools(descriptions, key):

    with open("./data_tools.json", "rb") as file:
        tools = json.load(file)[key]

    word_counts = Counter()

    for text in descriptions:
        words = text.lower().split()  # Simple tokenization
        word_counts.update(word for word in words if word in tools)