from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


CSV_URL = (
    "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/"
    "Refactoring-And-Documentation/Data/IntermediaryData/DataSus/"
    "respiratory_hospitalization_time_series_by_hospital.csv"
)
CNES_URL = "https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp"
OUTPUT_CSV_PATH = (
    "Data/IntermediaryData/DataSus/"
    "respiratory_hospitalization_time_series_by_hospital_with_endereco.csv"
)

# XPaths solicitados pelo usuario
XPATH_INPUT_CNES = "/html/body/div[2]/main/div/div[2]/div/form[2]/div/input"
XPATH_BUTTON_SEARCH_CNES = "/html/body/div[2]/main/div/div[2]/div/form[2]/div/button"
XPATH_BUTTON_INFO_ESTABELECIMENTO = (
    "/html/body/div[2]/main/div/div[2]/div/div[3]/table/tbody/tr/td[8]/button"
)
XPATH_LOGRADOURO_INFO = (
    "/html/body/div[2]/main/div/div[2]/div/div[4]/div/div/div[2]/div/form/div[3]/div[1]/div/input"
)
XPATH_NUMERO_INFO = (
    "/html/body/div[2]/main/div/div[2]/div/div[4]/div/div/div[2]/div/form/div[3]/div[2]/div/input"
)
XPATH_CLOSE_INFO_ESTABELECIMENTO = (
    "/html/body/div[2]/main/div/div[2]/div/div[4]/div/div/div[3]/button"
)


LOCATORS = {
    "input_cnes": [
        (By.XPATH, XPATH_INPUT_CNES),
        (By.XPATH, "//form[2]//input"),
    ],
    "button_search": [
        (By.XPATH, XPATH_BUTTON_SEARCH_CNES),
        (By.XPATH, "//form[2]//button"),
    ],
    "button_info": [
        (By.XPATH, XPATH_BUTTON_INFO_ESTABELECIMENTO),
        (By.XPATH, "//table/tbody/tr[1]/td[last()]//button"),
    ],
    "logradouro_info": [
        (By.XPATH, XPATH_LOGRADOURO_INFO),
        (By.XPATH, "//div[contains(@class,'modal')]//input[contains(@id,'logradouro')]"),
    ],
    "numero_info": [
        (By.XPATH, XPATH_NUMERO_INFO),
        (By.XPATH, "//div[contains(@class,'modal')]//input[contains(@id,'numero')]"),
    ],
    "close_modal": [
        (By.XPATH, XPATH_CLOSE_INFO_ESTABELECIMENTO),
        (By.XPATH, "//div[contains(@class,'modal')]//button[contains(., 'Fechar')]"),
    ],
}


MAX_TENTATIVAS_POR_CNES = 3
PAGE_TIMEOUT = 30
DEFAULT_WAIT = 20
RESULT_WAIT = 12
MODAL_WAIT = 12
HEADLESS = False

STATUS_ENCONTRADO = "Encontrado"
STATUS_NAO_ENCONTRADO = "Não encontrado"
STATUS_ERRO = "Erro na consulta"
STATUS_NAO_CONSULTADO = "Não consultado (CNES vazio)"


def normalizar_cnes(valor: object) -> Optional[str]:
    if pd.isna(valor):
        return None

    texto = str(valor).strip()
    if not texto:
        return None

    texto = re.sub(r"\.0+$", "", texto)
    texto = re.sub(r"\s+", "", texto)

    if texto.isdigit():
        return texto.zfill(7)

    return texto


def carregar_dataframe(csv_url: str) -> pd.DataFrame:
    print("Lendo CSV remoto...")
    df = pd.read_csv(csv_url, dtype={"CNES": "string"}, encoding="utf-8")

    if "CNES" not in df.columns:
        raise KeyError(
            "A coluna 'CNES' nao existe no CSV informado. "
            "Verifique a fonte ou gere o arquivo com CNES antes do scraping."
        )

    df["CNES"] = df["CNES"].map(normalizar_cnes).astype("string")
    total = len(df)
    unicos = df["CNES"].dropna().nunique()
    vazios = int(df["CNES"].isna().sum())
    print(f"Linhas totais: {total}")
    print(f"CNES unicos: {unicos}")
    print(f"Linhas com CNES vazio: {vazios}")
    return df


