import requests
from bs4 import BeautifulSoup
import logging
import re
from urllib.parse import unquote

def search_wikimedia(query, max_images=20):
    url = f"https://commons.wikimedia.org/w/index.php?search={query}&title=Special:MediaSearch&go=Go&type=image"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    results = soup.find_all('a', class_='sdms-image-result')

    image_urls = []
    for result in results[:max_images]:
        try:
            # Get the page URL of the image
            image_page_url = "https://commons.wikimedia.org" + result['href']
            image_page = requests.get(image_page_url)
            image_soup = BeautifulSoup(image_page.content, 'html.parser')

            # Find the full resolution image URL
            full_image = image_soup.find('div', class_='fullImageLink').find('a')
            if full_image:
                original_url = "https:" + full_image['href']
                image_urls.append(original_url)
        except Exception as e:
            logging.error(f"Error processing Wikimedia image: {str(e)}")

    return image_urls