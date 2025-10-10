import os
import importlib

# Автоматически импортируем все .py файлы в папке utils
package_dir = os.path.dirname(__file__)

for filename in os.listdir(package_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        module_name = filename[:-3]  # убираем .py
        try:
            module = importlib.import_module(f'.{module_name}', package='utils')
            globals()[module_name] = module
        except ImportError as e:
            print(f"Warning: Could not import {module_name}: {e}")

__all__ = [name for name in globals() if not name.startswith('_')]