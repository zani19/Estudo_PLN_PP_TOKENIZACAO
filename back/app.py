from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import time
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

@app.route('/scrape', methods=['POST'])

def scrape():
    data = request.get_json()
    url = data['url']

    start_time = time.time()
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    end_time = time.time()

    scrape_time_ms = (end_time - start_time) * 1000  # em milissegundos
    
    # Remoção de Ruído
    start_clean = time.time()
    cleaned_text = clean_html(soup)
    end_clean = time.time()

    clean_time_ms = (end_clean - start_clean) * 1000  # em milissegundos

    return jsonify({
        'scrape_time': round(scrape_time_ms, 2),
        'clean_time': round(clean_time_ms, 2),
        'cleaned_text': cleaned_text[:500] + '...',  # Opcional: mandar só os 500 primeiros caracteres
        'status': 'success'
    })

def clean_html(soup):
    # Remover scripts e styles
    for script_or_style in soup(["script", "style", "meta", "noscript", "header", "footer", "head"]):
        script_or_style.extract()

    # Pega o texto limpo
    text = soup.get_text(separator=' ')

    # Remove espaços em excesso
    cleaned_text = ' '.join(text.split())
    return cleaned_text


if __name__ == '__main__':
    app.run(debug=True)
