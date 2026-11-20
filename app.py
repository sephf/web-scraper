from playwright.sync_api import sync_playwright
import time
import csv, json
import os
import pandas as pd
from datetime import date
import glob
os.makedirs("history", exist_ok=True)
def scrape_jobs():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        all_jobs = []
        currently = 1
        while True:
            url = f"https://empleo.cr/job-list/page/{currently}/?filter-date-posted=30days&filter-salary-from=0&filter-salary-to=1000000"
            page.goto(url)
            if page.query_selector(".item-job") is None:
                break
            print(f"✨ Scraping page.. {currently}")
            page.wait_for_selector(".item-job")
            jobs = page.evaluate("""
                () => {
                    const jobs = document.querySelectorAll('.item-job');
                    return Array.from(jobs).map(job=> ({
                        titulo: job.querySelector('.job-title')?.textContent.trim(),
                        categoria: job.querySelector('.category-job')?.textContent.trim(),
                        link: job.querySelector('.job-title a')?.href
                    }))
                }
            """)
            all_jobs.extend(jobs)
            currently += 1
            time.sleep(0.3)

        browser.close()
        return all_jobs

datos = scrape_jobs()

today = date.today()
def save_csv(datos):
    filename = f"history/jobs{today}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames = ['titulo', 'categoria', 'link'])
        writer.writeheader()
        writer.writerows(datos)

def save_json(datos):
    filename = f"history/jobs{today}.json"
    with open(filename, 'w',encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent = 2)
 
save_csv(datos)


files = sorted(glob.glob("history/jobs*.csv"))

if len(files) >= 2:
        print("No hay histórico suficiente para comparar.")
else:
    csv_actual = pd.read_csv(files[-1])
    csv_anterior = pd.read_csv(files[-2])

    nuevos = csv_actual.merge(
        csv_anterior.drop_duplicates(),
        how="left",
        indicator=True
    ).query('_merge == "left_only"').drop(columns="_merge")

    nuevos.to_csv("new_jobs.csv", index=False)

files_to_clean = sorted(
    glob.glob("history/jobs*.csv"),
    key=os.path.getmtime
)

while len(files_to_clean) > 3:
    archivo_viejo = files_to_clean.pop(0)
    os.remove(archivo_viejo)