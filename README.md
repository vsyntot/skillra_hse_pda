# Skillra HSE PDA

Набор утилит и ноутбук для курса «Python для анализа данных» (Skillra + ВШЭ).

## Быстрый старт (CLI)
1. Создайте виртуальное окружение (`python -m venv .venv && source .venv/bin/activate`).
2. Установите зависимости: `pip install -r requirements.txt` или сразу в editable-режиме `pip install -e .`.
3. Убедитесь, что исходные данные лежат в `data/raw/hh_moscow_it_2025_11_30.csv` (не изменяйте их).
4. Прогоните быструю регрессию пайплайна: `python scripts/validate_pipeline.py` — она загрузит CSV, выполнит cleaning и сохранит parquet в `data/processed`.
5. Полный прогон без ноутбука: `python scripts/run_pipeline.py` (чистые и фичевые parquet-файлы окажутся в `data/processed`).
6. Откройте финальный ноутбук `notebooks/01_hse_project.ipynb` и запустите **Run All**.

## Работа в PyCharm
1. Откройте корень репозитория как проект.
2. Выберите интерпретатор из `.venv` (или создайте его прямо в PyCharm) и выполните `pip install -e . -r requirements.txt`.
3. Убедитесь, что каталог `src` отмечен как Source Root (PyCharm сделает это автоматически после editable-установки; при необходимости кликните правой кнопкой → *Mark Directory as* → *Sources Root*).
4. Для работы с ноутбуками добавьте ядро: `python -m ipykernel install --user --name skillra-pda` и выберите его в PyCharm/IDEA.
5. Готовые Run/Debug конфигурации можно создавать для сценариев из `scripts/` (рабочая директория — корень репозитория).

## Структура
- `src/skillra_pda/` — функции загрузки, очистки, фичей, визуализации и продуктового слоя.
- `data/` — `raw` для исходных CSV, `processed` для подготовленных данных.
- `reports/figures/` — папка для сохранения графиков.
- `notebooks/01_hse_project.ipynb` — основной отчёт с ходом анализа.
- `scripts/validate_pipeline.py` — быстрый скрипт для проверки пайплайна без ноутбука.
- `scripts/run_pipeline.py` — полный прогон cleaning → features → сохранение parquet.
- `parser/hse_vacancies/hh_scraper.py` — вспомогательный парсер исходного датасета (используется только для сбора, не нужен в основном пайплайне).
