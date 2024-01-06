from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from uk_bin_collection.uk_bin_collection.common import *
from uk_bin_collection.uk_bin_collection.get_bin_data import AbstractGetBinDataClass


# import the wonderful Beautiful Soup and the URL grabber
class CouncilClass(AbstractGetBinDataClass):
    """
    Concrete classes have to implement all abstract operations of the
    base class. They can also override some operations with a default
    implementation.
    """

    def parse_data(self, page: str, **kwargs) -> dict:
        data = {"bins": []}
        user_paon = kwargs.get("paon")
        user_postcode = kwargs.get("postcode")
        web_driver = kwargs.get("web_driver")
        headless= kwargs.get("headless")
        check_paon(user_paon)
        check_postcode(user_postcode)

        # Create Selenium webdriver
        driver = create_webdriver(web_driver,headless)
        driver.get(
            "https://www.e-lindsey.gov.uk/article/6714/Your-Waste-Collection-Days"
        )

        # Wait for the postcode field to appear then populate it
        inputElement_postcode = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.ID, "WASTECOLLECTIONDAYS202324_LOOKUP_ADDRESSLOOKUPPOSTCODE")
            )
        )
        inputElement_postcode.send_keys(user_postcode)

        # Click search button
        findAddress = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, "WASTECOLLECTIONDAYS202324_LOOKUP_ADDRESSLOOKUPSEARCH")
            )
        )
        findAddress.click()

        # Wait for the 'Select address' dropdown to appear and select option matching the house name/number
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//select[@id='WASTECOLLECTIONDAYS202324_LOOKUP_ADDRESSLOOKUPADDRESS']//option[contains(., '"
                    + user_paon
                    + "')]",
                )
            )
        ).click()

        # Wait for the submit button to appear, then click it to get the collection dates
        submit = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, "WASTECOLLECTIONDAYS202324_LOOKUP_FIELD2_NEXT")
            )
        )
        submit.click()

        # Wait for the collections table to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".waste-results"))
        )

        soup = BeautifulSoup(driver.page_source, features="html.parser")

        # Quit Selenium webdriver to release session
        driver.quit()

        # Get collections
        for collection in soup.find_all("div", {"class": "waste-result"}):
            ptags = collection.find_all("p")
            dict_data = {
                "type": collection.find("h3").get_text(strip=True),
                "collectionDate": datetime.strptime(
                    remove_ordinal_indicator_from_date_string(
                        ptags[1]
                        .get_text()
                        .replace("The date of your next collection is", "")
                        .replace(".", "")
                        .strip()
                    ),
                    "%A %d %B %Y",
                ).strftime(date_format),
            }
            data["bins"].append(dict_data)

        data["bins"].sort(
            key=lambda x: datetime.strptime(x.get("collectionDate"), "%d/%m/%Y")
        )

        return data
