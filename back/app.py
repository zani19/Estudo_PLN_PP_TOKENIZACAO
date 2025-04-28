from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from flask_cors import CORS
from nltk.tokenize import sent_tokenize, word_tokenize
import time
import requests
import nltk

nltk.download('punkt')

app = Flask(__name__)
CORS(app)

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    url = data['url']

    # Raspagem de dados
    start_time = time.perf_counter()
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    end_time = time.perf_counter()

    scrape_time_ms = max((end_time - start_time) * 1000, 0.01)  # em milissegundos
    raw_html = soup.prettify()  # HTML bruto raspado

    # Remoção de ruído
    start_clean = time.perf_counter()
    cleaned_text = extract_reviews(soup, url)  # Extrai apenas os comentários
    end_clean = time.perf_counter()

    clean_time_ms = max((end_clean - start_clean) * 1000, 0.01)  # em milissegundos

    # Verifique se o texto limpo está vazio
    if not cleaned_text.strip():
        return jsonify({'error': 'Texto limpo está vazio.'})

    # Tokenização por frases
    start_sent = time.perf_counter()
    sentences = sent_tokenize(cleaned_text, language='portuguese')
    end_sent = time.perf_counter()
    sent_tokenize_time_ms = max((end_sent - start_sent) * 1000, 0.01)

    # Tokenização por palavras dentro de frases
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

    # Formatação da saída
    formatted_sentences = [item["sentence"] for item in tokenized_sentences]
    formatted_words = [item["words"] for item in tokenized_sentences]

    return jsonify({
        'scrape_time': round(scrape_time_ms, 2),
        'clean_time': round(clean_time_ms, 2),
        'sent_tokenize_time': round(sent_tokenize_time_ms, 2),
        'word_tokenize_time': round(word_tokenize_time_ms, 2),
        'raw_html': raw_html[:500],
        'cleaned_text': cleaned_text[:500],
        'sentences': formatted_sentences,  # Frases formatadas
        'words': formatted_words,          # Palavras formatadas dentro das frases
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