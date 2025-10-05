from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time, os

def upload_to_tiktok(file_path):
    chrome_options = Options()
    chrome_options.add_argument("--user-data-dir=chrome-data")  # keeps login
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get("https://www.tiktok.com/upload?lang=en")
        print("🌐 Opening TikTok Upload Page...")

        time.sleep(10)  # Wait for manual login first time
        upload_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        upload_input.send_keys(os.path.abspath(file_path))
        print(f"📤 Uploaded: {file_path}")

        # Wait to process video manually or click post
        time.sleep(15)

    except Exception as e:
        print(f"⚠️ TikTok upload failed: {e}")
    finally:
        driver.quit()
