from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
import re
from datetime import datetime

from uk_bin_collection.uk_bin_collection.common import *
from uk_bin_collection.uk_bin_collection.get_bin_data import AbstractGetBinDataClass

# Define the CouncilClass for fetching bin collection data
class CouncilClass(AbstractGetBinDataClass):
    def parse_data(self, page: str, **kwargs) -> dict:
        driver = None
        try:
            page = "https://maps.norwich.gov.uk/mynorwich/index.html"

            data = {"bins": []}

            user_paon = kwargs.get("paon")
            user_postcode = kwargs.get("postcode")
            web_driver = kwargs.get("web_driver")
            headless = kwargs.get("headless")
            check_paon(user_paon)
            check_postcode(user_postcode)

            # Create Selenium webdriver
            driver = create_webdriver(web_driver, headless, None, __name__)
            driver.get(page)

            # Populate postcode field
            inputElement_postcode = driver.find_element(By.ID, "postcode-input")
            inputElement_postcode.send_keys(user_postcode)

            # Click search button
            driver.find_element(By.ID, "search-button").click()

            # Wait for the results to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "nearestLayer")
                )
            )

            soup = BeautifulSoup(driver.page_source, features="html.parser")

            # Find the nearestLayer
            nearest_layer = soup.find("div", class_="nearestLayer")

            if nearest_layer:
                details_body = nearest_layer.find("div", class_="nearestLayer-details-body")
                if details_body:
                    # Extract text
                    details_text = details_body.get_text(separator="\n")

                    # Regex to extract collection day and date
                    match = re.search(r"Your normal collection day:\s*(.+?)\n.*?Your next collection:\s*(\d{2}/\d{2}/\d{4})\n.*?We will be collecting:\s*(.+?)\.", details_text, re.DOTALL)

                    if match:
                        collection_day = match.group(1).strip()
                        collection_date_str = match.group(2).strip()
                        waste_type = match.group(3).strip()

                        # Convert the collection date string to a datetime object
                        collection_date = datetime.strptime(collection_date_str, "%d/%m/%Y")

                        # Add the extracted data to the bins list
                        dict_data = {
                            "type": waste_type,
                            "collectionDate": collection_date.strftime("%Y-%m-%d"),
                        }
                        data["bins"].append(dict_data)

            # Sort the bins data by collection date
            data["bins"].sort(
                key=lambda x: datetime.strptime(x.get("collectionDate"), "%Y-%m-%d")
            )
        except Exception as e:
            print(f"An error occurred: {e}")
            raise
        finally:
            if driver:
                driver.quit()
        return data