def extrair_cnes_unicos(df: pd.DataFrame) -> List[str]:
    cnes_unicos = df["CNES"].dropna().drop_duplicates().tolist()
    print(f"Total de CNES para consulta unica: {len(cnes_unicos)}")
    return cnes_unicos


def configurar_driver(headless: bool = False) -> webdriver.Chrome:
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    if headless:
        options.add_argument("--headless=new")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(PAGE_TIMEOUT)
    return driver


def esperar_elemento(
    driver: webdriver.Chrome,
    locators: Sequence[Tuple[str, str]],
    timeout: int,
    condition,
):
    ultimo_erro: Optional[Exception] = None

    for locator in locators:
        try:
            return WebDriverWait(driver, timeout).until(condition(locator))
        except TimeoutException as erro:
            ultimo_erro = erro
            continue

    raise TimeoutException(
        f"Nao foi possivel localizar elemento com os locators: {locators}"
    ) from ultimo_erro


def limpar_e_preencher_input(input_element, valor: str) -> None:
    input_element.click()
    input_element.send_keys(Keys.CONTROL, "a")
    input_element.send_keys(Keys.DELETE)
    input_element.clear()
    input_element.send_keys(valor)


def fechar_modal(driver: webdriver.Chrome) -> None:
    try:
        botao_fechar = esperar_elemento(
            driver=driver,
            locators=LOCATORS["close_modal"],
            timeout=6,
            condition=EC.element_to_be_clickable,
        )
        botao_fechar.click()
    except Exception:
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        except Exception:
            pass

    try:
        WebDriverWait(driver, 6).until(
            EC.invisibility_of_element_located(LOCATORS["logradouro_info"][0])
        )
    except TimeoutException:
        pass


def consultar_cnes(
    driver: webdriver.Chrome,
    cnes: str,
    indice: int,
    total: int,
    max_tentativas: int = MAX_TENTATIVAS_POR_CNES,
) -> Dict[str, Optional[str]]:
    houve_erro = False
    houve_nao_encontrado = False

    for tentativa in range(1, max_tentativas + 1):
        print(
            f"[{indice}/{total}] Consultando CNES {cnes} "
            f"(tentativa {tentativa}/{max_tentativas})"
        )

        try:
            driver.get(CNES_URL)

            input_cnes = esperar_elemento(
                driver=driver,
                locators=LOCATORS["input_cnes"],
                timeout=DEFAULT_WAIT,
                condition=EC.element_to_be_clickable,
            )
            limpar_e_preencher_input(input_cnes, cnes)

            button_search = esperar_elemento(
                driver=driver,
                locators=LOCATORS["button_search"],
                timeout=DEFAULT_WAIT,
                condition=EC.element_to_be_clickable,
            )
            button_search.click()

            try:
                button_info = esperar_elemento(
                    driver=driver,
                    locators=LOCATORS["button_info"],
                    timeout=RESULT_WAIT,
                    condition=EC.element_to_be_clickable,
                )
            except TimeoutException:
                houve_nao_encontrado = True
                print(f"  - CNES {cnes}: nao encontrado nesta tentativa.")
                continue

            button_info.click()

            logradouro_input = esperar_elemento(
                driver=driver,
                locators=LOCATORS["logradouro_info"],
                timeout=MODAL_WAIT,
                condition=EC.visibility_of_element_located,
            )
            numero_input = esperar_elemento(
                driver=driver,
                locators=LOCATORS["numero_info"],
                timeout=MODAL_WAIT,
                condition=EC.visibility_of_element_located,
            )

            logradouro = (logradouro_input.get_attribute("value") or "").strip()
            numero = (numero_input.get_attribute("value") or "").strip()

            fechar_modal(driver)

            print(
                "  - Encontrado | "
                f"Logradouro: {logradouro if logradouro else '[vazio]'} | "
                f"Numero: {numero if numero else '[vazio]'}"
            )

            return {
                "CNES": cnes,
                "Logradouro": logradouro or None,
                "Numero": numero or None,
                "Status_Busca_CNES": STATUS_ENCONTRADO,
            }

        except (TimeoutException, WebDriverException) as erro:
            houve_erro = True
            print(
                f"  - Erro de consulta para CNES {cnes} na tentativa {tentativa}: {erro}"
            )
            fechar_modal(driver)
            continue
        except Exception as erro:
            houve_erro = True
            print(
                f"  - Erro inesperado para CNES {cnes} na tentativa {tentativa}: {erro}"
            )
            fechar_modal(driver)
            continue

    if houve_nao_encontrado and not houve_erro:
        print(f"  - CNES {cnes}: nao encontrado apos {max_tentativas} tentativa(s).")
        return {
            "CNES": cnes,
            "Logradouro": None,
            "Numero": None,
            "Status_Busca_CNES": STATUS_NAO_ENCONTRADO,
        }

    print(f"  - CNES {cnes}: erro apos {max_tentativas} tentativa(s).")
    return {
        "CNES": cnes,
        "Logradouro": None,
        "Numero": None,
        "Status_Busca_CNES": STATUS_ERRO,
    }


