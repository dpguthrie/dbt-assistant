# stdlib
import logging
import os
import re
from typing import TYPE_CHECKING, List, Tuple, Union

if TYPE_CHECKING:
    from selenium.webdriver import Chrome, Firefox


# third party
import requests
from bs4 import BeautifulSoup
from langchain_community.document_loaders import SeleniumURLLoader
from langchain_core.documents import Document
from langchain_text_splitters import CharacterTextSplitter
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


def wait_for_loading_to_complete(driver, timeout=10):
    try:
        # Wait for the loading div to disappear
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, "loading"))
        )
        return True
    except TimeoutException:
        logger.error("Loading did not complete within the expected time.")
        return False
    except Exception as e:
        logger.error(f"An error occurred while waiting for loading to complete: {e}")
        return False


class DbtHubSeleniumURLLoader(SeleniumURLLoader):
    def __init__(self, *args, get_github_data: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.get_github_data = get_github_data
        self.github_headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "dbt Hub Assistant",
        }
        if github_token := os.getenv("GITHUB_TOKEN", None):
            self.github_headers["Authorization"] = f"Bearer {github_token}"

    def _build_metadata(self, url: str, driver: Union["Chrome", "Firefox"]) -> dict:
        metadata = dict()
        metadata["title"] = (
            driver.find_element(By.CLASS_NAME, "tile-text")
            .find_element(By.TAG_NAME, "h1")
            .text
        )
        version_element = driver.find_element(By.ID, "version")
        latest_version = [e.strip() for e in version_element.text.split("\n")][
            0
        ].replace(" (latest)", "")
        metadata["version"] = latest_version
        github_url: str = None
        try:
            link_element = driver.find_element(
                By.XPATH, "//a[contains(text(), 'View on GitHub')]"
            )

            # Extract the href attribute
            github_url = link_element.get_attribute("href")

        except Exception as e:
            logger.error(f"An error occurred: {e}")

        if github_url and self.get_github_data:
            data = self._get_github_data(github_url)
            if data:
                metadata["github_url"] = data.get("html_url") or ""
                metadata["github_stars"] = data.get("stargazers_count", 0)
                metadata["description"] = (
                    data.get("description") or "No description found."
                )
                metadata["created_at"] = data.get("created_at") or ""
                metadata["last_updated_at"] = data.get("updated_at") or ""
                metadata["open_issues"] = data.get("open_issues") or 0
                metadata["owner"] = data.get("owner", {}).get("login", "")
                metadata["repo_name"] = data.get("name", "")
                metadata["owner_type"] = data.get("owner", {}).get("type", "")
                metadata["license"] = (data.get("license") or {}).get("name", "")
                metadata["topics"] = ", ".join(data.get("topics", []))
        return metadata

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,
    )
    def _make_github_request(self, url: str) -> requests.Response:
        response = requests.get(url, headers=self.github_headers)
        response.raise_for_status()
        return response.json()

    def _get_github_data(self, github_url: str) -> int:
        def extract_name_and_repo(github_url: str) -> Tuple[str, str]:
            pattern = r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+)"
            match = re.search(pattern, github_url)

            if match:
                org_or_username = match.group(1)
                repo_name = match.group(2)
                return org_or_username, repo_name
            else:
                return None, None

        org_or_username, repo_name = extract_name_and_repo(github_url)
        if not org_or_username or not repo_name:
            logger.warning(
                f"Unable to find org or username and repo name for {github_url}"
            )
            return None

        url = f"https://api.github.com/repos/{org_or_username}/{repo_name}"
        try:
            data = self._make_github_request(url)
        except Exception as e:
            logger.error(f"Error fetching stars for {url}, exception: {e}")
            return None
        else:
            return data

    def load(self) -> List[Document]:
        """Load the specified URLs using Selenium and create Document instances.

        Returns:
            List[Document]: A list of Document instances with loaded content.
        """
        from unstructured.partition.html import partition_html

        docs: List[Document] = list()
        driver = self._get_driver()

        for url in self.urls:
            try:
                driver.get(url)

            except Exception as e:
                if self.continue_on_failure:
                    logger.error(f"Error fetching or processing {url}, exception: {e}")
                else:
                    raise e
            else:
                # Need to wait until the readme is loaded in the page.
                if wait_for_loading_to_complete(driver):
                    logger.info(f"Loading completed for {url}.")
                    page_content = driver.page_source
                    elements = partition_html(text=page_content)
                    text = "\n\n".join([str(el) for el in elements])

                    # Build metadata with github stars, if applicable
                    metadata = self._build_metadata(url, driver)
                    docs.append(Document(page_content=text, metadata=metadata))
                else:
                    logger.error(f"Loading failed for {url}")

        driver.quit()
        return docs


def _get_package_urls() -> List[str]:
    url = "https://hub.getdbt.com"
    response = requests.get(url)
    text = response.text
    soup = BeautifulSoup(text, "html.parser")
    links = soup.select("ul > li > a")

    relative_links = list()

    for link in links:
        href = link.get("href")
        if href and href.startswith("/"):
            full_url = url + href
            relative_links.append(full_url)

    return relative_links


def get_hub_documents(chunk_size: int = 10):
    urls = _get_package_urls()
    loader = DbtHubSeleniumURLLoader(urls)
    documents = loader.load()
    text_splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)
