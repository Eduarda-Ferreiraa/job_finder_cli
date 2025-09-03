import typer
import requests
import json
import csv
import re
from datetime import datetime
from typing import Optional, List
from collections import Counter
from bs4 import BeautifulSoup

app = typer.Typer()

URL = "https://api.itjobs.pt/job/list.json?api_key=7948cb253161333d9cd4634fa957cc86"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ========================================================
# Funções auxiliares
# ========================================================
def limpar_html(texto_html: str) -> str:
    """Remove tags HTML de uma string"""
    texto_limpo = re.sub(r"<[^>]+>", "", texto_html)
    return texto_limpo.strip()

def export_to_csv(data: List[dict], filename: str):
    """Exporta uma lista de dicionários para CSV"""
    try:
        if not data:
            print("Nenhum dado para exportar.")
            return
        fieldnames = data[0].keys()
        with open(filename, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        print(f"CSV '{filename}' criado com sucesso!")
    except Exception as e:
        print(f"Erro ao criar o CSV: {e}")

def extract_wage(job_data: dict) -> str:
    """Extrai salários de um job (campo wage ou texto body via regex)"""
    wage = job_data.get("wage")
    if wage:
        return f"Salário encontrado no campo específico: {wage}"
    body_text = job_data.get("body", "")
    salary_patterns = re.findall(r"(\€|\$|USD|EUR)?\s?\d+[.,]?\d*\s?(k|mil|m)?\s?(\€|\$|USD|EUR)?", body_text, re.IGNORECASE)
    if salary_patterns:
        matches = [" ".join(p).strip() for p in salary_patterns]
        return f"Salário(s) encontrado(s) no campo 'body': {', '.join(matches)}"
    return "Salário não encontrado em nenhum campo."

# ========================================================
# Parte 1 – API itjobs.pt
# ========================================================
@app.command()
def listar_n_trabalhos(n: int, export_csv: Optional[str] = None):
    response = requests.get(URL, headers=HEADERS)
    jobs = response.json().get("results", [])
    ordenados = sorted(jobs, key=lambda job: datetime.strptime(job["publishedAt"], "%Y-%m-%d %H:%M:%S"), reverse=True)
    mais_recentes = ordenados[:n]

    n_recentes = [{
        "id": job.get("id", "N/A"),
        "titulo": job.get("title", "N/A"),
        "empresa": job.get("company", {}).get("name", "N/A"),
        "descrição": limpar_html(job.get("body", "N/A")),
        "data de publicação": job.get("publishedAt", "N/A"),
        "salário": job.get("wage", "N/A"),
        "localização": "; ".join(loc.get("name", "N/A") for loc in job.get("locations", []))
    } for job in mais_recentes]

    print("Trabalhos mais recentes:")
    for job in mais_recentes:
        print(f"- {job.get('title')} (Publicado em: {job.get('publishedAt')})")

    if export_csv:
        export_to_csv(n_recentes, export_csv)

@app.command()
def full_time_emp(company: str, location: str, limit: int, export_csv: Optional[str] = None):
    response = requests.get(URL, headers=HEADERS)
    jobs = response.json().get("results", [])

    company, location = company.lower(), location.lower()
    filtered_jobs = []
    for job in jobs:
        if job.get("company", {}).get("name", "").lower() == company:
            if any(t["name"] == "Full-time" for t in job.get("types", [])) and \
               any(l["name"].lower() == location for l in job.get("locations", [])):
                filtered_jobs.append({
                    "id": job["id"],
                    "titulo": job["title"],
                    "empresa": job["company"]["name"],
                    "descrição": limpar_html(job["body"]),
                    "data de publicação": job["publishedAt"],
                    "salário": job.get("wage", "N/A"),
                    "localização": "; ".join(loc["name"] for loc in job.get("locations", []))
                })
    filtered_jobs = filtered_jobs[:limit]
    if not filtered_jobs:
        typer.echo(f"Não foram encontrados empregos do tipo 'Full-time' em '{location}' para a empresa '{company}'.")
    else:
        print(json.dumps(filtered_jobs, indent=2, ensure_ascii=False))
    if export_csv:
        export_to_csv(filtered_jobs, export_csv)

@app.command()
def salary(job_id: int):
    response = requests.get(URL, headers=HEADERS)
    jobs = response.json().get("results", [])
    job_data = next((job for job in jobs if job["id"] == job_id), None)
    if not job_data:
        typer.echo(f"Job ID {job_id} não encontrado.")
        raise typer.Exit()
    typer.echo(extract_wage(job_data))

@app.command()
def skills(skill: List[str], datainicial: str, datafinal: str, export_csv: Optional[str] = None):
    response = requests.get(URL, headers=HEADERS)
    jobs = response.json().get("results", [])
    datainicial = datetime.strptime(datainicial, "%Y-%m-%d")
    datafinal = datetime.strptime(datafinal, "%Y-%m-%d")
    filtered_jobs = []
    for job in jobs:
        published_at = datetime.strptime(job["publishedAt"].split(" ")[0], "%Y-%m-%d")
        if datainicial <= published_at <= datafinal:
            body_text = job.get("body", "").lower()
            if all(s.lower() in body_text for s in skill):
                filtered_jobs.append({
                    "id": job["id"],
                    "titulo": job["title"],
                    "empresa": job["company"]["name"],
                    "descrição": limpar_html(job["body"]),
                    "data de publicação": job["publishedAt"],
                    "salário": job.get("wage", "N/A"),
                    "localização": "; ".join(loc["name"] for loc in job.get("locations", []))
                })
    print(json.dumps(filtered_jobs, indent=2, ensure_ascii=False))
    if export_csv:
        export_to_csv(filtered_jobs, export_csv)

# ========================================================
# Parte 2 – Scraping + Estatísticas
# ========================================================
def itjobs_data(job_id: int) -> dict:
    """Busca um job por ID (API paginada)"""
    page = 1
    while True:
        paginated_url = f"{URL}&page={page}"
        response = requests.get(paginated_url, headers=HEADERS)
        if response.status_code == 200:
            jobs = response.json().get("results", [])
            job = next((j for j in jobs if j.get("id") == job_id), None)
            if job:
                return job
            if not jobs:
                break
            page += 1
        else:
            typer.echo(f"Erro ao conectar à API itjobs.pt. Status: {response.status_code}")
            raise typer.Exit()
    typer.echo(f"Job ID {job_id} não encontrado.")
    raise typer.Exit()

def ambitionbox_data(company_name: str) -> dict:
    """Extrai info da empresa no AmbitionBox"""
    company_name_formatted = company_name.strip().lower().replace(" ", "-")
    url = f"https://www.ambitionbox.com/overview/{company_name_formatted}-overview"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return {"rating": "N/A", "description": "N/A", "benefits": "N/A"}
    soup = BeautifulSoup(response.text, "html.parser")
    rating = soup.select_one("span.css-1jxf684")
    description = soup.select_one("div[data-test='company-description']")
    benefits = soup.select_one("div[data-test='company-benefits']")
    return {
        "rating": rating.text.strip() if rating else "N/A",
        "description": description.text.strip() if description else "N/A",
        "benefits": benefits.text.strip() if benefits else "N/A",
    }

@app.command()
def get_job_info(job_id: int, export_csv: Optional[str] = None):
    job_data = itjobs_data(job_id)
    company_name = job_data.get("company", {}).get("name", "").strip()
    if not company_name:
        typer.echo("Empresa não especificada para o emprego.")
        raise typer.Exit()
    ambitionbox_info = ambitionbox_data(company_name)
    enriched_data = {
        "job_id": job_data.get("id"),
        "company_name": company_name,
        "rating": ambitionbox_info["rating"],
        "ambitionbox_description": ambitionbox_info["description"],
        "ambitionbox_benefits": ambitionbox_info["benefits"]
    }
    typer.echo(json.dumps(enriched_data, indent=2, ensure_ascii=False))
    if export_csv:
        export_to_csv([enriched_data], export_csv)

@app.command()
def statistics():
    """Conta vagas por título + localização"""
    job_counts = {}
    page = 1
    while True:
        response = requests.get(f"{URL}&page={page}", headers=HEADERS)
        if response.status_code != 200:
            break
        jobs = response.json().get("results", [])
        if not jobs:
            break
        for job in jobs:
            title = job["title"]
            locations = ", ".join([loc["name"] for loc in job.get("locations", [])]) if job.get("locations") else "N/A"
            key = (title, locations)
            job_counts[key] = job_counts.get(key, 0) + 1
        page += 1
    aggregated_data = [{"titulo": t, "localização": l, "número de vagas": c} for (t, l), c in job_counts.items()]
    if aggregated_data:
        export_to_csv(aggregated_data, filename="numero_de_vagas.csv")
    else:
        print("Nenhum dado para exportar.")

def skills_from_job(job_url: str):
    response = requests.get(job_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    skills_elements = soup.find_all("a", class_="body-medium chip")
    return [s.get_text(strip=True).lower() for s in skills_elements]

def job_urls(job_title: str):
    job_title = job_title.replace(" ", "-")
    url = f"https://www.ambitionbox.com/jobs/{job_title}-jobs-prf"
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    job_elements = soup.find_all("div", class_="jobsInfoCardCont")
    return [f"https://www.ambitionbox.com{job.find('a')['href']}" for job in job_elements]

@app.command()
def list_skills(job_title: str, export_csv: Optional[str] = None):
    urls = job_urls(job_title)
    all_skills = []
    for url in urls:
        all_skills.extend(skills_from_job(url))
    skill_count = Counter(all_skills)
    top_skills = skill_count.most_common(10)
    skills = [{"skill": s, "count": c} for s, c in top_skills]
    print(json.dumps(skills, indent=2, ensure_ascii=False))
    if export_csv:
        export_to_csv(skills, filename=f"skills_{job_title}.csv")

# ========================================================
# Main
# ========================================================
if __name__ == "__main__":
    app()
