import re 
import pandas as pd

exclude_patterns = [
        r"электрод", r"шнур", r"кабель", r"провод", 
        r"пластин", r"гель",
        r"крепеж", r"держатель", r"запчасть",
        r"аксессуар", r"led", #r"подставка",
        r"основание"
    ]

def is_relevant(name, exclude_patterns=exclude_patterns, include_patterns=None):
    """
    Универсальная фильтрация товаров по паттернам
    
    Parameters:
    - name: название товара
    - exclude_patterns: список regex-паттернов для исключения
    - include_patterns: список regex-паттернов для обязательного включения
    """
    if pd.isna(name):
        return False
        
    name = name.lower().strip()

    if include_patterns:
        if any(re.search(pattern, name) for pattern in include_patterns):
            return True
    
    # Проверка исключающих паттернов
    if exclude_patterns:
        if any(re.search(pattern, name) for pattern in exclude_patterns):
            return False
    
    return True

def cleaner_products(dirty_df, 
                    percent_feedbacks=20, 
                    id_col="id", 
                    # Параметры фильтрации
                    exclude_patterns=None,
                    include_patterns=None,
                    # Параметры выборки
                    price_segment_samples=30,
                    undervalued_samples=20,
                    min_rating=0,
                    min_feedbacks=1,
                    # Стратегии выборки
                    include_top_by_feedbacks=True,
                    include_price_segments=True,
                    include_undervalued=True):
    """
    Универсальная очистка и фильтрация товаров
    
    Parameters:
    - dirty_df: исходный DataFrame
    - percent_feedbacks: процент товаров с наибольшим количеством отзывов
    - id_col: название колонки с идентификатором
    
    # Параметры фильтрации
    - exclude_patterns: кастомные паттерны для исключения
    - include_patterns: кастомные паттерны для включения  
    
    # Параметры выборки
    - price_segment_samples: количество товаров в каждом ценовом сегменте
    - undervalued_samples: количество недооцененных товаров
    - min_rating: минимальный рейтинг
    - min_feedbacks: минимальное количество отзывов
    
    # Стратегии выборки
    - include_top_by_feedbacks: включать топ по отзывам
    - include_price_segments: включать ценовые сегменты
    - include_undervalued: включать недооцененные товары
    """
    
    # Применяем фильтрацию
    mask = dirty_df['name'].apply(lambda x: is_relevant(
        x, 
        exclude_patterns=exclude_patterns, 
        include_patterns=include_patterns
    ))
    clear_df = dirty_df[mask].copy()

    # Базовые фильтры
    clear_df = clear_df[
        (clear_df['feedbacks'] >= min_feedbacks) & 
        (clear_df['rating'] >= min_rating)
    ]

    selected_ids = set()
    
    # 1. Топ по отзывам
    if include_top_by_feedbacks and percent_feedbacks > 0:
        percentile = 1 - percent_feedbacks/100
        top_feedbacks = clear_df[clear_df['feedbacks'] >= clear_df['feedbacks'].quantile(percentile)]
        selected_ids.update(top_feedbacks[id_col].tolist())
    
    # 2. Сбалансированные выборки по ценовым сегментам
    if include_price_segments and price_segment_samples > 0:
        price_25 = clear_df['price'].quantile(0.25)
        price_75 = clear_df['price'].quantile(0.75)
        
        low_price = clear_df[clear_df['price'] < price_25].nlargest(price_segment_samples, 'feedbacks')
        mid_price = clear_df[(clear_df['price'] >= price_25) & (clear_df['price'] <= price_75)].nlargest(price_segment_samples, 'feedbacks')
        high_price = clear_df[clear_df['price'] > price_75].nlargest(price_segment_samples, 'feedbacks')
        
        selected_ids.update(low_price[id_col].tolist())
        selected_ids.update(mid_price[id_col].tolist())
        selected_ids.update(high_price[id_col].tolist())
    
    # 3. Недооцененные товары
    if include_undervalued and undervalued_samples > 0:
        feedback_median = clear_df['feedbacks'].median()
        undervalued = clear_df[
            (clear_df['rating'] >= 4.8) & 
            (clear_df['price'] < clear_df['price'].median()) & 
            (clear_df['feedbacks'] < feedback_median)
        ].nlargest(undervalued_samples, 'rating')
        selected_ids.update(undervalued[id_col].tolist())
    
    # Возвращаем отфильтрованный DataFrame
    result_df = dirty_df[dirty_df[id_col].isin(selected_ids)].copy()
    
    return result_df