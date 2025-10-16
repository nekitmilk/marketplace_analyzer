import requests
import pandas as pd 
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType 

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
import random

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from threading import Lock
import os
from concurrent.futures import ThreadPoolExecutor

from parsers import config_parser

import logging
logging.basicConfig(level=logging.INFO, filename="parser.log", filemode="w",
                format="%(asctime)s %(levelname)s %(message)s")

from dotenv import load_dotenv
load_dotenv()
token = os.getenv('GH_TOKEN')

import undetected_chromedriver as uc 
from selenium.webdriver.common.keys import Keys


class Parser:
    def __init__(self):
        self.driver = None
    
    def _init_driver(self, browser="firefox"):
        if browser == "firefox":
            self.driver = self._init_driver_firefox(config_parser.BROWSER_HEADLESS)
        elif browser == "chrome":
            self.driver = self._init_driver_chrome()
        elif browser == "undetected_chrome":
            self.driver = self._init_driver_undetected_chrome(config_parser.CHROME_HEADLESS)
        else:
            raise ValueError(f"Unsupported browser: {browser}")
        
    def _init_driver_firefox(self, headless = False):
        firefox_options = Options()

        if headless:
            firefox_options.add_argument("--headless")
            firefox_options.set_preference("layout.css.devPixelsPerPx", "1")
            
        firefox_options.set_preference("dom.webdriver.enabled", False)
        firefox_options.set_preference("useAutomationExtension", False)
        firefox_options.set_preference("browser.cache.disk.enable", True)
        firefox_options.set_preference("browser.cache.memory.enable", True)
        firefox_options.set_preference("browser.cache.offline.enable", True)
        firefox_options.set_preference("network.http.use-cache", True)
        firefox_options.set_preference("permissions.default.image", 2)
        
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
        ]
        firefox_options.set_preference("general.useragent.override", random.choice(user_agents))
        firefox_options.set_preference("privacy.resistFingerprinting", True)
        firefox_options.set_preference("privacy.trackingprotection.enabled", True)
        firefox_options.set_preference("dom.event.clipboardevents.enabled", False)
        firefox_options.set_preference("media.volume_scale", "0.0")
        firefox_options.set_preference("gfx.webrender.all", True)
        firefox_options.set_preference("layers.acceleration.force-enabled", True)
        firefox_options.set_preference("intl.accept_languages", "ru")
        firefox_options.set_preference("browser.shell.checkDefaultBrowser", False)
        firefox_options.set_preference("dom.disable_beforeunload", True)
        firefox_options.set_preference("browser.tabs.warnOnClose", False)

        firefox_options.set_preference("dom.disable_open_during_load", True)
        firefox_options.set_preference("alerts.showFadeIn", False)
        firefox_options.set_preference("alerts.slideIncrement", 0)
        firefox_options.set_preference("alerts.slideIncrementTime", 0)
        
        service = Service(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=firefox_options)
        
        driver.set_window_size(random.randint(1200, 1400), random.randint(800, 1000))
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_script("window.chrome = undefined;")

        try:
            driver.get(f"https://www.wildberries.ru")
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.dismiss()
        except:
            logging.info("Диалоговое окно смены языка не найдено")
            pass
        
        return driver
    
    def _init_driver_chrome(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        stealth(driver, 
                platform="macOS",
                languages=["en-US", "en"],
                webgl_vendor="Intel Inc.")
        
        return driver
    
    def _init_driver_undetected_chrome(self, headless = False):
        options = uc.ChromeOptions()
        # Отключаем загрузку изображений и CSS (если они не нужны)
        prefs = {
            "profile.managed_default_content_settings.images": 2,  # Блокировка картинок
            "profile.managed_default_content_settings.javascript": 1,  # JS включен (иначе Ozon не работает)
            "profile.managed_default_content_settings.stylesheets": 2,  # Блокировка CSS (опционально)
            "profile.default_content_setting_values.notifications": 2,  # Блокировка уведомлений
        }
        options.add_experimental_option("prefs", prefs)
        driver = uc.Chrome(
            options=options,
            headless=headless, 
            use_subprocess=True)
        # driver.implicitly_wait(5)
        return driver

    def restart_driver(self):
        if self.driver:
            self.driver.quit()
        self._init_driver()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.safe_close()

    def __del__(self):
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
                self.driver = None
            except Exception as e:
                logging.warning(f"Error closing driver: {e}")
    
    def safe_close(self):
        self.__del__()

    @staticmethod
    def _scroll_page_down(driver):
        # Прокрутка страницы для загрузки ВСЕХ отзывов
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 10 # Максимум попыток прокрутки для защиты от бесконечного цикла

        while scroll_attempts < max_scroll_attempts:
            prev_count = 0
            new_items = len(driver.find_elements(By.CSS_SELECTOR, "li.comments__item"))
            if new_items > prev_count:
                prev_count = new_items
                scroll_attempts = 0  # Сброс при нахождении новых
            else:
                scroll_attempts += 1
                logging.info("Не получилось прокрутить страницу")
            # Прокрутка вниз
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)  # Ожидание подгрузки контента
            
            # Проверка изменения высоты страницы
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    @staticmethod
    def _page_down_slowly(driver):
        # Прокрутка страницы для загрузки ВСЕХ отзывов
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 100 # Максимум попыток прокрутки для защиты от бесконечного цикла

        while scroll_attempts < max_scroll_attempts:
            prev_count = 0
            new_items = len(driver.find_elements(By.CSS_SELECTOR, "div.tile-root"))
            if new_items > prev_count:
                prev_count = new_items
                scroll_attempts = 0  # Сброс при нахождении новых
            else:
                scroll_attempts += 1
                logging.info("Не получилось прокрутить страницу")
            # Прокрутка вниз
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            driver.execute_script('''
                                const scrollStep = 200; // Размер шага прокрутки (в пикселях)
                                const scrollInterval = 100; // Интервал между шагами (в миллисекундах)

                                const scrollHeight = document.documentElement.scrollHeight;
                                let currentPosition = 0;
                                const interval = setInterval(() => {
                                    window.scrollBy(0, scrollStep);
                                    currentPosition += scrollStep;

                                    if (currentPosition >= scrollHeight) {
                                        clearInterval(interval);
                                    }
                                }, scrollInterval);
                            ''')
            time.sleep(2)  # Ожидание подгрузки контента
            
            # Проверка изменения высоты страницы
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

