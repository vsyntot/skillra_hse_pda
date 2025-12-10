# Skillra HSE PDA

Аналитика рынка IT-вакансий для карьерного навигатора Skillra. Проект следует ТЗ курса «Python для анализа данных» (этапы 0–4) и использует открытый словарь признаков HeadHunter.

## Установка и запуск пайплайна
1. Создайте окружение: `python -m venv .venv && source .venv/bin/activate`.
2. Установите зависимости: `pip install -r requirements.txt` или `pip install -e . -r requirements.txt` для editable-режима.
3. Убедитесь, что исходный файл лежит по умолчанию в `data/raw/hh_moscow_it_2025_11_30.csv` (не изменяйте raw-данные).
4. Запустите сборку всех артефактов: `python scripts/run_pipeline.py`. Скрипт сам подтянет пути из `src/skillra_pda/config.py` и сохранит `hh_clean.parquet`, `hh_features.parquet` и `market_view.parquet` в `data/processed/`.
5. Быстрый smoke-чек пайплайна: `python scripts/validate_pipeline.py`.
6. Прогон ноутбука end-to-end: `python scripts/validate_notebook.py` (использует `jupyter nbconvert --execute`).

### Полный аналитический пайплайн (от сырого CSV до витрины рынка)
1. Активируйте виртуальное окружение и установите зависимости (см. шаги выше).
2. Подготовьте сырые данные: положите CSV вакансий в `data/raw/hh_moscow_it_2025_11_30.csv` или поправьте путь в `src/skillra_pda/config.py` → `RAW_DATA_FILE`.
3. Запустите скрипт: `python scripts/run_pipeline.py`.
   - На выходе появятся:
     - `data/processed/hh_clean.parquet` — очищенные данные.
     - `data/processed/hh_features.parquet` — фичи (стек, грейд, режим работы, junior-friendly и др.).
     - `data/processed/market_view.parquet` — агрегаты по роли × грейду × городу/домену с долей remote/junior-friendly, медианой зарплат и топ-скиллами.
   - Скрипт печатает пути сохранения, а также применяет обрезку выбросов зарплат и расчёт `primary_role`/`city_tier`, чтобы витрина была готова к использованию агентом Skillra.
4. Для быстрой проверки используйте `python scripts/validate_pipeline.py` (контроль ключевых инвариантов) и при необходимости `pytest`.
5. Чтобы убедиться, что ноутбук повторно воспроизводим, прогоните `python scripts/validate_notebook.py` (скаченные артефакты из `data/processed/` переиспользуются внутри ноутбука).

### Работа с витриной `market_view` и функцией `analyze_persona`
- `market_view`: откройте `data/processed/market_view.parquet` после пайплайна и фильтруйте по нужной роли/грейду/городу. Столбцы `salary_median`, `salary_q25/q75`, `remote_share`, `junior_friendly_share`, `median_tech_stack_size` и `top_skills` дают готовые фразы для Skillra-агента.
- В Python можно загрузить витрину так: `import pandas as pd; mv = pd.read_parquet("data/processed/market_view.parquet")` и далее использовать `mv.query("primary_role == 'Data Analyst' and grade == 'Middle'")` или группировки по `domain`, чтобы формировать карточки сегмента.
- Для персон: импортируйте `Persona` и `analyze_persona` из `src.skillra_pda.personas`. Пример:
  ```python
  from src.skillra_pda.personas import Persona, analyze_persona
  import pandas as pd

  df = pd.read_parquet("data/processed/hh_features.parquet")
  persona = Persona(
      name="switcher_bi",
      description="Свитчер в BI/продакт-аналитику",
      target_roles=["BI Analyst", "Product Analyst"],
      target_grade="Junior",
      current_skills={"excel", "sql", "product"},
  )
  result = analyze_persona(df, persona, top_k=10)
  print(result["market_summary"])
  print(result["skill_gap"])
  print(result["recommended_skills"])
  ```
- `market_summary` показывает размер сегмента и зарплатные квантильные показатели, `skill_gap` раскрывает востребованные навыки с долями требований, а `recommended_skills` — топ навыков с наибольшим гэпом. Эти блоки можно напрямую отдавать AI-агенту Skillra для подсказок и планов развития.

## Как быстро проверить проект
- Активируйте виртуальное окружение и установите зависимости: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Убедитесь, что исходный датасет лежит в `data/raw/hh_moscow_it_2025_11_30.csv` (или измените путь в `src/skillra_pda/config.py`).
- Пример команды для смоук-чека пайплайна: `python scripts/validate_pipeline.py`.
  - Скрипт выводит метрики очистки (количество удалённых дубликатов, долю non-RUB зарплат, наличие `vacancy_age_days`) и итоговую строку `OK` при успешном прохождении инвариантов.
  - В процессе создаётся/обновляется `data/processed/hh_clean.parquet` (требуются права на запись в `data/processed`).
- Пример команды для тестов: `pytest` — прогоняет все юнит-тесты из каталога `tests/`.

## Ноутбук и структура
- Основной отчёт: `notebooks/01_hse_project.ipynb` — строго следует этапам 0–4 (данные → предобработка → признаки → EDA → визуализации) и включает продуктовый слой с персонами.
- Все тяжёлые вычисления вынесены в `src/skillra_pda`, ноутбук переиспользует готовые функции и артефакты из `data/processed`.
- Фигуры сохраняются в `reports/figures` (требование AGENTS.md).

## Артефакты
- `data/processed/hh_clean.parquet` — очищенный датасет.
- `data/processed/hh_features.parquet` — обогащённые признаки (возраст вакансии, стековые счётчики, текстовые метрики, junior-friendly и др.).
- `data/processed/market_view.parquet` — агрегированная витрина рынка (роль × грейд × город/домен) с зарплатами, форматами и топами навыков.
- `reports/figures/*.png` — визуализации зарплат, форматов работы, навыковых тепловых карт и распределений.
- `scripts/run_pipeline.py`, `scripts/validate_notebook.py` — точки входа для воспроизводимости.

## Соответствие ТЗ курса
- Этап 0: описание источника и профиля данных — секция 1 ноутбука.
- Этап 1: предобработка (пропуски, дубликаты, булевые, зарплата) — секция 2.
- Этап 2: новые признаки (city_tier, work_mode, стековые агрегаты, тексты, vacancy_age_days) — секция 3.
- Этап 3: EDA (зарплаты, навыки, бенефиты, soft-skills, junior-friendly) — секция 4.
- Этап 4: визуализации (≥3 типов графиков, heatmap навыков) — секция 5.
- Дополнительно: продуктовый слой с персонами и skill-gap — секция 6.

## Связь с продуктом Skillra
- Карта рынка: зарплаты по грейдам/ролям/городам, форматы работы, востребованные навыки и бенефиты.
- Skill gap: анализ недостающих навыков для целевых персон (студент, свитчер, middle-аналитик).
- Встраиваемость: результаты пайплайна и ноутбука могут питать AI-агента Skillra (рекомендации по развитию и подбору вакансий).
