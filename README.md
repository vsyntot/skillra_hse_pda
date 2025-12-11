# Skillra HSE PDA

Учебный проект по курсу «Python для анализа данных» (ВШЭ), который служит продуктовым фундаментом для Skillra Career & Job Market Navigator. Пайплайн строит витрину рынка IT-вакансий, EDA и продуктовые инсайты (персоны, skill-gap) для дальнейшей интеграции в сервис Skillra.

## Структура репозитория
- `data/` — исходные (`raw/`) и обработанные (`processed/`) данные, включая итоговую витрину рынка.
- `docs/` — дополнительная документация (например, словарь признаков HH).
- `notebooks/` — основной ноутбук отчёта `01_hse_project.ipynb` (этапы 0–4, EDA, персоны, выводы).
- `parser/` — компоненты для сбора вакансий с hh.ru.
- `src/skillra_pda/` — пакет с логикой проекта (`cleaning.py`, `features.py`, `eda.py`, `viz.py`, `market.py`, `personas.py`).
- `scripts/` — точки входа пайплайна (`run_pipeline.py`, `validate_pipeline.py`, `validate_notebook.py`).
- `tests/` — юнит-тесты основных модулей.
- `reports/` — артефакты визуализаций (`figures/`).

## Установка окружения
1. Создайте виртуальное окружение: `python -m venv .venv && source .venv/bin/activate`.
2. Установите зависимости: `pip install -r requirements.txt` или `pip install -e . -r requirements.txt` для editable-режима (в них уже есть parquet‑движок `pyarrow`). При необходимости установите `pyarrow` отдельно: `pip install pyarrow`.
3. Убедитесь, что сырые данные лежат по умолчанию в `data/raw/hh_moscow_it_2025_11_30.csv` (путь можно изменить в `src/skillra_pda/config.py`).

## Запуск пайплайна
- Полный аналитический цикл: `python scripts/run_pipeline.py` — очистка, генерация признаков и сборка витрины рынка (`hh_clean.parquet`, `hh_features.parquet`, `market_view.parquet`) в `data/processed/`.
- Быстрый smoke-чек: `python scripts/validate_pipeline.py` — проверка ключевых инвариантов и путей.

## Парсер hh.ru
- Полный сбор свежих IT-вакансий: `python parser/hh_scraper.py --limit 10000` (по умолчанию широкая булева строка по IT-ролям, регионы СНГ, задержки и ротация user-agent). Такой прогон может занять ~8 часов и сохранит CSV в `data/raw/`.
- Тестовый/быстрый прогон: выставьте `DEFAULT_LIMIT = 50` в `parser/hh_scraper.py` или запустите `python parser/hh_scraper.py --limit 50 --output data/raw/hh_test.csv`.
- Скрипт принимает параметры для `--areas`, `--max-pages`, `--proxies`, `--output`; ежедневный запуск собирает дельту активных вакансий, чтобы поддерживать актуальность витрины.

## Проверка и тесты
- Юнит-тесты: `pytest`.
- Повторное выполнение ноутбука: `python scripts/validate_notebook.py` (опционально, для полного воспроизведения отчёта).

## Работа с анализом/ноутбуком
Откройте `notebooks/01_hse_project.ipynb`. Внутри:
- Вводная и этап 0: описание парсера hh.ru, сырой датасет, ограничения.
- Этап 1: предобработка (очистка, дубликаты, пропуски, обработка зарплат).
- Этап 2: генерация признаков (city_tier, work_mode, primary_role, stack-size, junior_friendly и др.).
- Этап 3: EDA — зарплаты, форматы работы, роли, навыки, домены, английский, образование, работодатели, корреляционный анализ.
- Этап 4: визуализации/сводка и продуктовый слой с персонами, итоговые выводы и чек-лист ТЗ.

## Ключевые артефакты
- `data/processed/hh_clean.parquet` — очищенный датасет вакансий.
- `data/processed/hh_features.parquet` — данные с engineered-признаками для дальнейшей аналитики и персон.
- `data/processed/market_view.parquet` — агрегированная витрина (роль × грейд × город/домен) с зарплатами, долями remote/junior-friendly, размерами стеков и топовыми навыками.
- `reports/figures/*.png` — сохранённые графики EDA.

## Personas API
Используйте `src/skillra_pda/personas.analyze_persona` для анализа конкретной персоны на фичевом датасете:
```python
from src.skillra_pda.personas import Persona, analyze_persona
import pandas as pd

features = pd.read_parquet("data/processed/hh_features.parquet")
persona = Persona(
    name="switcher_bi",
    description="Свитчер в BI/продакт-аналитику",
    target_roles=["BI Analyst", "Product Analyst"],
    target_grade="Junior",
    current_skills={"excel", "sql", "product"},
)
result = analyze_persona(features, persona, top_k=10)
print(result["market_summary"])
print(result["skill_gap"])
print(result["recommended_skills"])
```
`market_summary` даёт объём и зарплаты целевого сегмента, `skill_gap` — востребованные навыки и их дефицит, `recommended_skills` — список навыков для роста.

## Связь с продуктом Skillra
Полученные витрины и визуализации помогают Skillra:
- строить карту рынка по ролям/грейдам/городам с зарплатами и форматами работы;
- выявлять skill-gap для разных сценариев (студент, свитчер, middle) через Personas API;
- генерировать рекомендации и подсказки для пользователя Career & Job Market Navigator.