class WB_Parser(Parser):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_wb_products(query="электроды миостимулятор", pages=3) -> pd.DataFrame:
        all_products = []
        
        for page in range(1, pages + 1):
            try:
                url = "https://u-search.wb.ru/exactmatch/ru/common/v18/search"
                
                params = {
                    "ab_testid": "no_promo",
                    "ab_testing": "false",
                    "appType": "1",
                    "curr": "rub",
                    "dest": "-1255987",
                    "inheritFilters": "false",
                    "lang": "ru",
                    "page": str(page),
                    "query": query,
                    "resultset": "catalog",
                    "sort": "popular",
                    "spp": "30",
                    "suppressSpellcheck": "false"
                }
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Referer": f"https://www.wildberries.ru/catalog/0/search.aspx?search={requests.utils.quote(query)}",
                    "Origin": "https://www.wildberries.ru"
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=10)
                response.raise_for_status()

                data = response.json()
                
                products = data.get("products", [])
                
                if not products:
                    logging.info(f"Нет товаров на странице {page}. Прекращаем парсинг.")
                    break

                for product in products:
                    price = 0
                    if product.get("sizes") and len(product["sizes"]) > 0:
                        price_data = product["sizes"][0].get("price", {})
                        price = price_data.get("product", 0) / 100
                    
                    all_products.append({
                        "id": product.get("id"),
                        "marketplace": "wb",
                        "name": product.get("name", ""),
                        "price": price,
                        "rating": product.get("reviewRating", 0),
                        "feedbacks": product.get("feedbacks", 0),
                        "brand": product.get("brand", ""),
                    })
                
                logging.info(f"Страница {page} получена, товаров: {len(products)}")
                
                delay = random.uniform(1, 2)
                time.sleep(delay)
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Ошибка при запросе страницы {page}: {e}")
                continue
            except Exception as e:
                logging.error(f"Неожиданная ошибка на странице {page}: {e}")
                continue
        
        print(f"Всего собрано товаров: {len(all_products)}")
        return pd.DataFrame(all_products).drop_duplicates(subset=['id']).reset_index(drop=True)
     
    def get_product_details(self, product_id, driver=None) -> dict: 
        if driver is None:
            if not self.driver:
                self._init_driver(browser="firefox")
                # self._init_driver(browser="undetected_chrome")
                logging.info(f"Инициализация драйвера {type(self.driver)}")
            driver = self.driver

        details = {
            "id": product_id,
            "description": "",
            "specifications": {},
        }
        
        try:
            url = f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"
            logging.info(f"Загружаем страницу: {url}")
            driver.get(url)
            
            # Ждем загрузки основного контента
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Обработка подтверждения возраста
            try:
            # Ждем появления модального окна подтверждения возраста
                age_modal = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".mo-modal__paper._popupNarrow_1b9nk_25"))
                )
                logging.info(f"{product_id} Найдено модальное окно подтверждения возраста")
                
                # Ищем кнопку "Да, мне есть 18 лет"
                confirm_buttons = [
                    "//button[contains(., 'Да, мне есть 18 лет')]",
                    "//span[contains(text(), 'Да, мне есть 18 лет')]/ancestor::button",
                    "button.mo-button:has(span:contains('Да, мне есть 18 лет'))"
                ]
                
                for button_selector in confirm_buttons:
                    try:
                        if button_selector.startswith("//"):
                            confirm_btn = WebDriverWait(driver, 0.5).until(
                                EC.element_to_be_clickable((By.XPATH, button_selector))
                            )
                        else:
                            confirm_btn = WebDriverWait(driver, 0.5).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector))
                            )
                        
                        driver.execute_script("arguments[0].click();", confirm_btn)
                        logging.info(f"{product_id} Подтверждение возраста выполнено")
                        time.sleep(1)  # Ждем закрытия модального окна
                        break
                    except Exception as e:
                        continue
                else:
                    logging.warning(f"{product_id} Не удалось найти кнопку подтверждения возраста")
                    
            except Exception as e:
                logging.debug(f"{product_id} Модальное окно подтверждения возраста не найдено: {e}")

            # Прокрутка к блоку с характеристиками
            driver.execute_script("window.scrollTo(0, 800)")
            time.sleep(2)

            # ПОИСК И НАЖАТИЕ КНОПКИ "ХАРАКТЕРИСТИКИ И ОПИСАНИЕ"
            detail_button_found = False
            detail_button_selectors = [
                "//button[contains(., 'Характеристики и описание')]",
                "//span[contains(text(), 'Характеристики и описание')]/ancestor::button",
                ".btnDetail--im7UR",
                "button.btnDetail--im7UR",
                "//button[contains(@class, 'btnDetail--im7UR')]",
                "//button[contains(@class, 'mo-button') and contains(., 'Характеристики')]",
                "//div[contains(@class, 'options--JpiVQ')]//button",
                "//button[contains(., 'арактеристики')]",
                "button[data-name-for-wba='Item_Parameters_More']",
                ".clickableButton--I1bNU",
                "//button[contains(., 'Подробнее')]",
                "//h4[contains(text(), 'Характеристики')]/preceding-sibling::button"
            ]
            
            logging.info(f"Поиск кнопки характеристик для товара {product_id}")
            for selector in detail_button_selectors:
                try:
                    if selector.startswith("//"):
                        button = WebDriverWait(driver, 1.5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        button = WebDriverWait(driver, 1.5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    driver.execute_script("arguments[0].click();", button)
                    logging.info(f"{product_id} Кнопка характеристик нажата: {selector}")
                    detail_button_found = True
                    time.sleep(1.5)  # Ждем открытия модального окна
                    break
                except Exception as e:
                    logging.debug(f"{product_id} Селектор {selector} не сработал: {e}")
                    continue

            if not detail_button_found:
                logging.warning(f"{product_id} Не удалось найти кнопку характеристик")
                return details

            # ПАРСИНГ МОДАЛЬНОГО ОКНА С ХАРАКТЕРИСТИКАМИ
            try:
                # Ждем появления модального окна
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".detailsModal--eHzZX, .mo-modal__paper"))
                )
                logging.info(f"{product_id} Модальное окно с характеристиками открыто")

                # ПАРСИНГ ОПИСАНИЯ
                description_selectors = [
                    ".descriptionText--Jq9n2",
                    ".description__text",
                    ".product-page__text",
                    "section p"
                ]
                
                for selector in description_selectors:
                    try:
                        desc_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for desc_elem in desc_elements:
                            text = desc_elem.text.strip()
                            if text and len(text) > 10:  # Минимальная длина описания
                                details["description"] = text
                                logging.debug(f"{product_id} Описание найдено: {selector}")
                                break
                        if details["description"]:
                            break
                    except:
                        continue

                # ПАРСИНГ ХАРАКТЕРИСТИК ИЗ ТАБЛИЦ
                try:
                    # Ищем все таблицы с характеристиками в модальном окне
                    tables = driver.find_elements(By.CSS_SELECTOR, "table.table--tSF0X, table.table--CGApj")
                    logging.info(f"{product_id} Найдено таблиц с характеристиками: {len(tables)}")
                    
                    for table in tables:
                        try:
                            # Получаем название группы характеристик
                            group_name = "Общие характеристики"
                            try:
                                caption = table.find_element(By.CSS_SELECTOR, "caption.caption--gsljv")
                                group_name = caption.text.strip()
                            except:
                                pass
                            
                            if group_name not in details["specifications"]:
                                details["specifications"][group_name] = {}
                            
                            # Парсим строки таблицы
                            rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
                            for row in rows:
                                try:
                                    # Ищем ячейки с характеристиками
                                    th_elem = row.find_element(By.CSS_SELECTOR, "th")
                                    td_elem = row.find_element(By.CSS_SELECTOR, "td")
                                    
                                    name = th_elem.text.strip()
                                    value = td_elem.text.strip()
                                    
                                    if name and value and name not in details["specifications"][group_name]:
                                        details["specifications"][group_name][name] = value
                                        logging.debug(f"{product_id} Характеристика: {name} = {value}")
                                        
                                except Exception as e:
                                    logging.debug(f"{product_id} Ошибка парсинга строки: {e}")
                                    continue
                                    
                        except Exception as e:
                            logging.debug(f"{product_id} Ошибка парсинга таблицы: {e}")
                            continue
                            
                except Exception as e:
                    logging.error(f"{product_id} Ошибка парсинга характеристик: {e}")

                # ЗАКРЫТИЕ МОДАЛЬНОГО ОКНА
                try:
                    close_buttons = [
                        "button._close_1b9nk_55",
                        "button.popup__close",
                        "button.close--sxuWI",
                        "//button[@aria-label='Close']",
                        "//button[contains(@class, 'close')]"
                    ]
                    
                    for close_selector in close_buttons:
                        try:
                            if close_selector.startswith("//"):
                                close_btn = driver.find_element(By.XPATH, close_selector)
                            else:
                                close_btn = driver.find_element(By.CSS_SELECTOR, close_selector)
                            
                            driver.execute_script("arguments[0].click();", close_btn)
                            logging.debug(f"{product_id} Модальное окно закрыто")
                            time.sleep(1)
                            break
                        except:
                            continue
                except:
                    logging.debug(f"{product_id} Не удалось закрыть модальное окно")

            except Exception as e:
                logging.error(f"{product_id} Ошибка при работе с модальным окном: {e}")

            logging.info(f"{product_id} Успешно собрано: описание={bool(details['description'])}, хар-ки={sum(len(g) for g in details['specifications'].values())}")

        except Exception as e:
            logging.error(f"Ошибка при парсинге товара {product_id}: {str(e)}")
        
        return details
    
    def get_product_feedbacks(self, product_id, driver = None) -> pd.DataFrame:
        if driver is None:
            if not self.driver:  # Если драйвер еще не инициализирован
                self._init_driver(browser="firefox")
                logging.info(f"Инициализация драйвера {type(self.driver)}")
            driver = self.driver

        feedbacks = pd.DataFrame(columns=['product_id', 'rating', 'advantage', 'disadvantage', 'comment'])
        try:
            driver.get(f"https://www.wildberries.ru/catalog/{product_id}/feedbacks")

            # Ожидание загрузки основного контейнера с отзывами
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "comments__list, .non-comments"))
            )
            
            try:
                driver.find_element(By.CLASS_NAME, ".non-comments")
                logging.info(f"{product_id} - нет отзывов")
                return pd.DataFrame(columns=['product_id', 'rating', 'advantage', 'disadvantage', 'comment'])
            except:
                pass

            # Проверка и переключение на вкладку "Этот вариант" если доступна
            try:
                # Ожидаем появления переключателя вариантов
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".product-feedbacks__tabs"))
                )
                
                # Ищем кнопку "Этот вариант"
                variant_button = driver.find_element(
                    By.CSS_SELECTOR, "li.product-feedbacks__tab:nth-child(2) > button:nth-child(1)"
                )
                variant_button.click()
                time.sleep(1.5)
            except:
                # Если нет переключателя или кнопки, продолжаем как обычно
                logging.info(f"{product_id} - не удалось найти кнопку \"Этот вариант\"")
                pass

            # Прокрутка страницы для загрузки ВСЕХ отзывов
            last_height = driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scroll_attempts = 10 # Максимум попыток прокрутки для защиты от бесконечного цикла

            while scroll_attempts < max_scroll_attempts:
                prev_count = 0
                new_items = len(driver.find_elements(By.CSS_SELECTOR, "li.comments__item"))
                if new_items > prev_count:
                    prev_count = new_items
                    scroll_attempts = 0  # Сброс при нахождении новых
                else:
                    scroll_attempts += 1
                # Прокрутка вниз
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1.5)  # Ожидание подгрузки контента
                
                # Проверка изменения высоты страницы
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Сбор всех отзывов
            feedback_items = driver.find_elements(By.CSS_SELECTOR, "li.comments__item.feedback")
            feedbacks_list = []

            for item in feedback_items:
                try:
                    rating_elem = item.find_element(By.CLASS_NAME, "feedback__rating")
                    rating_class = rating_elem.get_attribute("class")
                    rating = int(re.search(r'star(\d+)', rating_class).group(1))
                except:
                    rating = None

                text = None
                
                # Парсинг текста отзыва
                try:
                    text_block = item.find_element(By.CSS_SELECTOR, ".feedback__text.j-feedback__text")
                    text = text_block.text
                except:
                    pass

                feedbacks_list.append({
                    'good_id': product_id,
                    'marketplace': 'wb',
                    'rating': rating,
                    'text': text,
                })
            feedbacks = pd.DataFrame(feedbacks_list)
            logging.info(f"{product_id} Отзывы успешно собраны. Количество отзывов: {len(feedbacks)}")
        except Exception as e:
            logging.error(f"Ошибка при парсинге отзывов товара {product_id}: {str(e)}")
            
        return feedbacks

    def __del__(self):
        return super().__del__()
    
    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return super().__exit__(exc_type, exc_val, exc_tb)
    
