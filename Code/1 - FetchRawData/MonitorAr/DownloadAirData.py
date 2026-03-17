import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


CONFIG = {
    "URL": "https://www.data.rio/datasets/PCRJ::qualidade-do-ar-dados-hor%C3%A1rios/explore?layer=2",
    "DOWNLOAD_DIR": "../../../../Data/RawData/MonitorAr",
    "WAIT_TIMEOUT": 60
}


def create_driver():

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")

    prefs = {
        "download.default_directory": os.path.abspath(CONFIG["DOWNLOAD_DIR"]),
        "download.prompt_for_download": False
    }

    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)

    return driver


def run_rpa():

    driver = create_driver()

    wait = WebDriverWait(driver, CONFIG["WAIT_TIMEOUT"])

    try:

        print("Abrindo página...")
        driver.get(CONFIG["URL"])

        # -------------------------------------------------
        # Abrir aba de downloads
        # -------------------------------------------------

        print("Abrindo aba de downloads...")

        download_tab = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "nav button:nth-of-type(4)"))
        )

        download_tab.click()

        # -------------------------------------------------
        # Esperar lista de downloads
        # -------------------------------------------------
        time.sleep(3)

        print("Esperando lista de downloads...")

        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "arcgis-hub-download-list-item")
            )
        )

        time.sleep(3)

        # -------------------------------------------------
        # Encontrar todos os itens
        # -------------------------------------------------

        items = driver.find_elements(By.CSS_SELECTOR, "arcgis-hub-download-list-item")

        print(f"{len(items)} opções de download encontradas")

        csv_item = None

        for item in items:

            try:

                file_type = item.find_element(By.CSS_SELECTOR, "div div div")

                text = file_type.text.lower()

                print("Tipo encontrado:", text)

                if "csv" in text:
                    csv_item = item
                    break

            except:
                continue

        if csv_item is None:
            raise Exception("Arquivo CSV não encontrado")

        print("CSV encontrado. Clicando no botão...")

        download_button = csv_item.find_element(By.CSS_SELECTOR, "calcite-button")

        driver.execute_script("arguments[0].click();", download_button)

        print("Download iniciado")

        time.sleep(30)

    finally:

        driver.quit()


if __name__ == "__main__":

    os.makedirs(CONFIG["DOWNLOAD_DIR"], exist_ok=True)

    run_rpa()