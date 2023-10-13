from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel
from summarizer import generateCompanySummary

app = FastAPI()


class Company(BaseModel):
    company_url: str


@app.post("/generateCompanySummary")
async def generate_summary(requestData: Company):
    markdownSummary = generateCompanySummary(requestData.company_url)
    return {"company_url": markdownSummary}


@app.get("/")
def read_root():
    return {"Hello": "World"}


# @app.get("/scrapeInternalLinks")
# def scrape_internal_links(company_url: str):
#     print(f"[INFO] Getting links for {company_url}")
#     return {'links': scrapeInternalLinks(company_url)}