class Ozon_Parser(Parser):
    def __init__(self):
        super().__init__()
    
    def get_products_links(self, query="миостимулятор", driver=None, max_products=200) -> pd.DataFrame:
        if driver is None:
            if not self.driver:  # Если драйвер еще не инициализирован
                self._init_driver(browser="undetected_chrome")
                logging.info(f"Инициализация драйвера {type(self.driver)}")
            driver = self.driver
        
        try:
            self.driver.get(url='https://ozon.ru')
            time.sleep(2)
    
            find_input = driver.find_element(By.NAME, 'text')
            find_input.clear()
            find_input.send_keys(query)
            time.sleep(2)
            find_input.send_keys(Keys.ENTER)
            time.sleep(2)
    
            logging.info("Начало прокрутки страницы")
            seen_links = set()
            products_data = []
            scroll_attempts = 0
            max_attempts = 10
            while scroll_attempts < max_attempts and len(products_data) < max_products:
                driver.execute_script("""
                    window.scrollBy({
                        top: window.innerHeight * 2,
                        behavior: 'smooth'
                    });
                """)
                time.sleep(0.1 + random.uniform(0.1, 0.2))
                new_items = self._collect_current_cards_(seen_links, products_data)
                    
                if new_items == 0:
                    scroll_attempts += 1
                    time.sleep(1)
                    logging.info(f"Новых товаров нет ({scroll_attempts}/{max_attempts})")
                else:
                    scroll_attempts = 0  # Сброс счетчика
                    logging.info(f"Найдено новых: {new_items} | Всего: {len(products_data)}")
                
                # Выход при достижении лимита
                if len(products_data) >= max_products:
                    break
            logging.info("Конец прокрутки страницы")
            logging.info(f"Завершено. Собрано товаров: {len(products_data)}")
            return pd.DataFrame(products_data)

        except Exception as e:
            logging.error(f"Произошла ошибка при получении товаров с Ozon: {e}")

    def get_products_details(self, product_link, driver=None) -> dict:
        if driver is None:
            if not self.driver:
                self._init_driver(browser="undetected_chrome")
            driver = self.driver
        
        details = {
            "link": product_link,
            "id": "",
            "description": "",
            "brand": "",
            "specifications": {}
        }
        
        try:
            driver.get(product_link)
            time.sleep(3)  # Ожидание загрузки страницы

            # Парсинг артикула (ID)
            try:
                sku_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-widget="webDetailSKU"]'))
                )
                sku_text = sku_button.text
                sku_value = re.search(r'\d+', sku_text)
                if sku_value:
                    details["id"] = int(sku_value.group(0))
            except Exception as e:
                logging.warning(f"Артикул не найден: {str(e)}")

            # Парсинг бренда
            try:
                categories = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ol.tsBodyControl400Small"))
                )
                items = categories.find_elements(By.CSS_SELECTOR, "li")
                if items:
                    last_item = items[-1]
                    brand_link = last_item.find_element(By.CSS_SELECTOR, "a")
                    brand = brand_link.text.strip()
                    details["brand"] = brand
            except Exception as e:
                logging.warning(f"Бренд не найден: {str(e)}")


            self._scroll_to_element('div[data-widget="webDescription"]')
            time.sleep(0.5)
            
            # Парсинг описания
            try:
                description_sections = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-widget="webDescription"]'))
                )
                
                description_texts = []
                for section in description_sections:
                    content = section.find_elements(By.CSS_SELECTOR, '.RA-a1, .RA-a1 *')
                    if content:
                        section_text = "\n".join([e.text for e in content if e.text.strip()])
                        description_texts.append(section_text)
                
                details["description"] = "\n\n".join(description_texts).strip()
            except Exception as e:
                logging.warning(f"Описание не найдено: {str(e)}")
            
            self._scroll_to_element("#section-characteristics")

            # Парсинг характеристик
            try:
                specs_section = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, 'section-characteristics'))
                )
                
                specs_items = specs_section.find_elements(By.CSS_SELECTOR, 'dl.pdp_ha9')
                for item in specs_items:
                    try:
                        key_elem = item.find_element(By.CSS_SELECTOR, '.pdp_ha8')
                        value_elem = item.find_element(By.CSS_SELECTOR, '.pdp_h8a')
                        
                        key = key_elem.text.strip().rstrip(':')
                        value = value_elem.text.strip()
                        
                        if key and value:
                            details["specifications"][key] = value
                    except:
                        continue
            except Exception as e:
                logging.warning(f"Характеристики не найдены: {str(e)}")
            
            return details
        
        except Exception as e:
            logging.error(f"Ошибка при получении деталей товара: {str(e)}")
            return details
    
    def get_product_feedbacks(self, product_id, driver=None, max_product_feedbacks=10_000) -> pd.DataFrame:

        this_variant_xpath = "//button[contains(., 'Этот вариант товара')]"
        reviews_selector = "div[data-widget='webReviewTabs']"
        recomendation_selector = 'jl9_24'

        if driver is None:
            if not self.driver:  # Если драйвер еще не инициализирован
                self._init_driver(browser="undetected_chrome")
                logging.info(f"Инициализация драйвера {type(self.driver)}")
            driver = self.driver
        
        try:
            driver.get(url=f"https://www.ozon.ru/product/{product_id}/")
            time.sleep(2)
            self._scroll_to_element(css_selector=reviews_selector)
            try:
                variant_button = WebDriverWait(driver, 1).until(
                    EC.element_to_be_clickable((By.XPATH, this_variant_xpath))
                )
                driver.execute_script("arguments[0].click();", variant_button)
            except:
                logging.info('Не удалось найти кнопку "Этот вариант товара"')

            time.sleep(1)
            seen_feedbacks = set()
            product_feedbacks = []
            scroll_attempts = 0
            max_attempts = 3

            while scroll_attempts < max_attempts and len(product_feedbacks) < max_product_feedbacks:
                driver.execute_script("""
                    window.scrollTo({
                        top: document.body.scrollHeight - 4500,
                        behavior: 'smooth'
                    });
                """)
                time.sleep(0.1 + random.uniform(0.1, 0.2))
                new_items = self._collect_current_feedbacks_(seen_feedbacks, product_feedbacks, product_id)
                    
                if new_items == 0:
                    scroll_attempts += 1
                    # self._scroll_to_element(web_element=driver.find_elements(
                    #     By.CSS_SELECTOR, (f'div.{recomendation_selector}'))[-1]
                    # )
                    self._scroll_to_element(web_element=driver.find_elements(
                        By.XPATH, "//span[text()='Рекомендуем также']")[-1]
                    )

                    time.sleep(2)
                    logging.info(f"Новых товаров нет ({scroll_attempts}/{max_attempts})")
                else:
                    scroll_attempts = 0  # Сброс счетчика
                    logging.info(f"Найдено новых: {new_items} | Всего: {len(product_feedbacks)}")
                
                # Выход при достижении лимита
                if len(product_feedbacks) >= max_product_feedbacks:
                    break
            logging.info("Конец прокрутки страницы")
            logging.info(f"Завершено. Собрано отзывов: {len(product_feedbacks)}")
            return pd.DataFrame(product_feedbacks)



        except Exception as e:
            logging.info(f"Не удалось получить отзывы на товар, ошибка: {e}")

    def _collect_current_cards_(self, seen_links: set, data_collector: list):
        driver = self.driver
        current_cards = driver.find_elements(By.CSS_SELECTOR, "div.tile-root")
        new_items = 0

        for card in current_cards:
            try:
                link_elem = card.find_element(By.CSS_SELECTOR, "a.tile-clickable-element[href*='/product/']")
                link = link_elem.get_attribute("href")
                
                if link not in seen_links:
                    seen_links.add(link)
                    title = card.find_element(By.CSS_SELECTOR, "span.tsBody500Medium").text

                    # Цена (актуальная)
                    try:
                        price_elem = card.find_element(By.CSS_SELECTOR, "span.tsHeadline500Medium")
                        price = price_elem.text
                    except:
                        # Если нет скидки, ищем обычную цену
                        price_elem = card.find_element(By.CSS_SELECTOR, "span[class*='tsHeadline']")
                        price = price_elem.text
                    
                    try:
                        bottom_elem = WebDriverWait(card, 0.5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div.tsBodyMBold"))
                        )
                        rating = bottom_elem.text[:3]
                        reviews = re.sub(r'[^\d]', '', bottom_elem.text[3:])
                    except:
                        logging.info(f"Отзывы и рейтинг не найдены для товара: {title}")
                        rating = 0
                        reviews = 0

                    data_collector.append({
                        "link": link,
                        "marketplace": "ozon",
                        "name": title,
                        "price": price,
                        "rating": rating,
                        "feedbacks": reviews
                    })
                    new_items += 1
            except Exception as e:
                logging.debug(f"Пропуск карточки: {str(e)}")
                continue
    
        return new_items

    def _collect_current_feedbacks_(self, seen_feedbacks: set, data_collector: list, product_id: str):
        driver = self.driver
        # current_feedbacks = driver.find_elements(By.CSS_SELECTOR, "div.v5r_30")
        current_feedbacks = driver.find_elements(By.XPATH, '//*[@data-review-uuid]')

        rating_selector = 'ml4_28' #
        read_full_selector = 'l6m_28'
        # advantage_selector = 'q5r_30'
        paragraph_selector = 'lm6_28' #
        text_selector = 'ml5_28' #
        new_items = 0

        for feedback in current_feedbacks:
            try:
                feedback_id = feedback.get_attribute('data-review-uuid')
                # feedback_id = feedback_id_elem.get_attribute('data-review-uuid')
                # print(feedback_id_elem.text)
                if feedback_id in seen_feedbacks:
                    continue

                seen_feedbacks.add(feedback_id)

                # Извлекаем оценку (количество звезд)
                try:
                    stars_container = feedback.find_element(By.CSS_SELECTOR, f'div.{rating_selector}')
                    filled_stars = stars_container.find_elements(
                        By.CSS_SELECTOR, 'svg[style*="graphicRating"]'
                    )
                    rating = len(filled_stars)
                except:
                    rating = 0
                    logging.debug("Оценка не найдена")

                # Извлекаем текст отзыва
                try:
                    read_full_button = feedback.find_element(By.CSS_SELECTOR, f'span.{read_full_selector}')
                    driver.execute_script("arguments[0].click();", read_full_button)
                except:
                    logging.debug('Кнопка "Читать полностью" не найдена"')

                text = ""
                try:
                    texts_elem = feedback.find_elements(By.CSS_SELECTOR, f'div.{paragraph_selector}')
                    logging.debug(f'Кол-во параграфов: {len(texts_elem)}')
                    if len(texts_elem) > 1:
                        # for text in texts_elem:
                        #     text_field_name = text.find_element(By.CSS_SELECTOR, f'div.{advantage_selector}').text.strip().lower()
                        #     if text_field_name == 'достоинства':
                        #         advantage = text.find_element(By.CSS_SELECTOR, f'span.{text_selector}').text.strip()
                        #     elif text_field_name == 'недостатки':
                        #         disadvantage = text.find_element(By.CSS_SELECTOR, f'span.{text_selector}').text.strip()
                        #     else:
                        #         comment = text.find_element(By.CSS_SELECTOR, f'span.{text_selector}').text.strip()

                        for text_elem in texts_elem:
                            text += text_elem.find_element(By.CSS_SELECTOR, f'span.{text_selector}').text.strip() + ' '
                    else:
                        text = feedback.find_element(By.CSS_SELECTOR, f'span.{text_selector}').text.strip()
                except:
                    text = ""
                    logging.debug("Текст отзыва не найден")

                data_collector.append({
                    'good_id': int(product_id),
                    'marketplace': 'ozon',
                    'rating': rating,
                    'text': text,
                })
                new_items += 1
            except Exception as e:
                logging.info(f"Пропуск отзыва: {str(e)}")
                continue

        return new_items

    def _scroll_to_element(self, css_selector=None, xpath=None, web_element=None):
        """
        Прокрутка к элементу
        
        :param css_selector: CSS селектор элемента
        :param xpath: XPath элемента
        :param web_element: Веб-элемент
        :param scroll_duration: Длительность прокрутки в секундах
        """
        driver = self.driver
        if css_selector:
            element = driver.find_element(By.CSS_SELECTOR, css_selector)
        elif xpath:
            element = driver.find_element(By.XPATH, xpath)
        elif web_element:
            element = web_element
        
        driver.execute_script("""
            arguments[0].scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'center'
            });
        """, element)
        
        


    def __del__(self):
        return super().__del__()
    
    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return super().__exit__(exc_type, exc_val, exc_tb)


