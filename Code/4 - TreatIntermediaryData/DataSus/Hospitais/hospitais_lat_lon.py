from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd
import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


PARQUET_URL = (
    "https://raw.githubusercontent.com/AILAB-CEFET-RJ/qualiar/refs/heads/"
    "Refactoring-And-Documentation/Data/IntermediaryData/DataSus/"
    "respiratory_hospitalization_time_series_by_hospital.parquet"
)
CNES_URL = "https://cnes.datasus.gov.br/pages/estabelecimentos/consulta.jsp"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

OUTPUT_PARQUET_PATH = (
    "Data/IntermediaryData/DataSus/"
    "respiratory_hospitalization_time_series_by_hospital_with_endereco.parquet"
)

XPATH_INPUT_CNES = "/html/body/div[2]/main/div/div[2]/div/form[2]/div/input"
XPATH_BUTTON_SEARCH_CNES = "/html/body/div[2]/main/div/div[2]/div/form[2]/div/button"
XPATH_BUTTON_INFO_ESTABELECIMENTO = (
    "/html/body/div[2]/main/div/div[2]/div/div[3]/table/tbody/tr/td[8]/button"
)
XPATH_NOME_HOSP_INFO = (
    "/html/body/div[2]/main/div/div[2]/div/div[4]/div/div/div[2]/div/form/div[1]/div[1]/div/input"
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
    "nome_hosp_info": [
        (By.XPATH, XPATH_NOME_HOSP_INFO),
        (By.XPATH, "//div[contains(@class,'modal')]//input[contains(@id,'nome')]"),
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

NOMINATIM_TIMEOUT = 20
NOMINATIM_MAX_TENTATIVAS = 3
NOMINATIM_MIN_INTERVALO_SEG = 1.1
NOMINATIM_USER_AGENT = (
    "qualiar-geocoder/1.0 (AILAB-CEFET-RJ; projeto-qualiar)"
)

STATUS_ENCONTRADO = "Encontrado"
STATUS_NAO_ENCONTRADO = "Nao encontrado"
STATUS_ERRO = "Erro na consulta"
STATUS_NAO_CONSULTADO = "Nao consultado (CNES vazio)"

AJUSTES_MANUAIS_POR_CNES: Dict[str, Dict[str, str]] = {
    "2296748": {"Logradouro": "RUA DUALMA RIBEIRO ANDRADE"},
    "2273187": {"NOME_HOSP": "HOSPITAL MUNICIPAL ALVARO RAMOS"},
    "2273349": {"NOME_HOSP": "HOSPITAL MUNICIPAL RAPHAEL DE PAULA SOUZA"},
    "2270390": {"NOME_HOSP": "HOSPITAL MATERNIDADE HERCULANO PINHEIRO"},
    "2289709": {"Logradouro": "AVENIDA BENJAMIN PINTO DIAS"},
    "2296764": {"Logradouro": "AVENIDA BENJAMIN PINTO DIAS"},
    "2269481": {"NOME_HOSP": "HOSPITAL MUNICIPAL DA PIEDADE"},
    "2270234": {"NOME_HOSP": "HOSPITAL ESTADUAL GETULIO"},
    "2269724": {"NOME_HOSP": "HOSPITAL MUNICIPAL NOSSA SENHORA DO LORETO"},
    "2273411": {"NOME_HOSP": "HOSPITAL ESTADUAL CARLOS CHAGAS"},
}


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


def normalizar_texto(valor: object) -> str:
    if valor is None:
        return ""
    if pd.isna(valor):
        return ""
    return str(valor).strip()


def carregar_dataframe(parquet_url: str) -> pd.DataFrame:
    print("Lendo Parquet remoto...")
    df = pd.read_parquet(parquet_url)

    if "CNES" not in df.columns:
        raise KeyError(
            "A coluna 'CNES' nao existe no Parquet informado. "
            "Verifique a fonte antes de executar o scraping."
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
            EC.invisibility_of_element_located(LOCATORS["close_modal"][0])
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

            nome_hosp_input = esperar_elemento(
                driver=driver,
                locators=LOCATORS["nome_hosp_info"],
                timeout=MODAL_WAIT,
                condition=EC.visibility_of_element_located,
            )
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

            nome_hosp = normalizar_texto(nome_hosp_input.get_attribute("value"))
            logradouro = normalizar_texto(logradouro_input.get_attribute("value"))
            numero = normalizar_texto(numero_input.get_attribute("value"))

            fechar_modal(driver)

            print(
                "  - Encontrado | "
                f"Nome: {nome_hosp if nome_hosp else '[vazio]'} | "
                f"Logradouro: {logradouro if logradouro else '[vazio]'} | "
                f"Numero: {numero if numero else '[vazio]'}"
            )

            return {
                "CNES": cnes,
                "NOME_HOSP": nome_hosp or None,
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
            "NOME_HOSP": None,
            "Logradouro": None,
            "Numero": None,
            "Status_Busca_CNES": STATUS_NAO_ENCONTRADO,
        }

    print(f"  - CNES {cnes}: erro apos {max_tentativas} tentativa(s).")
    return {
        "CNES": cnes,
        "NOME_HOSP": None,
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
        resultados,
        columns=["CNES", "NOME_HOSP", "Logradouro", "Numero", "Status_Busca_CNES"],
    )


def aplicar_ajustes_manuais(df_consultas: pd.DataFrame) -> pd.DataFrame:
    df_ajustado = df_consultas.copy()
    df_ajustado["Ajuste_Manual"] = False
    df_ajustado["Campos_Ajustados"] = ""

    print("Aplicando ajustes manuais de CNES (quando houver)...")
    for cnes, ajustes in AJUSTES_MANUAIS_POR_CNES.items():
        mask = df_ajustado["CNES"].astype("string") == cnes
        if not mask.any():
            print(f"  - CNES {cnes}: nao presente na lista consultada.")
            continue

        campos_alterados: List[str] = []
        for campo, novo_valor in ajustes.items():
            valor_atual = normalizar_texto(df_ajustado.loc[mask, campo].iloc[0])
            if valor_atual != novo_valor:
                df_ajustado.loc[mask, campo] = novo_valor
                campos_alterados.append(campo)

        if campos_alterados:
            df_ajustado.loc[mask, "Ajuste_Manual"] = True
            df_ajustado.loc[mask, "Campos_Ajustados"] = ",".join(campos_alterados)
            print(
                f"  - CNES {cnes}: ajuste aplicado em {', '.join(campos_alterados)}."
            )
        else:
            print(f"  - CNES {cnes}: valor ja estava igual ao ajuste manual.")

    return df_ajustado


def montar_endereco(logradouro: str, numero: str) -> str:
    log = normalizar_texto(logradouro)
    num = normalizar_texto(numero)

    if log and num:
        return f"{log}, {num}"
    if log:
        return log
    if num:
        return num
    return ""


class NominatimClient:
    def __init__(
        self,
        timeout: int = NOMINATIM_TIMEOUT,
        min_intervalo_seg: float = NOMINATIM_MIN_INTERVALO_SEG,
        max_tentativas: int = NOMINATIM_MAX_TENTATIVAS,
    ) -> None:
        self.timeout = timeout
        self.min_intervalo_seg = min_intervalo_seg
        self.max_tentativas = max_tentativas
        self.ultima_requisicao_ts = 0.0
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": NOMINATIM_USER_AGENT,
                "Accept": "application/json",
            }
        )

    def _respeitar_intervalo(self) -> None:
        agora = time.monotonic()
        decorrido = agora - self.ultima_requisicao_ts
        if decorrido < self.min_intervalo_seg:
            time.sleep(self.min_intervalo_seg - decorrido)
        self.ultima_requisicao_ts = time.monotonic()

    def buscar(
        self,
        amenity: Optional[str] = None,
        street: Optional[str] = None,
    ) -> List[Dict[str, object]]:
        if not amenity and not street:
            return []

        params: Dict[str, str] = {
            "polygon_geojson": "1",
            "format": "jsonv2",
        }
        if amenity:
            params["amenity"] = amenity
        if street:
            params["street"] = street

        for tentativa in range(1, self.max_tentativas + 1):
            try:
                self._respeitar_intervalo()
                resp = self.session.get(
                    NOMINATIM_URL,
                    params=params,
                    timeout=self.timeout,
                )

                if resp.status_code == 200:
                    data = resp.json()
                    return data if isinstance(data, list) else []

                if resp.status_code in {429, 500, 502, 503, 504}:
                    print(
                        f"  - Nominatim HTTP {resp.status_code} "
                        f"(tentativa {tentativa}/{self.max_tentativas})"
                    )
                    continue

                print(f"  - Nominatim retorno inesperado HTTP {resp.status_code}.")
                return []

            except requests.RequestException as erro:
                print(
                    f"  - Erro de rede no Nominatim "
                    f"(tentativa {tentativa}/{self.max_tentativas}): {erro}"
                )
                continue
            except ValueError as erro:
                print(f"  - Falha ao decodificar JSON do Nominatim: {erro}")
                return []

        return []

    def close(self) -> None:
        self.session.close()


def extrair_lat_lon(
    resultados: Sequence[Dict[str, object]],
) -> Tuple[Optional[float], Optional[float]]:
    if not resultados:
        return None, None

    candidato: Optional[Dict[str, object]] = None
    for item in resultados:
        if str(item.get("type", "")).lower() == "hospital":
            candidato = item
            break

    if candidato is None:
        candidato = resultados[0]

    lat_raw = candidato.get("lat")
    lon_raw = candidato.get("lon")

    try:
        lat = float(str(lat_raw)) if lat_raw not in (None, "") else None
        lon = float(str(lon_raw)) if lon_raw not in (None, "") else None
    except ValueError:
        return None, None

    return lat, lon


def obter_lat_lon(
    client: NominatimClient,
    nome_hosp: str,
    logradouro: str,
    numero: str,
) -> Tuple[Optional[float], Optional[float], str]:
    nome = normalizar_texto(nome_hosp)
    rua = montar_endereco(logradouro, numero)

    if nome:
        resultados_nome = client.buscar(amenity=nome)
        lat, lon = extrair_lat_lon(resultados_nome)
        if lat is not None and lon is not None:
            return lat, lon, "amenity"

    if rua:
        resultados_rua = client.buscar(street=rua)
        lat, lon = extrair_lat_lon(resultados_rua)
        if lat is not None and lon is not None:
            return lat, lon, "street"

    return None, None, "nao_encontrado"


def enriquecer_lat_lon(df_consultas: pd.DataFrame) -> pd.DataFrame:
    df_geo = df_consultas.copy()
    df_geo["Latitude"] = None
    df_geo["Longitude"] = None

    total = len(df_geo)
    client = NominatimClient()

    try:
        for indice, row in enumerate(df_geo.itertuples(index=True), start=1):
            cnes = normalizar_texto(row.CNES)
            nome_hosp = normalizar_texto(row.NOME_HOSP)
            logradouro = normalizar_texto(row.Logradouro)
            numero = normalizar_texto(row.Numero)
            ajuste_manual = bool(getattr(row, "Ajuste_Manual", False))
            campos_ajustados = normalizar_texto(getattr(row, "Campos_Ajustados", ""))
            status_ajuste = "SIM" if ajuste_manual else "NAO"

            print(
                f"[{indice}/{total}] Geocodificando CNES {cnes} | "
                f"Manipulado: {status_ajuste}"
            )
            if ajuste_manual and campos_ajustados:
                print(f"  - Campos manipulados: {campos_ajustados}")

            lat, lon, metodo = obter_lat_lon(
                client=client,
                nome_hosp=nome_hosp,
                logradouro=logradouro,
                numero=numero,
            )

            df_geo.at[row.Index, "Latitude"] = lat
            df_geo.at[row.Index, "Longitude"] = lon

            if lat is not None and lon is not None:
                print(f"  - Geocode encontrado ({metodo}) | lat={lat} lon={lon}")
            else:
                print("  - Geocode nao encontrado.")
    finally:
        client.close()

    return df_geo


def enriquecer_dataframe(df_original: pd.DataFrame, df_enderecos: pd.DataFrame) -> pd.DataFrame:
    df_saida = df_original.copy()
    df_saida["CNES"] = df_saida["CNES"].map(normalizar_cnes).astype("string")

    df_aux = df_enderecos.copy()
    df_aux["CNES"] = df_aux["CNES"].astype("string")

    df_saida = df_saida.merge(df_aux, on="CNES", how="left", validate="m:1")
    df_saida["Status_Busca_CNES"] = df_saida["Status_Busca_CNES"].fillna(
        STATUS_NAO_CONSULTADO
    )

    for coluna in ["NOME_HOSP", "Logradouro", "Numero"]:
        df_saida[coluna] = df_saida[coluna].fillna("").astype(str).str.strip()

    df_saida["Endereco"] = [
        montar_endereco(logradouro, numero)
        for logradouro, numero in zip(df_saida["Logradouro"], df_saida["Numero"])
    ]

    df_saida["Latitude"] = pd.to_numeric(df_saida["Latitude"], errors="coerce")
    df_saida["Longitude"] = pd.to_numeric(df_saida["Longitude"], errors="coerce")
    return df_saida


def organizar_saida_final(df: pd.DataFrame) -> pd.DataFrame:
    colunas_obrigatorias = ["CNES", "data_dia", "num_internacoes", "Latitude", "Longitude"]
    faltantes = [col for col in colunas_obrigatorias if col not in df.columns]
    if faltantes:
        raise KeyError(
            "Colunas obrigatorias ausentes para saida final: "
            + ", ".join(faltantes)
        )

    df_saida = df.copy()
    df_saida["LAT"] = pd.to_numeric(df_saida["Latitude"], errors="coerce")
    df_saida["LON"] = pd.to_numeric(df_saida["Longitude"], errors="coerce")
    df_saida = df_saida[["CNES", "data_dia", "num_internacoes", "LAT", "LON"]]
    return df_saida


def salvar_resultado(df_final: pd.DataFrame, output_path: str) -> Path:
    caminho_saida = Path(output_path)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_parquet(caminho_saida, index=False)
    print(f"Parquet salvo em: {caminho_saida.resolve()}")
    return caminho_saida


def main() -> None:
    df_original = carregar_dataframe(PARQUET_URL)
    cnes_unicos = extrair_cnes_unicos(df_original)

    if not cnes_unicos:
        print("Nenhum CNES valido encontrado. Salvando somente com colunas vazias.")
        df_vazio = df_original.copy()
        df_vazio["Latitude"] = None
        df_vazio["Longitude"] = None
        df_saida = organizar_saida_final(df_vazio)
        salvar_resultado(df_saida, OUTPUT_PARQUET_PATH)
        return

    driver: Optional[webdriver.Chrome] = None
    try:
        driver = configurar_driver(headless=HEADLESS)
        df_consultas = consultar_todos_cnes(driver, cnes_unicos)
    finally:
        if driver is not None:
            driver.quit()
            print("Navegador fechado.")

    df_consultas = aplicar_ajustes_manuais(df_consultas)
    df_consultas = enriquecer_lat_lon(df_consultas)
    df_enriquecido = enriquecer_dataframe(df_original, df_consultas)
    df_saida = organizar_saida_final(df_enriquecido)
    salvar_resultado(df_saida, OUTPUT_PARQUET_PATH)
    print("Processo finalizado com sucesso.")


if __name__ == "__main__":
    main()
