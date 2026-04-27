import requests
import json
import time
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ===== КОНФИГУРАЦИЯ =====
OLLAMA_URL = "http://localhost:11434/api/generate"
# Модель
MODEL_NAME = "qwen2.5-coder:3b"

#API
TARGET_API = "http://localhost:5188"

TEST_CREDENTIALS = {
    "smpNumber": "12",
    "login": "1262",
    "password": "+12345"
}

# Глобальный токен
jwt_token = None

# ===== ЭНДПОИНТЫ ДЛЯ ТЕСТИРОВАНИЯ =====
ENDPOINTS = [
    # Аутентификация (без токена)
    {
        "path": "/triage-api/auth/login",
        "method": "POST",
        "requires_auth": False,
        "description": "Логин и получение JWT токена",
        "schema": {
            "smpNumber": "string",
            "login": "string", 
            "password": "string"
        }
    },
    {
        "path": "/triage-api/auth/who-i-am",
        "method": "POST",
        "requires_auth": True,
        "description": "Получить данные о себе (требует токен)",
        "schema": None
    },
    
    # Чрезвычайные ситуации
    {
        "path": "/triage-api/emergency-situations",
        "method": "POST",
        "requires_auth": True,
        "description": "Создать или обновить ЧС",
        "schema": {
            "id": "uuid (опционально)",
            "clientCreationTime": "ISO дата-время",
            "clientLastUpdateTime": "ISO дата-время", 
            "isDeleted": False,
            "isClosed": False,
            "emergencySituationTime": "ISO дата-время",
            "reason": "string",
            "clarifications": "string",
            "haveRadiationContamination": False,
            "haveChemicalContamination": False,
            "havePsychicContamination": False,
            "haveBiologicalContamination": False,
            "deathToll": 0,
            "victimsCount": 0,
            "haveFemaleVictims": False,
            "haveChildrenVictims": False,
            "havePregnantVictims": False,
            "city": "Москва",
            "street": "ул. Примерная",
            "buildingNumber": "1",
            "latitude": 55.7558,
            "longitude": 37.6176
        }
    },
    {
        "path": "/triage-api/emergency-situations/page",
        "method": "GET",
        "requires_auth": True,
        "description": "Получить страницу с ЧС",
        "params": ["toSkip", "toTake"],
        "schema": None
    },
    {
        "path": "/triage-api/emergency-situations/opened",
        "method": "GET",
        "requires_auth": True,
        "description": "Получить все открытые ЧС",
        "params": ["lastUpdateTime"],
        "schema": None
    },
    # Пострадавшие
    {
        "path": "/triage-api/emergency-situations/victims",
        "method": "POST",
        "requires_auth": True,
        "description": "Создать или обновить пострадавшего",
        "schema": {
            "id": "uuid (опционально)",
            "emergencySituationId": "uuid",
            "number": "001",
            "sortingCard": {
                "id": "uuid (опционально)",
                "creationTime": "ISO дата-время",
                "sendingTime": "ISO дата-время",
                "sortingPointId": "uuid",
                "version": "1.0",
                "isDeleted": False,
                "name": "Иван",
                "surname": "Иванов",
                "fullYears": 30,
                "traumas": ["S00"],
                "specialSigns": []
            }
        }
    },
    
    # Справочники
    {
        "path": "/triage-api/handbooks/descriptors",
        "method": "GET",
        "requires_auth": True,
        "description": "Получить описания справочников",
        "schema": None
    },
    {
        "path": "/triage-api/handbooks",
        "method": "GET",
        "requires_auth": True,
        "description": "Получить содержимое справочника",
        "params": ["version"],
        "schema": None
    }
]


# ===== ФУНКЦИИ =====

def ask_ai(prompt: str, timeout: int = 60) -> str:
    """Отправить запрос к нейросети deepseek-coder"""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.9,
            "num_predict": 500
        }
    }
    
    try:
        print(f"    Запрос к нейросети (таймаут {timeout}с)...", end=" ", flush=True)
        response = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
        print("OK")
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except requests.exceptions.Timeout:
        print(f"\n    Таймаут {timeout}с - модель думает слишком долго")
        return ""
    except Exception as e:
        print(f"\n    Ошибка: {e}")
        return ""

