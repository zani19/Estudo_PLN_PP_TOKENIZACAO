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

    # Raspagem de dados
    start_time = time.time()
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    end_time = time.time()

    scrape_time_ms = (end_time - start_time) * 1000  # em milissegundos
    raw_html = soup.prettify()  # HTML bruto raspado

    # Remoção de ruído
    start_clean = time.time()
    cleaned_text = extract_reviews(soup, url)  # Extrai apenas os comentários
    end_clean = time.time()

    clean_time_ms = (end_clean - start_clean) * 1000  # em milissegundos

    return jsonify({
        'scrape_time': round(scrape_time_ms, 2),
        'clean_time': round(clean_time_ms, 2),
        'raw_html': raw_html[:500],  # Limita o HTML bruto a 500 caracteres
        'cleaned_text': cleaned_text[:500],  # Limita o texto limpo a 500 caracteres
        'status': 'success'
    })

def extract_reviews(soup, url):
    """
    Localiza e extrai os comentários dos usuários com base em classes ou tags específicas.
    """
    reviews = []

    # Verifica se é Mercado Livre
    if "mercadolivre" in url or "mercadolivre.com" in url:
        # Busca o resumo das avaliações no Mercado Livre
        summary = soup.find_all("p", class_="ui-review-capability__summary__plain_text__summary_container")
        print("Resumo encontrado no Mercado Livre:", summary)
        reviews.extend([item.get_text(strip=True) for item in summary])

    # Verifica se é Amazon
    elif "amazon" in url or "amazon.com" in url:
        # Busca os comentários individuais na Amazon
        detailed_reviews = soup.find_all("div", {"data-hook": "review-collapsed"})
        print("Comentários detalhados encontrados na Amazon:", detailed_reviews)
        for review in detailed_reviews:
            # Extrai o texto dentro de <span> (se existir)
            span = review.find("span", {"data-hook": "review-body"})
            if span:
                reviews.append(span.get_text(strip=True))
            else:
                # Caso não haja <span>, extrai o texto diretamente do <div>
                reviews.append(review.get_text(strip=True))

    # Caso nenhum comentário seja encontrado
    if not reviews:
        print("Nenhum comentário encontrado.")
        return "Nenhum comentário encontrado."

    return '\n'.join(reviews)  # Junta os comentários em um único texto com quebras de linha

if __name__ == '__main__':
    app.run(debug=True)