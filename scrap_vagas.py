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

# Função para extrair dados das vagas de um termo de busca
# - keyword: termo de busca
# - max_pages: número máximo de páginas de resultados (escala de 25 em 25)
def scrape_jobs(driver, keyword, max_pages=40):
    resultados = []
    seen_ids = set()

    for page in range(max_pages):
        start = page * 25
        url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&start={start}"
        driver.get(url)

        # Aguarda carregamento do primeiro card clicável
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

            # Armazena resultado com o termo de busca
            resultados.append({
                "job_id": job_id,
                "titulo": titulo,
                "empresa": empresa,
                "descricao": descricao,
                "keyword": keyword
            })

        print(f"Termo '{keyword}': página {page + 1} processada. Vagas até agora: {len(resultados)}.")
        time.sleep(2)

    return resultados

if __name__ == "__main__":
    # Configuração do driver (Edge ou Chrome)
    driver = webdriver.Edge()  # ou webdriver.Chrome()
    try:
        login(driver)
        # Lista de termos de busca
        keywords = ["analista BI", "analista dados", "cientista dados", "inteligência mercado", "analytics", "business intelligence", "analista negócios", "data analyst"]  # adicione/remova termos conforme necessidade

        all_jobs = []
        seen_main = set()
        for kw in keywords:
            print(f"Iniciando scraping para keyword: {kw}")
            vagas_kw = scrape_jobs(driver, keyword=kw, max_pages=40)
            for vaga in vagas_kw:
                jid = vaga["job_id"]
                if jid not in seen_main:
                    seen_main.add(jid)
                    all_jobs.append(vaga)

        # Cria DataFrame com todos os resultados
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