class ShopEmsParser(Parser):
    def __init__(self):
        super().__init__()

    def __del__(self):
        return super().__del__()
    
    def __enter__(self):
        return super().__enter__()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return super().__exit__(exc_type, exc_val, exc_tb)
    
    def collect_product_links(self, url):
        """Получить все ссылки на товары со страницы"""
        if not self.driver:
            self._init_driver()
        
        self.driver.get(url)
        time.sleep(3)  # Даем странице загрузиться
        
        # Прокручиваем страницу для загрузки всех товаров
        self._scroll_page_down(self.driver)
        
        # Находим все карточки товаров
        product_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.js-product.t-store__card")
        
        links = []
        for card in product_cards:
            try:
                # Получаем ссылку из атрибута data-product-url
                product_url = card.get_attribute("data-product-url")
                if product_url:
                    links.append(product_url)
                else:
                    # Альтернативно: получаем ссылку из тега <a>
                    link_element = card.find_element(By.CSS_SELECTOR, "a")
                    href = link_element.get_attribute("href")
                    if href:
                        links.append(href)
            except Exception as e:
                logging.warning(f"Не удалось извлечь ссылку для товара: {e}")
        
        return links

    def parse_single_product(self, url, driver=None):
        if driver is None:
            if not self.driver:
                self._init_driver(browser="firefox")
                logging.info(f"Инициализация драйвера {type(self.driver)}")
            driver = self.driver
        """Парсинг одной страницы товара"""
        try:
            logging.info(f"Парсинг товара: {url}")
            
            self.driver.get(url)
            time.sleep(2)
            
            # Ждем загрузки основных элементов
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Собираем основную информацию
            product_info = self._parse_product_info(url)
            if not product_info:
                return None, []
            
            characteristics_tabs = self.driver.find_elements(
            By.XPATH, 
            "//button[contains(text(), 'Характеристики')] | //li[contains(text(), 'Характеристики')]"
            )
            
            for tab in characteristics_tabs:
                try:
                    # Кликаем на вкладку характеристик
                    self.driver.execute_script("arguments[0].click();", tab)
                    time.sleep(1)  # Ждем загрузки характеристик
                    break
                except:
                    continue
            
            # Также пробуем через селектор для мобильной версии
            try:
                select_element = self.driver.find_element(By.CSS_SELECTOR, "select.t395__select")
                from selenium.webdriver.support.ui import Select
                select = Select(select_element)
                # Выбираем опцию с характеристиками
                for option in select.options:
                    if "Характеристики" in option.text:
                        select.select_by_visible_text(option.text)
                        time.sleep(1)
                        break
            except:
                pass

            # Собираем характеристики
            product_specs = self._parse_specifications(url)
            
            return product_info, product_specs
            
        except Exception as e:
            logging.error(f"Ошибка при парсинге {url}: {e}")
            return None, []

    def _parse_product_info(self, url):
        """Парсинг основной информации о товаре"""
        try:
            # Название товара
            name = self._get_element_text(
                By.CSS_SELECTOR, 
                "h1.t795__title, h1.t-title, div.t-container h1, h1.t-name"
            )
            
            if not name:
                logging.warning(f"Не найдено название для товара: {url}")
                return None
            
            # Цена в рублях (из формы)
            price = self._extract_price_from_form()
            
            # Бренд (извлекаем из названия или находим отдельно)
            brand = self._extract_brand(name)
            
            # Описание
            description = self._get_element_text(
                By.CSS_SELECTOR, 
                "div[field='text']"
            )
            
            # Если описание не найдено, пробуем альтернативные селекторы
            if not description:
                description = self._get_element_text(
                    By.CSS_SELECTOR,
                    "div.t-text.t-text_md, .t-rich-text, .t-typography"
                )
            
            return {
                'url': url,
                'name': name,
                'price': price,
                'rating': None,  # пустое
                'feedbacks': None,  # пустое
                'brand': brand,
                'description': description
            }
            
        except Exception as e:
            logging.error(f"Ошибка при парсинге основной информации для {url}: {e}")
            return None

    def _extract_price_from_form(self):
        """Извлечение цены в рублях из формы"""
        try:
            # Сначала пытаемся найти и выбрать опцию "Новый" в форме
            form_selectors = [
                "select[name='type']",
                "select.js-tilda-rule",
                "div.t396__elem select"
            ]
            
            for selector in form_selectors:
                try:
                    select_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Используем Select для работы с выпадающим списком
                    from selenium.webdriver.support.ui import Select
                    select = Select(select_element)
                    
                    # Ищем опцию "Новый"
                    for option in select.options:
                        if "Новый" in option.text:
                            select.select_by_visible_text(option.text)
                            time.sleep(1)  # Ждем обновления цены
                            break
                    
                    break  # Выходим из цикла если нашли селектор
                except:
                    continue
            
            # Теперь ищем цену в рублях
            rub_price_selectors = [
                "//*[contains(text(), 'Стоимость ₽')]/following-sibling::span[contains(@class, 't-calc')]",
                "//*[contains(text(), 'Стоимость ₽')]//following-sibling::span",
                "//span[contains(@class, 't-calc') and preceding-sibling::span[contains(text(), 'Стоимость ₽')]]"
            ]
            
            for xpath in rub_price_selectors:
                try:
                    price_elements = self.driver.find_elements(By.XPATH, xpath)
                    for price_element in price_elements:
                        price_text = price_element.text.strip()
                        if price_text:
                            # Очищаем текст от пробелов и символов
                            price = ''.join(filter(str.isdigit, price_text))
                            if price:
                                return int(price)
                except:
                    continue
            
            # Альтернативный способ: через data-атрибуты опций
            try:
                option_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "option[data-calc-value]"
                )
                for option in option_elements:
                    if "Новый" in option.text:
                        price_eur = option.get_attribute("data-calc-value")
                        if price_eur:
                            # Конвертируем евро в рубли (как в форме на сайте - умножаем на 100)
                            return int(price_eur) * 100
            except:
                pass
                    
        except Exception as e:
            logging.warning(f"Не удалось извлечь цену из формы: {e}")
        
        return None

    def _extract_brand(self, product_name):
        """Извлечение бренда из названия товара"""
        try:
            if product_name:
                # Убираем лишние пробелы и берем первое слово
                return product_name.strip().split()[0]
        except:
            pass
        return "Unknown"

    def _parse_specifications(self, url):
        """Парсинг таблицы характеристик"""
        specs = []
        
        try:
            # Ищем таблицу характеристик
            table_selectors = [
                "table.t431__table",
                "div.t431 table",
                ".t-rec_pt_45 table",
                "table.t-record"
            ]
            
            for selector in table_selectors:
                try:
                    tables = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for table in tables:
                        rows = table.find_elements(By.CSS_SELECTOR, "tr")
                        
                        for row in rows:
                            cells = row.find_elements(By.CSS_SELECTOR, "td")
                            if len(cells) >= 2:
                                name = cells[0].text.strip()
                                value = cells[1].text.strip()
                                
                                if name and value:
                                    specs.append({
                                        'url': url,
                                        'name': name,
                                        'value': value
                                    })
                    
                    if specs:  # Если нашли характеристики, выходим
                        break
                        
                except:
                    continue
            
            # Если таблицу не нашли, пробуем извлечь из data-part2
            if not specs:
                data_parts = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "div.t431__data-part2"
                )
                for data_part in data_parts:
                    text = data_part.text
                    if text:
                        lines = text.split('\n')
                        for line in lines:
                            if ';' in line:
                                name, value = line.split(';', 1)
                                specs.append({
                                    'url': url,
                                    'name': name.strip(),
                                    'value': value.strip()
                                })
        
        except Exception as e:
            logging.warning(f"Не удалось извлечь характеристики для {url}: {e}")
        
        return specs

    def _get_element_text(self, by, selector):
        """Безопасное получение текста элемента"""
        try:
            element = self.driver.find_element(by, selector)
            return element.text.strip()
        except:
            return ""

    def create_dataframes(self, goods_data, specs_data):
        """Создание DataFrame из собранных данных"""
        if not goods_data:
            goods_df = pd.DataFrame(columns=['url', 'name', 'price', 'rating', 'feedbacks', 'brand', 'description'])
        else:
            goods_df = pd.DataFrame(goods_data)
        
        if not specs_data:
            specs_df = pd.DataFrame(columns=['url', 'name', 'value'])
        else:
            specs_df = pd.DataFrame(specs_data)
        
        # Приводим к правильным типам данных
        if not goods_df.empty:
            goods_df = goods_df.astype({
                'url': 'str',
                'name': 'str', 
                'price': 'Int64',  # Разрешаем NaN
                'rating': 'object',
                'feedbacks': 'object',
                'brand': 'str',
                'description': 'str'
            })
        
        if not specs_df.empty:
            specs_df = specs_df.astype({
                'url': 'str',
                'name': 'str',
                'value': 'str'
            })
        
        return goods_df, specs_df


