from selenium.webdriver.common.by import By

# Конфиг для парсинга Ozon
OZON_SELECTORS = {
    'specifications': {
        'section': (By.ID, 'section-characteristics'),
        'items_container': (By.CSS_SELECTOR, '.pdp_ha5'),
        'items': (By.CSS_SELECTOR, 'dl.pdp_ha9'),
        'key': (By.CSS_SELECTOR, '.pdp_ha8 span.pdp_ah9, .pdp_ha8'),
        'value': (By.CSS_SELECTOR, '.pdp_h8a'),
        'value_text': (By.CSS_SELECTOR, '.pdp_ai0, .pdp_ia span:first-child'),
    }
}