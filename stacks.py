import os
import pandas as pd
from groq import Groq
import httpx

# --- CONFIGURAÇÃO DO CLIENTE GROQ ---
transport = httpx.HTTPTransport(verify=False)
http_client = httpx.Client(transport=transport)

cliente = Groq(
    api_key=os.getenv("GROQ_API_KEY", "seu_api_key_aqui"),
    http_client=http_client
)

MODEL = "llama3-8b-8192"  # ou outro modelo compatível

# --- LEITURA DO EXCEL DE ENTRADA ---
input_path = "vagas.xlsx"  # ajuste conforme necessário
df = pd.read_excel(input_path)

# --- PROCESSAMENTO E CHAMADAS AO GROQ ---
results = []
for _, row in df.iterrows():
    id_vaga    = row["id"]
    descricao  = row["descricao"]
    prompt     = (
        "Analise esta descrição de vaga do LinkedIn "
        "e liste as tecnologias (stacks) solicitadas. "
        "retorne apenas o nome das stacks, separadas por vírgula:\n\n"
        f"{descricao}"
    )
    resp = cliente.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODEL
    )
    content = resp.choices[0].message.content.strip()
    stacks  = [s.strip() for s in content.split(",") if s.strip()]
    for stack in stacks:
        results.append({"id": id_vaga, "stack": stack})

# --- CRIAÇÃO DO DATAFRAME “PIVOT” E EXPORTAÇÃO ---
result_df = pd.DataFrame(results)

# --- DEFINIÇÃO DE OUTPUT PATH SEM SOBREPOSIÇÃO ---
output_path = "vagas_stacks_pivot.xlsx"
base, ext = os.path.splitext(output_path)
counter = 1
new_path = output_path
while os.path.exists(new_path):
    new_path = f"{base}_{counter}{ext}"
    counter += 1
output_path = new_path

result_df.to_excel(output_path, index=False)
print(f"Gerado: {output_path} ({len(result_df)} linhas)")