def normalize_text(text):
    """Нормализует текст для поиска"""
    if not isinstance(text, str):
        return ""
    return re.sub(r'[^\w\s]', '', text.lower().strip())

def parse_product_data_wb(product_data):
    """
    Преобразует сырые данные товара в два DataFrame:
    1. Описание (main_info)
    2. Характеристики (specifications)
    
    Args:
        product_data: Сырые данные товара
    """
    product_id = product_data['id']
    description = product_data['description']
    details = {
        "id" : product_id,
        "description": description,
    }

    specs_list = []
    for group_name, group_items in product_data['specifications'].items():
        for name, value in group_items.items():
            specs_list.append({
                'good_id': product_id,
                'group_name': group_name,
                'name': name,
                'value': value
            })
    
    main_info_data = {key: [value] for key, value in details.items()}
    main_info = pd.DataFrame(main_info_data)
    specifications = pd.DataFrame(specs_list)
    
    return main_info, specifications

def parse_product_data_ozon(product_data):
    """
    Преобразует сырые данные товара в два DataFrame:
    1. Основная информация (main_info)
    2. Характеристики (specifications)
    """
    product_id = product_data['id']
    description = product_data['description']
    brand = product_data['brand']
    link = product_data['link']
    details = {
        "id" : product_id,
        'link': link,
        "description": description,
        "brand": brand,
    }

    specs_list = []
    for name, value in product_data['specifications'].items():
        specs_list.append({
            'good_id': product_id,
            'name': name,
            'value': value
        })

    main_info_data = {key: [value] for key, value in details.items()}
    main_info = pd.DataFrame(main_info_data)
    specifications = pd.DataFrame(specs_list)
    
    return main_info, specifications

def write_lock_df_to_file(path, df, write_lock):
    with write_lock:
        try:
            if not os.path.exists(path):
                df.to_csv(path, index=False)
            else:
                df.to_csv(path, mode='a', header=False, index=False) 
            logging.debug(f"Успешная запись в файл!")
        except Exception as e:
            logging.error(f"Ошибка записи в файл: {e}")