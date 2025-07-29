from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import pandas as pd
import os

# Função para realizar login manual
# - wait_time: segundos para pausa após abrir a página de login
def login(driver, wait_time=15):
    driver.get("https://www.linkedin.com/login")
    print("Faça login manualmente no LinkedIn...")
    time.sleep(wait_time)

# Função para extrair dados das vagas
# - keyword: termo de busca
# - max_pages: número máximo de páginas de resultados (escala de 25 em 25)
def scrape_jobs(driver, keyword, max_pages=40):
    resultados = []
    seen_ids = set()

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
            print(f"Nenhum card encontrado na página {page + 1}. Encerrando.")
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
                "descricao": descricao
            }
            print(vaga_info)
            resultados.append(vaga_info)

        print(f"Página {page + 1} processada. Coletadas até agora: {len(resultados)} vagas.")
        time.sleep(2)

    return resultados

if __name__ == "__main__":
    # Configuração do driver (Edge ou Chrome)
    driver = webdriver.Edge()  # ou webdriver.Chrome()
    try:
        login(driver)
        vagas = scrape_jobs(driver, keyword="BI", max_pages=40)

        # Cria DataFrame
        df = pd.DataFrame(vagas)

        # Define nome de arquivo sem sobrescrever versões existentes
        arquivo = "vagas_collected3.xlsx"
        base, ext = os.path.splitext(arquivo)
        i = 1
        while os.path.exists(arquivo):
            arquivo = f"{base}({i}){ext}"
            i += 1

        # Exporta para Excel
        df.to_excel(arquivo, index=False)
        print(f"Arquivo '{arquivo}' criado com sucesso com {len(vagas)} vagas.")

    finally:
        driver.quit()
