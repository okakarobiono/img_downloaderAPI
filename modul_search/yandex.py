import requests
from bs4 import BeautifulSoup
import re
import logging

def search_yandex(query, max_images=20):
    url = f"https://yandex.com/images/search?text={query}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    image_urls = []
    for img in soup.find_all('img', class_='serp-item__thumb'):
        try:
            # Extract the actual image URL from the data-src attribute
            img_url = img.get('src')
            if img_url and img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url and not img_url.startswith('http'):
                img_url = 'https://yandex.com' + img_url

            if img_url:
                image_urls.append(img_url)
                if len(image_urls) >= max_images:
                    break
        except Exception as e:
            logging.error(f"Error processing Yandex image: {str(e)}")

    return image_urls