def get_malicious_values() -> List[Dict]:
    """Получить список вредоносных значений для тестирования через нейросеть"""
    
    prompt = """Generate 8 malicious test values for API security testing.
Return ONLY valid JSON array. Do NOT use any expressions like "A".repeat() - use actual strings.
Example: [{"type":"sql","value":"' OR '1'='1"}, {"type":"xss","value":"<script>"}]
Response should be ONLY JSON, no explanations, no markdown.

Response:"""

    response = ask_ai(prompt, timeout=45)
    
    #print(response)
    
    # Парсинг JSON
    if response:
        try:
            # Очищаем ответ от markdown и лишних символов
            clean_response = response.strip()
            # Убираем возможные маркеры кода
            if clean_response.startswith('```json'):
                clean_response = clean_response[7:]
            if clean_response.startswith('```'):
                clean_response = clean_response[3:]
            if clean_response.endswith('```'):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            #print(clean_response)
            
            # Находим JSON массив
            start = clean_response.find('[')
            end = clean_response.rfind(']') + 1
            if start != -1 and end > start:
                json_str = clean_response[start:end]
                attacks = json.loads(json_str)
                if attacks and isinstance(attacks, list):
                    print(f"    Успешно подготовлено {len(attacks)} атак")
                    return attacks
        except json.JSONDecodeError as e:
            print(f"    Ошибка парсинга JSON: {e}")

def get_jwt_token() -> Optional[str]:
    """Получить JWT токен через логин"""
    print("\n Получение JWT токена...")
    try:
        login_response = requests.post(
            f"{TARGET_API}/triage-api/auth/login",
            json=TEST_CREDENTIALS,
            timeout=10
        )
        
        if login_response.status_code == 200:
            result = login_response.json()
            token = result.get('data')
            if token:
                print(f"    Токен получен ({token[:50]}...)")
                return token
            else:
                print(f"    Ответ без токена: {json.dumps(result, ensure_ascii=False)[:200]}")
                return None
        else:
            print(f"    Ошибка {login_response.status_code}: {login_response.text[:200]}")
            return None
    except Exception as e:
        print(f"    Ошибка: {e}")
        return None

def make_request(endpoint: Dict, test_value: Any) -> Dict:
    """Отправить запрос на API с тестовым значением"""
    global jwt_token
    
    url = f"{TARGET_API}{endpoint['path']}"
    headers = {"Content-Type": "application/json"}
    
    if endpoint.get('requires_auth') and jwt_token:
        headers["Authorization"] = f"Bearer {jwt_token}"
    
    start_time = time.time()
    
    try:
        if endpoint['method'] == 'GET':
            # Для GET запросов
            if endpoint.get('params'):
                params = {p: str(test_value) for p in endpoint['params']}
                resp = requests.get(url, params=params, headers=headers, timeout=10)
            else:
                resp = requests.get(url, headers=headers, timeout=10)
        
        elif endpoint['method'] == 'POST':
            # Для POST запросов - пробуем разные форматы тела
            if isinstance(test_value, dict):
                body = test_value
            elif isinstance(test_value, str) and test_value.startswith('{'):
                # Пробуем парсить как JSON
                try:
                    body = json.loads(test_value)
                except:
                    body = {"input": test_value}
            else:
                body = {"input": test_value}
            
            resp = requests.post(url, json=body, headers=headers, timeout=10)
        
        response_time = (time.time() - start_time) * 1000
        
        # Определяем потенциальную уязвимость
        is_vulnerable = (
            resp.status_code >= 500 or      # Серверная ошибка
            resp.status_code == 200 or
            "timeout" in resp.text.lower() or
            len(resp.text) > 50000          # Возможна DoS
        )
        
        return {
            "status": resp.status_code,
            "time_ms": round(response_time, 1),
            "vulnerable": is_vulnerable,
            "response_preview": resp.text[:200],
            "test_value": str(test_value)[:100]
        }
        
    except requests.exceptions.Timeout:
        return {
            "status": 0,
            "time_ms": 10000,
            "vulnerable": True,
            "response_preview": "TIMEOUT - возможна DoS уязвимость",
            "test_value": str(test_value)[:100]
        }
    except Exception as e:
        return {
            "status": 0,
            "vulnerable": True,
            "response_preview": str(e)[:200],
            "test_value": str(test_value)[:100]
        }

