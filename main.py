from fastapi import FastAPI, HTTPException, Query
import requests
from PyPDF2 import PdfReader
from io import BytesIO
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Utility functions


def fetch_and_read_pdf(pdf_url):
    response = requests.get(pdf_url)
    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code, detail="Failed to fetch PDF"
        )
    file = BytesIO(response.content)
    reader = PdfReader(file)
    return "".join([page.extract_text() for page in reader.pages])


# External API requests functions


def ss_search_paper(query):
    """
    Search for papers using the Semantic Scholar API.

    Args:
    query: The search query string.

    Returns:
    The JSON response from the Semantic Scholar API.

    Raises:
    HTTPException: If the Semantic Scholar API request fails.
    """
    endpoint_url = "https://api.semanticscholar.org/graph/v1/paper/search/"
    ss_api_params = {
        "query": query,
        "fields": "title,authors,year,openAccessPdf",
        "openAccessPdf": "",
    }
    ss_response = requests.get(endpoint_url, params=ss_api_params)

    if ss_response.status_code != 200:
        raise HTTPException(
            status_code=ss_response.status_code, detail="Error in Semantic Scholar API"
        )

    return ss_response.json()["data"]


# Routes


@app.get("/")
def read_root():
    """
    Home endpoint, returns a welcome message.
    """
    return {"message": "Welcome to the PaperSearch server!"}


@app.get("/search")
def search_route(
    query: str = Query(..., description="The query string to search for papers")
):
    """
    Search for papers based on a query and return the first result with its summary.

    Args:
    query: The query string to search for papers.

    Returns:
    The processed data of the first search result.
    """
    ss_search_result = ss_search_paper(query)
    if not ss_search_result:
        raise HTTPException(status_code=404, detail="No papers found")
    paper = ss_search_result[0]
    full_text = fetch_and_read_pdf(paper["openAccessPdf"]["url"])
    paper.update({"full_text": full_text})
    return {"message": "Data processed", "result": paper}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
