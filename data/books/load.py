import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Base URL for the psychology books catalog
BASE_URL = "https://flibusta.site/g/sci_psychology"
DOWNLOAD_DIR = "flibusta_books"

# Selenium WebDriver setup
options = webdriver.ChromeOptions()
prefs = {"download.default_directory": os.path.abspath(DOWNLOAD_DIR)}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(options=options)

# Create a directory for downloads
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_catalog_book_links(catalog_url):
    """
    Fetches all book links from the catalog page.
    """
    driver.get(catalog_url)
    book_links = driver.find_elements(By.CSS_SELECTOR, "ol > a[href^='/b/']")
    return [book.get_attribute("href") for book in book_links]

def find_and_download_format(book_url):
    """
    Navigates to a book page, finds the download block, and downloads the preferred format.
    """
    try:
        
        # Preferred formats for RAG systems
        preferred_formats = ["fb2", "epub", "mobi"]
        for format in preferred_formats:
            try:
                print(f"{book_url}/{format}")
                driver.get(url=f"{book_url}/{format}")
                time.sleep(5)
                return
            except Exception as e:
                print(f'format {format} didnt work')
                continue

        print(f"No suitable format found for {book_url}")
    except Exception as e:
        print(f"Failed to download from book page: {book_url}, Error: {e}")

def main():
    page_number = 1
    while True:
        print(f"Processing catalog page {page_number}...")
        catalog_page_url = f"{BASE_URL}?page={page_number}"

        try:
            # Fetch book links from the catalog page
            book_links = get_catalog_book_links(catalog_page_url)
            if not book_links:
                print("No more books found.")
                break

            for book_link in book_links:
                # Process each book
                find_and_download_format(book_link)

            # Move to the next catalog page
            page_number += 1
        except Exception as e:
            print(f"Error on catalog page {page_number}: {e}")
            break

    driver.quit()

if __name__ == "__main__":
    main()
