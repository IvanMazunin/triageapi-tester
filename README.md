# AI API Bombardier

## Инфраструктура
- **Ollama** - локальный сервер для LLM
- **qwen2.5-coder:3b** - нейросеть для генерации атак
- **Python 3.14** - рантайм тестировщика

## Запуск

1. Установить Ollama: https://ollama.com
2. Запустить сервер: `ollama serve`
3. Скачать модель: `ollama pull qwen2.5-coder:3b`
4. Запустить тестирование: `python bombardier.py`

## GitHub Actions
При пуше в main автоматически запускается бомбардировка API.
Отчет сохраняется как artifact.

## Результаты
Файл `bombardment_report.json` содержит все найденные уязвимости.