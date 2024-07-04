from bs4 import BeautifulSoup as soup
import json
from requests import get
from pydotmap import DotMap


class PinterestImageScraper:

    def __init__(self):
        self.json_data_list = []
        self.unique_img = []


    @staticmethod
    def get_pinterest_links(body, max_images: int):
        searched_urls = []
        html = soup(body, 'html.parser')
        links = html.select('#b_results cite')
        for link in links:
            link = link.text
            if "pinterest" in link:
                searched_urls.append(link)
                # stops adding links if the limit has been reached
                if max_images is not None and max_images == len(searched_urls):
                    break
        return searched_urls

    # -------------------------- save json data from source code of given pinterest url -------------
    def get_source(self, url: str, proxies: dict) -> None:
        try:
            res = get(url, proxies=proxies)
        except Exception:
            return
        html = soup(res.text, 'html.parser')
        json_data = html.find_all("script", attrs={"id": "__PWS_INITIAL_PROPS__"})
        if not len(json_data):
            json_data = html.find_all("script", attrs={"id": "__PWS_DATA__"})
        self.json_data_list.append(json.loads(json_data[0].string)) if len(json_data) else self.json_data_list.append({})

    # --------------------------- READ JSON OF PINTEREST WEBSITE ----------------------
    def save_image_url(self, max_images: int) -> list:
        url_list = []
        for js in self.json_data_list:
            try:
                data = DotMap(js)
                urls = []
                if not data.initialReduxState and not data.props:
                    return []
                pins = data.initialReduxState.pins if data.initialReduxState else data.props.initialReduxState.pins
                for pin in pins:
                    if isinstance(pins[pin].images.get("orig"), list):
                        for i in pins[pin].images.get("orig"):
                            urls.append(i.get("url"))
                    else:
                        urls.append(pins[pin].images.get("orig").get("url"))

                for url in urls:
                    url_list.append(url)
                    if max_images is not None and max_images == len(url_list):
                        return list(set(url_list))
            except Exception:
                continue

        return list(set(url_list))

    # -------------------------- get user keyword and google search for that keywords ---------------------
    @staticmethod
    def start_scraping(max_images, key=None, proxies={}):
        assert key is not None, "Please provide keyword for searching images"
        keyword = key + " pinterest"
        keyword = keyword.replace("+", "%20")
        url = f'https://www.bing.com/search?q={keyword}&first=1&FORM=PERE'
        res = get(url, proxies=proxies, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"})
        searched_urls = PinterestImageScraper.get_pinterest_links(res.content, max_images)

        return searched_urls, key.replace(" ", "_")

    def make_ready(self, key=None):
        extracted_urls, keyword = PinterestImageScraper.start_scraping(max_images=None, key=key)

        self.json_data_list = []
        self.unique_img = []

        print('saving json data ...')
        for i in extracted_urls:
            self.get_source(i, {})


        url_list = self.save_image_url(max_images=None)
        print(f"Total {len(url_list)} image URLs found.")
        print()

        if len(url_list) > 0:
            filename = f"{key}_pinterest_images.csv"
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                file.write("Image URLs\n")
                for url in url_list:
                    file.write(f"{url}\n")
            print(f"Image URLs saved to '{filename}'.")
            return True
        else:
            return False


if __name__ == "__main__":
    user_input = input("Enter keyword: ")
    p_scraper = PinterestImageScraper()
    is_downloaded = p_scraper.make_ready(user_input)
