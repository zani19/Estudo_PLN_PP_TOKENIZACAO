from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from flask_cors import CORS
from nltk.tokenize import sent_tokenize, word_tokenize
import time
import requests
import nltk
from spellchecker import SpellChecker
import re

nltk.download('punkt')

app = Flask(__name__)
CORS(app)

# Dicionário de abreviações
abbreviation_dict = {
    "vc": "você",
    "tbm": "também",
    "q": "que",
    "pq": "porque",
    "blz": "beleza",
    "msg": "mensagem",
    "obg": "obrigado",
    "dps": "depois",
}

def expand_abbreviations(text):
    pattern = re.compile(r'\b(' + '|'.join(re.escape(k) for k in abbreviation_dict.keys()) + r')\b', re.IGNORECASE)
    return pattern.sub(lambda x: abbreviation_dict[x.group().lower()], text)

def correct_spelling(text):
    spell = SpellChecker(language='pt')
    words = text.split()
    corrected_words = [spell.correction(word) or word for word in words]
    return ' '.join(corrected_words)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    url = data['url']

    # Raspagem
    start_time = time.perf_counter()
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    end_time = time.perf_counter()
    scrape_time_ms = max((end_time - start_time) * 1000, 0.01)

    raw_html = soup.prettify()

    # Remoção de ruído
    start_clean = time.perf_counter()
    cleaned_text = extract_reviews(soup, url)
    end_clean = time.perf_counter()
    clean_time_ms = max((end_clean - start_clean) * 1000, 0.01)

    if not cleaned_text.strip():
        return jsonify({'error': 'Texto limpo está vazio.'})

    # Conversão para minúsculas
    start_lower = time.perf_counter()
    lower_text = cleaned_text.lower()
    end_lower = time.perf_counter()
    lower_time_ms = max((end_lower - start_lower) * 1000, 0.01)

    # Expansão de abreviações
    start_expand = time.perf_counter()
    expanded_text = expand_abbreviations(lower_text)
    end_expand = time.perf_counter()
    expand_time_ms = max((end_expand - start_expand) * 1000, 0.01)

    # Correção ortográfica
    start_spell = time.perf_counter()
    corrected_text = correct_spelling(expanded_text)
    end_spell = time.perf_counter()
    spell_time_ms = max((end_spell - start_spell) * 1000, 0.01)

    # Tokenização de frases
    start_sent = time.perf_counter()
    sentences = sent_tokenize(corrected_text, language='portuguese')
    end_sent = time.perf_counter()
    sent_tokenize_time_ms = max((end_sent - start_sent) * 1000, 0.01)

    # Tokenização de palavras
    start_word = time.perf_counter()
    tokenized_sentences = [
        {
            "sentence": f"[{sentence}]",
            "words": [f"[{word}]" for word in word_tokenize(sentence, language='portuguese')]
        }
        for sentence in sentences
    ]
    end_word = time.perf_counter()
    word_tokenize_time_ms = max((end_word - start_word) * 1000, 0.01)

    formatted_sentences = [item["sentence"] for item in tokenized_sentences]
    formatted_words = [item["words"] for item in tokenized_sentences]

    return jsonify({
        'scrape_time': round(scrape_time_ms, 2),
        'clean_time': round(clean_time_ms, 2),
        'lower_time': round(lower_time_ms, 2),
        'expand_time': round(expand_time_ms, 2),
        'spell_time': round(spell_time_ms, 2),
        'sent_tokenize_time': round(sent_tokenize_time_ms, 2),
        'word_tokenize_time': round(word_tokenize_time_ms, 2),
        'raw_html': raw_html[:500],
        'cleaned_text': cleaned_text[:500],
        'lower_text': lower_text[:500],
        'expanded_text': expanded_text[:500],
        'sentences': formatted_sentences,
        'words': formatted_words,
        'status': 'success'
    })
    
def extract_reviews(soup, url):
    """
    Localiza e extrai os comentários dos usuários com base em classes ou tags específicas.
    """
    reviews = []

    # Verifica se é Mercado Livre
    if "mercadolivre" in url or "mercadolivre.com" in url:
        summary = soup.find_all("p", class_="ui-review-capability__summary__plain_text__summary_container")
        reviews.extend([item.get_text(strip=True) for item in summary])

    # Verifica se é Amazon
    elif "amazon" in url or "amazon.com" in url:
        detailed_reviews = soup.find_all("div", {"data-hook": "review-collapsed"})
        for review in detailed_reviews:
            span = review.find("span", {"data-hook": "review-body"})
            if span:
                reviews.append(span.get_text(strip=True))
            else:
                reviews.append(review.get_text(strip=True))

    # Caso nenhum comentário seja encontrado
    if not reviews:
        return "Nenhum comentário encontrado."

    return '\n'.join(reviews)  # Junta os comentários em um único texto com quebras de linha



if __name__ == '__main__':
    app.run(debug=True)