def consultar_todos_cnes(
    driver: webdriver.Chrome,
    cnes_unicos: Sequence[str],
    max_tentativas: int = MAX_TENTATIVAS_POR_CNES,
) -> pd.DataFrame:
    resultados: List[Dict[str, Optional[str]]] = []
    total = len(cnes_unicos)

    for indice, cnes in enumerate(cnes_unicos, start=1):
        resultado = consultar_cnes(
            driver=driver,
            cnes=cnes,
            indice=indice,
            total=total,
            max_tentativas=max_tentativas,
        )
        resultados.append(resultado)

    return pd.DataFrame(
        resultados, columns=["CNES", "Logradouro", "Numero", "Status_Busca_CNES"]
    )


def montar_endereco(logradouro: str, numero: str) -> str:
    log = (logradouro or "").strip()
    num = (numero or "").strip()

    if log and num:
        return f"{log}, {num}"
    if log:
        return log
    if num:
        return num
    return ""


def enriquecer_dataframe(df_original: pd.DataFrame, df_enderecos: pd.DataFrame) -> pd.DataFrame:
    df_saida = df_original.copy()
    df_saida["CNES"] = df_saida["CNES"].map(normalizar_cnes).astype("string")

    df_aux = df_enderecos.copy()
    df_aux["CNES"] = df_aux["CNES"].astype("string")

    df_saida = df_saida.merge(df_aux, on="CNES", how="left", validate="m:1")
    df_saida["Status_Busca_CNES"] = df_saida["Status_Busca_CNES"].fillna(STATUS_NAO_CONSULTADO)

    for coluna in ["Logradouro", "Numero"]:
        df_saida[coluna] = df_saida[coluna].fillna("").astype(str).str.strip()

    df_saida["Endereco"] = [
        montar_endereco(logradouro, numero)
        for logradouro, numero in zip(df_saida["Logradouro"], df_saida["Numero"])
    ]

    return df_saida


def salvar_resultado(df_final: pd.DataFrame, output_path: str) -> Path:
    caminho_saida = Path(output_path)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(caminho_saida, index=False, encoding="utf-8")
    print(f"CSV salvo em: {caminho_saida.resolve()}")
    return caminho_saida


def main() -> None:
    df_original = carregar_dataframe(CSV_URL)
    cnes_unicos = extrair_cnes_unicos(df_original)

    if not cnes_unicos:
        print("Nenhum CNES valido encontrado. Salvando somente com colunas vazias.")
        df_vazio = df_original.copy()
        df_vazio["Logradouro"] = ""
        df_vazio["Numero"] = ""
        df_vazio["Endereco"] = ""
        df_vazio["Status_Busca_CNES"] = STATUS_NAO_CONSULTADO
        salvar_resultado(df_vazio, OUTPUT_CSV_PATH)
        return

    driver: Optional[webdriver.Chrome] = None
    try:
        driver = configurar_driver(headless=HEADLESS)
        df_enderecos = consultar_todos_cnes(driver, cnes_unicos)
    finally:
        if driver is not None:
            driver.quit()
            print("Navegador fechado.")

    df_final = enriquecer_dataframe(df_original, df_enderecos)
    salvar_resultado(df_final, OUTPUT_CSV_PATH)
    print("Processo finalizado com sucesso.")


if __name__ == "__main__":
    main()