def run_bombardment():
    """Главная функция - запуск атаки"""
    global jwt_token
    
    print("=" * 70)
    print("AI BOMBARDIER - Triage API Security Testing")
    print(f"Модель: {MODEL_NAME}")
    print("=" * 70)
    
    # Проверка Ollama
    print("\n Проверка инфраструктуры...")
    test_response = ask_ai("Respond: OK", timeout=30)
    if test_response:
        print(f"    Нейросеть отвечает: {test_response[:50]}")
    else:
        print("    Нейросеть не ответила, но продолжаем с fallback атаками")
    
    # Получение токена
    jwt_token = get_jwt_token()
    if not jwt_token:
        print("\n JWT токен не получен. Некоторые эндпоинты будут выдавать 401.")
    
    # Получаем вредоносные значения от нейросети
    print("\n Генерация тестовых значений нейросетью...")
    malicious_values = get_malicious_values()
    print(f"    Сгенерировано {len(malicious_values)} тестовых значений")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "target": TARGET_API,
        "model": MODEL_NAME,
        "jwt_obtained": bool(jwt_token),
        "total_tests": 0,
        "vulnerabilities": [],
        "endpoint_results": {}
    }
    
    # Бомбардировка
    for endpoint in ENDPOINTS:
        print(f"\n{'='*60}")
        print(f" ТЕСТИРУЕМ: {endpoint['method']} {endpoint['path']}")
        print(f"    {endpoint['description']}")
        
        endpoint_vulns = []
        
        for i, test in enumerate(malicious_values, 1):
            attack_type = test.get('type', 'unknown')
            test_value = test.get('value', 'test')
            
            print(f"    [{i}/{len(malicious_values)}] {attack_type}", end=" ... ")
            
            result = make_request(endpoint, test_value)
            
            if result['vulnerable']:
                print(f"  УЯЗВИМОСТЬ! (HTTP {result['status']})")
                endpoint_vulns.append({
                    "attack_type": attack_type,
                    "test_value": test_value,
                    "response_status": result['status'],
                    "response_preview": result['response_preview']
                })
                report["vulnerabilities"].append({
                    "endpoint": endpoint['path'],
                    "method": endpoint['method'],
                    "attack_type": attack_type,
                    "test_value": str(test_value)[:200],
                    "response_status": result['status'],
                    "response_preview": result['response_preview']
                })
            else:
                status_icon = "ОК" if result['status'] < 400 else "!!!"
                print(f" {status_icon} {result['status']} ({result['time_ms']}ms)")
        
        report["endpoint_results"][endpoint['path']] = {
            "method": endpoint['method'],
            "total_tests": len(malicious_values),
            "vulnerabilities": len(endpoint_vulns)
        }
        
        vuln_count = len(endpoint_vulns)
        if vuln_count > 0:
            print(f"   ИТОГ:  {vuln_count}/{len(malicious_values)} уязвимостей")
        else:
            print(f"   ИТОГ:  {vuln_count}/{len(malicious_values)} уязвимостей")
    
    # Финальный отчет
    print("\n" + "=" * 70)
    print("ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 70)
    print(f"НАЙДЕНО УЯЗВИМОСТЕЙ: {len(report['vulnerabilities'])}")
    
    if report['vulnerabilities']:
        print("\n ДЕТАЛИЗАЦИЯ:")
        for i, vuln in enumerate(report['vulnerabilities'], 1):
            print(f"\n   {i}. {vuln['method']} {vuln['endpoint']}")
            print(f"      Атака: {vuln['attack_type']}")
            print(f"      Payload: {vuln['test_value'][:80]}")
            print(f"      Ответ: {vuln['response_status']} - {vuln['response_preview'][:80]}")
    
    # Сохраняем отчеты
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    report_filename = f"security_report_{timestamp}.json"
    with open(report_filename, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n JSON отчет: {report_filename}")
    
    # Краткий текстовый отчет
    summary_filename = f"security_report_{timestamp}.txt"
    with open(summary_filename, "w", encoding="utf-8") as f:
        f.write(f"Triage API Security Report\n")
        f.write(f"==========================\n\n")
        f.write(f"Модель: {MODEL_NAME}\n")
        f.write(f"Время: {report['timestamp']}\n")
        f.write(f"JWT получен: {'Да' if jwt_token else 'Нет'}\n\n")
        f.write(f"Всего тестов: {report['total_tests']}\n")
        f.write(f"Найдено уязвимостей: {len(report['vulnerabilities'])}\n\n")
        
        if report['vulnerabilities']:
            f.write("=== УЯЗВИМОСТИ ===\n")
            for vuln in report['vulnerabilities']:
                f.write(f"\n[{vuln['method']}] {vuln['endpoint']}\n")
                f.write(f"  Тип: {vuln['attack_type']}\n")
                f.write(f"  Payload: {vuln['test_value']}\n")
                f.write(f"  Статус: {vuln['response_status']}\n")
    
    print(f" Текстовый отчет: {summary_filename}")
    
    return report

if __name__ == "__main__":
    run_bombardment()