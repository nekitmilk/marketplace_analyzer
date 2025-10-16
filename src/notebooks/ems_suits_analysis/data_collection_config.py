url_source_1 = 'https://shopems.ru/ems-oborudovanie'

RAW_DIRECTORY = '../data/raw_data_ems_suits/' # Директория для сырых данных 
CLEAR_DIRECTORY = '../data/clear_ems_suits/' # Директория для создания очищенного набора данных
CLEAR_GOODS_FILE = 'Goods.csv'
CLEAR_OTHER_CHARACTERISTICKS_FILE = 'Other_specifications.csv'
CLEAR_FEEDBACKS_FILE = 'Feedbacks.csv'

EMSSHOP_URLS_FILE = 'emsshop_urls.csv'
EMSSHOP_GOODS = 'emsshop_goods.csv' # Файл для записи всех товаров с главной страницы
EMSSHOP_OTHER_DETAILS_FILE = 'emsshop_other_specifications.csv'

NOBLERISE_GOODS = 'noblerise_goods.csv'
NOBLERISE_OTHER_DETAILS_FILE = 'noblerise_other_specifications.csv'

import os 
os.makedirs(RAW_DIRECTORY, exist_ok=True)
os.makedirs(CLEAR_DIRECTORY, exist_ok=True)