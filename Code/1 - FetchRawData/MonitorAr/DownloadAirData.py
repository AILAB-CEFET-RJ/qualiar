import time
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.data.rio/datasets/PCRJ::qualidade-do-ar-dados-hor%C3%A1rios/about?layer=2"
NOME_ARQUIVO_FINAL = "dados_qualidade_ar.parquet"
COLUNAS_REMOVER = [
    "rs",
    "dir_vento",
    "vel_vento",
    "hcnm",
    "hct",
    "ch4",
    "x_utm_sirgas2000",
    "y_utm_sirgas2000",
]

LOADER_XPATH = "/html/body/calcite-loader//div/svg[2]"
BOTAO_ABRIR_DOWNLOAD_XPATH = "/html/body/div[7]/div[2]/div/div[1]/div[2]/div/div/nav/div/div/div/button[3]"
LISTA_DOWNLOAD_XPATH = "/html/body/div[7]/div[2]/div/div[1]/div[1]/div/div/div/div[3]/arcgis-hub-download-list"


def pasta_download() -> Path:
    destino = Path(__file__).resolve().parents[3] / "Data" / "RawData" / "MonitorAr"
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def criar_driver(download_dir: Path) -> webdriver.Chrome:
    options = Options()
    options.add_experimental_option(
        "prefs",
        {
            "download.default_directory": str(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        },
    )

    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver


def esperar_download_csv(download_dir: Path, arquivos_antes: set[str], timeout: int = 600) -> Path:
    fim = time.time() + timeout

    while time.time() < fim:
        arquivos_agora = {arquivo.name for arquivo in download_dir.glob("*")}
        novos_arquivos = arquivos_agora - arquivos_antes

        if any(nome.endswith(".crdownload") for nome in novos_arquivos):
            time.sleep(1)
            continue

        csvs = [download_dir / nome for nome in novos_arquivos if nome.lower().endswith(".csv")]
        if csvs:
            return max(csvs, key=lambda arquivo: arquivo.stat().st_mtime)

        time.sleep(1)

    raise TimeoutError("O download do CSV demorou mais do que o esperado.")


def converter_csv_para_parquet(csv_path: Path) -> Path:
    parquet_path = csv_path.parent / NOME_ARQUIVO_FINAL

    print("Convertendo CSV para Parquet...")
    dataframe = pd.read_csv(csv_path)
    print("Removendo algumas colunas desnecessarias...")
    dataframe = dataframe.drop(columns=COLUNAS_REMOVER, errors="ignore")

    if parquet_path.exists():
        parquet_path.unlink()

    dataframe.to_parquet(parquet_path, index=False, compression="snappy")

    csv_path.unlink()
    return parquet_path


def clicar_opcao_csv_no_shadow_dom(driver: webdriver.Chrome) -> str:
    resultado = driver.execute_script(
        """
        const xpath = arguments[0];
        const lista = document.evaluate(
            xpath,
            document,
            null,
            XPathResult.FIRST_ORDERED_NODE_TYPE,
            null
        ).singleNodeValue;

        if (!lista) {
            return {ok: false, motivo: "Lista de download nao encontrada."};
        }

        if (!lista.shadowRoot) {
            return {ok: false, motivo: "A lista existe, mas nao possui shadowRoot aberto."};
        }

        const itens = Array.from(lista.shadowRoot.querySelectorAll("arcgis-hub-download-list-item"));
        const opcoes = [];

        for (const item of itens) {
            const itemRoot = item.shadowRoot;
            if (!itemRoot) {
                continue;
            }

            const titulo =
                itemRoot.querySelector(".download-option-card-title") ||
                itemRoot.querySelector("[class*='download-option-card-title']");

            const texto = (
                titulo?.textContent ||
                itemRoot.textContent ||
                item.textContent ||
                ""
            ).trim().toLowerCase();
            opcoes.push(texto);

            if (!texto.includes("csv")) {
                continue;
            }

            const calciteButton = itemRoot.querySelector("calcite-button");
            if (!calciteButton) {
                continue;
            }

            if (calciteButton.shadowRoot) {
                const botaoInterno = calciteButton.shadowRoot.querySelector("button");
                if (botaoInterno) {
                    botaoInterno.click();
                    return {ok: true, texto: texto, opcoes: opcoes};
                }
            }

            calciteButton.click();
            return {ok: true, texto: texto, opcoes: opcoes};
        }

        return {ok: false, motivo: "Nao encontrei a opcao CSV.", opcoes: opcoes};
        """,
        LISTA_DOWNLOAD_XPATH,
    )

    if not resultado["ok"]:
        opcoes = resultado.get("opcoes", [])
        raise RuntimeError(f'{resultado["motivo"]} Opcoes encontradas: {opcoes}')

    return resultado["texto"]


def main() -> None:
    download_dir = pasta_download()
    arquivos_antes = {arquivo.name for arquivo in download_dir.glob("*")}

    driver = criar_driver(download_dir)
    wait = WebDriverWait(driver, 60)

    try:
        print("Abrindo a pagina...")
        driver.get(URL)
        time.sleep(2)

        print("Esperando o loading desaparecer...")
        wait.until(EC.invisibility_of_element_located((By.XPATH, LOADER_XPATH)))
        time.sleep(2)

        print("Abrindo a aba de download...")
        botao_download = wait.until(
            EC.element_to_be_clickable((By.XPATH, BOTAO_ABRIR_DOWNLOAD_XPATH))
        )
        driver.execute_script("arguments[0].click();", botao_download)
        time.sleep(2)

        print("Procurando a opcao CSV...")
        wait.until(EC.presence_of_element_located((By.XPATH, LISTA_DOWNLOAD_XPATH)))
        time.sleep(2)
        texto_opcao = clicar_opcao_csv_no_shadow_dom(driver)
        print(f"Baixando a opcao: {texto_opcao}")

        arquivo_baixado = esperar_download_csv(download_dir, arquivos_antes)
        print(f"Download concluido: {arquivo_baixado}")
        arquivo_parquet = converter_csv_para_parquet(arquivo_baixado)
        print(f"Arquivo final salvo em: {arquivo_parquet}")
        time.sleep(5)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
