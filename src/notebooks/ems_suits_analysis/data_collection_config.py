QUERY = ""

RAW_DIRECTORY = '../data/raw_data_electrods/' # Директория для сырых данных 
CLEAR_DIRECTORY = '../data/clear_data_electrodes/' # Директория для создания очищенного набора данных
GOODS_FILE = 'Goods.csv'
OTHER_CHARACTERISTICKS_FILE = 'Other_specifications.csv'
FEEDBACKS_FILE = 'Feedbacks.csv'

# Настройка сбора товаров с Wildberries
WB_PRODUCTS_FILE = 'wb_products.csv' # Файл для записи всех товаров с главной страницы
WB_CLEARED_PRODUCTS_FILE = 'wb_cleared_products.csv' # Содержит в себе товары после очистки, для них происходит остальной парсинг
WB_DESCRIPTION_FILE = 'wb_descriptions.csv' # Файл, содержащий записи об описании товаров
WB_OTHER_DETAILS_FILE = 'wb_other_specifications.csv' # Файл содержащий все характеристики товаров
WB_GOODS_FILE = 'wb_goods.csv' # В этом файле объединяются WB_CLEARED_PRODUCTS_FILE и WB_MAIN_DETAILS_FILE
WB_FEEDBACKS_FILE = 'wb_feedbacks.csv' # Содержит отзывы на товары

WB_PAGES = 10_000 # Как много товаров собрать с главной страницы?


# Настройка сбора товаров с Ozon
OZON_PRODUCTS_FILE = 'ozon_products.csv'
OZON_CLEARED_PRODUCTS_FILE = 'ozon_cleared_products.csv'
OZON_DESCRIPTION_FILE = 'ozon_descriptions.csv'
OZON_OTHER_DETAILS_FILE = 'ozon_other_specificatio.csv'
OZON_GOODS_FILE = 'ozon_goods.csv'
OZON_FEEDBACKS_FILE = 'ozon_feedbacks.csv'

OZON_PAGES = 10_000


# Настройка очистки товаров с главной страницы
WB_INCLUDE_PATTERNS = [
    r'электрод',
] # Какие товары включать?
WB_EXCLUDE_PATTERNS = [
    r'шнур\s+переходник',
] # Какие товары исключить?

WB_PERCENT_FEEDBACKS = 100 # Какой топ товаров по отзывам брать? (%)
WB_MIN_FEEDBACKS = 0 # Минимальное количество отзывов на товаре
WB_MIN_RATING = 0 # Минимальный рейтинг товара

WB_PRICE_SEGMENT_SAMPLE = 20 # Делит выборку товаров на квартили по цене. На сколько обогащать очищенную выборку каждым сегментом?
WB_UNDERVALUED_SAMPLE = 20 # На сколько обогатить выборку недооцененными товарами (рейтинг > 4.8; цена < медианной; кол-во отзывов < медианного)

WB_INCLUDE_TOP_BY_FEEDBACKS = True
WB_INCLUDE_PRICE_SEGMENTS = False
WB_INCLUDE_UNDERVALUED = False

OZON_INCLUDE_PATTERNS = [
    r"электрод",
    r"липучк", 
    r"накладк",
    r"пластин",
    r"самокле" 
]
OZON_EXCLUDE_PATTERNS = [
    # Аксессуары и комплектующие
    r"шнур", r"кабель", r"провод", r"переходник", r"зажим",
    r"держатель", r"крепление", r"адаптер", r"разъем",
    
    # Специфичные устройства (не электроды)
    r"миостимулятор", r"массажер", r"тренажер", r"аппарат",
    r"прибор", r"устройство", r"платформа", r"пояс",
    r"тапочки", r"перчатки", r"носок", r"наколенник",
    r"пластырь", r"маска", r"зонд",
]

OZON_PERCENT_FEEDBACKS = 100
OZON_MIN_FEEDBACKS = 1 
OZON_MIN_RATING = 0 

OZON_PRICE_SEGMENT_SAMPLE = 20
OZON_UNDERVALUED_SAMPLE = 20

OZON_INCLUDE_TOP_BY_FEEDBACKS = True
OZON_INCLUDE_PRICE_SEGMENTS = True
OZON_INCLUDE_UNDERVALUED = True



import os 
os.makedirs(RAW_DIRECTORY, exist_ok=True)
os.makedirs(CLEAR_DIRECTORY, exist_ok=True)

# TYPES_MAIN_DETAILS = {
#     # Размеры электродов
#     'electrode_size': [
#         'размер электрод', 'размер', 'size', 'электрод размер',
#         'габарит', 'площадь', 'размеры'
#     ],
    
#     # Количество в упаковке
#     'quantity': [
#         'количество', 'комплектация', 'количество предметов', 
#         'шт.', 'штук', 'количество в упаковке', 'предметов в упаковке',
#         'пачк', 'упаковк'
#     ],
    
#     # Назначение/применение
#     'purpose': [
#         'назначение', 'применение', 'purpose', 'использование',
#         'для чего', 'функция', 'назначение электрод'
#     ],
    
#     # Страна производства
#     'country': [
#         'страна', 'производств', 'country', 'сделано',
#         'производитель', 'страна производства'
#     ],
    
#     # Вес
#     'weight': [
#         'вес', 'weight', 'масса', 'гр', 'грамм',
#         'вес товара', 'вес без упаковки'
#     ],
    
#     # Ширина
#     'width': [
#         'ширина', 'width', 'длина', 'size width',
#         'ширина предмета', 'габарит ширина'
#     ],
    
#     # Высота
#     'height': [
#         'высота', 'height', 'толщина', 'size height',
#         'высота предмета', 'габарит высота'
#     ],
    
#     # Тип электродов
#     'electrode_type': [
#         'тип', 'вид', 'type', 'категория',
#         'тип электрод', 'разновидность'
#     ],
    
#     # Материал
#     'material': [
#         'материал', 'material', 'состав', 'ткань',
#         'покрытие', 'основа', 'структура'
#     ],
    
#     # Форма электродов
#     'shape': [
#         'форма', 'shape', 'конфигурация', 'геометрия',
#         'внешний вид', 'дизайн'
#     ],
    
#     # Сопротивление/импеданс
#     'impedance': [
#         'сопротивление', 'импеданс', 'impedance', 'ом',
#         'электрическое сопротивление', 'resistance'
#     ],
    
#     # Срок службы/износостойкость
#     'lifespan': [
#         'срок', 'долговечность', 'lifespan', 'износ',
#         'количество использований', 'ресурс'
#     ],
    
#     # Способ крепления
#     'attachment': [
#         'крепление', 'attachment', 'фиксация', 'липучк',
#         'застежка', 'способ крепления', 'крепления'
#     ],
    
#     # Гелевое покрытие
#     'gel_coating': [
#         'гел', 'gel', 'покрытие', 'conductive gel',
#         'гелевое', 'проводящий гель', 'conductive'
#     ],
    
#     # Регистрационные документы
#     'certification': [
#         'регистрационное', 'удостоверение', 'сертификат',
#         'рзн', 'certification', 'документ', 'разрешение'
#     ]
# }