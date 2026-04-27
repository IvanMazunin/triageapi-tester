#!/usr/bin/env python3
"""
AI Bombardier - автоматический фаззинг Triage API с помощью нейросети
Адаптировано под Swagger/OpenAPI спецификацию
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid

# ===== КОНФИГУРАЦИЯ =====
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "jetbrains/mellum-4b-sft-kotlin:Q4_K_M"  # или "llama3.2:3b"

#API
TARGET_API = "http://localhost:5188"

# Тестовые учетные данные
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
    
    # Инциденты
    {
        "path": "/triage-api/emergency-situations/{emergencySituationId}/incidents",
        "method": "POST",
        "requires_auth": True,
        "has_path_param": True,
        "path_param_name": "emergencySituationId",
        "description": "Создать или обновить инцидент",
        "schema": {
            "id": "uuid (опционально)",
            "clientCreationTime": "ISO дата-время",
            "clientLastUpdateTime": "ISO дата-время",
            "isDeleted": False,
            "incidentTime": "ISO дата-время",
            "reason": "string",
            "clarifications": "string",
            "brigadeNeedsEvacuation": False,
            "deathToll": 0,
            "victimsCount": 0,
            "city": "Москва",
            "street": "ул. Примерная",
            "buildingNumber": "1",
            "latitude": 55.7558,
            "longitude": 37.6176
        }
    },
    
    # Запросы
    {
        "path": "/triage-api/emergency-situations/{emergencySituationId}/emergency-requests",
        "method": "POST",
        "requires_auth": True,
        "has_path_param": True,
        "path_param_name": "emergencySituationId",
        "description": "Создать запрос во время ЧС",
        "schema": {
            "id": "uuid (опционально)",
            "clientCreationTime": "ISO дата-время",
            "clientLastUpdateTime": "ISO дата-время",
            "isDeleted": False,
            "isGranted": True,
            "needPolice": False,
            "needFirefighters": False,
            "additionalSortingCrews": 0,
            "additionalEvacuationCrews": 0
        }
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


if __name__ == "__main__":
    print()