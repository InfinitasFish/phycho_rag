import json
import os
import re
import time
import zipfile

import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def download_font(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
    else:
        raise Exception(f"Failed to download font: {response.status_code}")


def extract_ttf_from_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.namelist():
            if member.endswith('.ttf'):
                zip_ref.extract(member, extract_to)


def clean_text(text):
    cleaned_text = re.sub(r'[^а-яА-ЯёЁa-zA-Z.,:!?"\s\n\t]', '', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    cleaned_text = cleaned_text.replace('Психолог zigmund.online ', '')\
        .replace('Психоаналитический психотерапевт zigmund.online ', '')
    return cleaned_text


def get_all_articles_with_scroll_and_click(base_url):
    chrome_options = Options()
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(base_url)
        time.sleep(3)

        article_links = set()
        no_more_button = False

        while True:
            articles = driver.find_elements(
                By.CSS_SELECTOR,
                "article.op-post a.op-post__inner",
            )
            for article in articles:
                href = article.get_attribute("href")
                if href:
                    article_links.add(href)

            if not no_more_button:
                try:
                    load_more_button = driver.find_element(
                        By.CSS_SELECTOR,
                        "button.op-posts__load-more",
                    )
                    load_more_button.click()
                    time.sleep(3)
                except Exception:
                    no_more_button = True

            if no_more_button:
                last_height = driver.execute_script(
                    "return document.body.scrollHeight"
                )
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )
                time.sleep(3)
                new_height = driver.execute_script(
                    "return document.body.scrollHeight"
                )
                if new_height == last_height:
                    break

            break

        return list(article_links)
    finally:
        driver.quit()


def get_article_links(base_url):
    response = requests.get(base_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    article_links = []
    for article in soup.find_all('article', class_='op-post'):
        a_tag = article.find('a', class_='op-post__inner')
        if a_tag:
            href = a_tag.get('href')
            if href:
                article_links.append(href)

    return article_links


def parse_article(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    title_element = soup.find('h1', class_='article-header__title')
    if title_element:
        title = title_element.get_text(strip=True)
    else:
        title = "Без заголовка"

    content = []

    article_body = soup.find('div', class_='post-content')
    if article_body:
        for element in article_body.find_all(['p', 'ol']):
            if element.name == 'p':
                text = element.get_text(strip=True)
                text = clean_text(text)
                if 'Используйте промокод' in text:
                    continue
                content.append(text)
            elif element.name == 'ol':
                for li in element.find_all('li'):
                    li_text = li.get_text(strip=True)
                    content.append(clean_text(li_text))

    return {
        'title': title,
        'content': '\n'.join(content)
    }


def save_articles_to_pdf(article, pdf_filename):
    font_path = "./dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf"

    if not os.path.exists(font_path):
        font_url = "https://sourceforge.net/projects/dejavu/files/dejavu/2.37/\
            dejavu-fonts-ttf-2.37.zip/download"
        temp_zip_path = "temp_fonts.zip"
        download_font(font_url, temp_zip_path)
        extract_ttf_from_zip(temp_zip_path, ".")
        os.remove(temp_zip_path)

    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

    c = canvas.Canvas(pdf_filename, pagesize=letter)
    width, height = letter
    y = height - 40
    c.setFont("DejaVuSans", 12)

    c.drawString(40, y, article['title'])
    y -= 20

    content_lines = simpleSplit(
        article['content'],
        "DejaVuSans",
        12,
        width - 80,
    )
    text_object = c.beginText(40, y - 20)
    text_object.setFont("DejaVuSans", 12)

    for line in content_lines:
        text_object.textLine(line)
        y -= 12
        if y < 40:
            c.showPage()
            c.drawString(40, height - 40, article['title'])
            c.setFont("DejaVuSans", 12)
            text_object = c.beginText(40, height - 60)
            y = height - 40

    c.drawText(text_object)
    c.save()


def save_articles_to_json(articles, json_filename):
    with open(json_filename, 'w', encoding='utf-8') as json_file:
        json.dump(articles, json_file, ensure_ascii=False, indent=4)


def main():
    base_url = "https://zigmund.online/journal/"
    all_links = get_all_articles_with_scroll_and_click(base_url)
    print(f"Найдено {len(all_links)} статей:")

    all_articles = []
    for link in all_links:
        article_data = parse_article(link)
        if article_data:
            all_articles.append(article_data)
            print(f"Спарсили статью: {article_data['title']}")
        else:
            print(f"Не удалось распарсить статью: {link}")

    os.makedirs('./data/articles/parsed_articles/', exist_ok=True)
    for article in all_articles:
        title = clean_text(article["title"]).replace(" ", "_")
        path = os.path.join('./articles/parsed_articles/', f'{title}.json')
        save_articles_to_json(article, path)


if __name__ == "__main__":
    main()
