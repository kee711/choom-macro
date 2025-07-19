from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .config_manager import ConfigManager
from .logger import setup_logger


class WebAutomator:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = setup_logger(self.__class__.__name__, config.get('general', 'log_level', 'INFO'))
        options = Options()
        if config.get('web_automation', 'headless'):
            options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(config.get('web_automation', 'implicit_wait', 10))

    def open_upload_page(self):
        self.driver.get('https://app.hanlim.world/upload')

    def search_song(self, query: str) -> None:
        search_box = self.driver.find_element(By.CSS_SELECTOR, '.upload-step-1-search-container input')
        search_box.clear()
        search_box.send_keys(query)
        # Wait for results
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.search-result-item'))
        )
        result = self.driver.find_element(By.CSS_SELECTOR, '.search-result-item')
        result.click()

    def upload_video(self, file_path: Path, description: str) -> None:
        self.search_song(file_path.stem)
        next_btn = self.driver.find_element(By.CSS_SELECTOR, 'button.next')
        next_btn.click()
        import_btn = self.driver.find_element(By.CSS_SELECTOR, 'button.import')
        import_btn.click()
        file_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
        file_input.send_keys(str(file_path.resolve()))
        desc_area = self.driver.find_element(By.CSS_SELECTOR, 'textarea.description')
        desc_area.send_keys(description)
        submit_btn = self.driver.find_element(By.CSS_SELECTOR, 'button.submit')
        submit_btn.click()

    def close(self):
        self.driver.quit()
