from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import pandas as pd
import os

# Função para realizar login automático
# - espera até que os campos de usuário e senha apareçam, preenche com variáveis de ambiente e submete
# - espera adicional após login para garantir carregamento do perfil
# Variáveis de ambiente necessárias:
#   LINKEDIN_USERNAME e LINKEDIN_PASSWORD
# Exemplo (Linux/macOS): export LINKEDIN_USERNAME='seu_email'; export LINKEDIN_PASSWORD='sua_senha'
def login(driver, wait_time=5):
    username = os.environ.get("LINKEDIN_USERNAME")
    password = os.environ.get("LINKEDIN_PASSWORD")
    if not username or not password:
        raise ValueError("Por favor, defina as variáveis de ambiente LINKEDIN_USERNAME e LINKEDIN_PASSWORD")
    driver.get("https://www.linkedin.com/login")
    # Aguarda campos de login
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "username"))
    )
    # Preenche credenciais
    driver.find_element(By.ID, "username").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    # Submete o formulário
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    # Aguarda até que o perfil ou barra de busca esteja disponível
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Pesquisar']"))
    )
    time.sleep(wait_time)

# Função para extrair dados das vagas de múltiplos termos de busca
# - max_pages: número máximo de páginas (escala de 25 em 25)
def scrape_jobs(driver, max_pages=40):
    # Define internamente a lista de palavras-chave
    keywords = [
        "analista BI", "analista dados", "cientista dados", "inteligência mercado",
        "analytics", "business intelligence", "analista negócios", "data analyst"
    ]

    resultados = []
    seen_ids = set()

    for keyword in keywords:
        print(f"Iniciando scraping para keyword: {keyword}")
        for page in range(max_pages):
            start = page * 25
            url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&start={start}"
            driver.get(url)

            # Aguarda carregamento inicial dos cards
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.job-card-container--clickable"))
            )
            time.sleep(2)

            # Scroll individual por cada <li> para carregar todos os cards
            li_items = driver.find_elements(By.CSS_SELECTOR, "li.scaffold-layout__list-item[data-occludable-job-id]")
            for li in li_items:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", li)
                    time.sleep(0.1)
                except:
                    continue

            # Coleta todos os cards carregados
            cards = driver.find_elements(By.CSS_SELECTOR, "div.job-card-container--clickable[data-job-id]")
            if not cards:
                print(f"Nenhum card encontrado para '{keyword}' na página {page + 1}. Encerrando este termo.")
                break

            for card in cards:
                job_id = card.get_attribute("data-job-id")
                if not job_id or job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                # Título da vaga
                try:
                    titulo = card.find_element(By.CSS_SELECTOR, "a.job-card-list__title--link").text.strip()
                except:
                    titulo = "<Título não encontrado>"

                # Clica no card e espera antes de coletar detalhes
                driver.execute_script("arguments[0].scrollIntoView(true);", card)
                card.click()
                time.sleep(random.uniform(2, 4))

                # Nome da empresa a partir do painel de detalhes
                try:
                    empresa = driver.find_element(
                        By.CSS_SELECTOR,
                        "div.job-details-jobs-unified-top-card__company-name a"
                    ).text.strip()
                except:
                    empresa = "<Empresa não encontrada>"

                # Coleta descrição do painel lateral
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.jobs-box__html-content#job-details"))
                    )
                    descricao = driver.find_element(
                        By.CSS_SELECTOR,
                        "div.jobs-box__html-content#job-details"
                    ).text.strip()
                except:
                    descricao = "<Descrição não disponível>"

                vaga_info = {
                    "job_id": job_id,
                    "titulo": titulo,
                    "empresa": empresa,
                    "descricao": descricao,
                    "keyword": keyword
                }
                # Loga cada vaga coletada no terminal
                print(vaga_info)
                resultados.append(vaga_info)

            print(f"Keyword '{keyword}': página {page + 1} processada. Total vagas até agora: {len(resultados)}.")
            time.sleep(2)
    return resultados

if __name__ == "__main__":
    # Configuração do driver em headless opcional
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome("/usr/bin/chromedriver", options=chrome_options)
    try:
        login(driver)
        # Executa scraping utilizando keywords definidas internamente
        all_jobs = scrape_jobs(driver, max_pages=40)

        # Cria DataFrame
        df = pd.DataFrame(all_jobs)

        # Define nome de arquivo sem sobrescrever versões existentes
        arquivo = "vagas_collected_multi.xlsx"
        base, ext = os.path.splitext(arquivo)
        i = 1
        while os.path.exists(arquivo):
            arquivo = f"{base}({i}){ext}"
            i += 1

        # Exporta para Excel
        df.to_excel(arquivo, index=False)
        print(f"Arquivo '{arquivo}' criado com sucesso com {len(all_jobs)} vagas.")
    finally:
        driver.quit()
