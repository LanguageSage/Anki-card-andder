# -*- coding: utf-8 -*-
"""
Модуль управления промптами.
Загрузка, сохранение и редактирование промптов AI.
"""
import os
import json
from typing import Dict, Optional

from core.settings_manager import get_user_dir, get_data_dir, get_resource_path, DEFAULT_TRANSLATE_PROMPT, DEFAULT_CONTEXT_PROMPT


def get_prompts_file_path() -> str:
    """Возвращает путь к файлу промптов (сначала во внешней папке data)"""
    external_path = os.path.join(get_data_dir(), "prompts.json")
    if os.path.exists(external_path):
        return external_path
    
    # Если внешнего нет, возвращаем путь, куда он должен быть сохранен или взят из ресурсов
    return external_path


class PromptsManager:
    """Менеджер для работы с промптами"""
    
    def __init__(self):
        self.prompts_file = get_prompts_file_path()
        self._cache: Optional[Dict] = None
    
    def load_prompts(self, force_reload: bool = False) -> Dict:
        """
        Загружает промпты из файла.
        """
        if self._cache is not None and not force_reload:
            return self._cache
            
        # Пытаемся загрузить из внешнего файла
        if os.path.exists(self.prompts_file):
            try:
                with open(self.prompts_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                    return self._cache
            except Exception as e:
                print(f"⚠️ Ошибка загрузки внешних промптов: {e}")

        # Если внешнего нет, пытаемся загрузить из внутренних ресурсов
        try:
            resource_path = get_resource_path("prompts.json")
            if os.path.exists(resource_path):
                with open(resource_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
                    return self._cache
        except Exception as e:
            print(f"⚠️ Ошибка загрузки встроенных промптов: {e}")
        
        self._cache = {}
        return self._cache
    
    def save_prompts(self, prompts: Dict) -> bool:
        """
        Сохраняет промпты в файл.
        
        Args:
            prompts: Dict с промптами
            
        Returns:
            True при успехе
        """
        try:
            with open(self.prompts_file, "w", encoding="utf-8") as f:
                json.dump(prompts, f, ensure_ascii=False, indent=2)
            self._cache = prompts
            return True
        except Exception as e:
            print(f"❌ Ошибка сохранения промптов: {e}")
            return False
    
    def get_preset(self, name: str) -> Optional[Dict]:
        """Получает пресет по имени"""
        prompts = self.load_prompts()
        return prompts.get(name)
    
    def save_preset(self, name: str, translate_prompt: str, context_prompt: str) -> bool:
        """Сохраняет или обновляет пресет"""
        prompts = self.load_prompts()
        prompts[name] = {
            "translate": translate_prompt,
            "context": context_prompt
        }
        return self.save_prompts(prompts)
    
    def delete_preset(self, name: str) -> bool:
        """Удаляет пресет"""
        prompts = self.load_prompts()
        if name in prompts:
            del prompts[name]
            return self.save_prompts(prompts)
        return False
    
    def rename_preset(self, old_name: str, new_name: str) -> bool:
        """Переименовывает пресет"""
        prompts = self.load_prompts()
        if old_name not in prompts:
            return False
        if new_name in prompts:
            print(f"⚠️ Пресет '{new_name}' уже существует")
            return False
        
        prompts[new_name] = prompts.pop(old_name)
        return self.save_prompts(prompts)
    
    def get_delimiter(self, name: str) -> str:
        """Получает разделитель контекста для пресета"""
        preset = self.get_preset(name)
        if preset:
             return preset.get("delimiter", "КОНТЕКСТ")
        return "КОНТЕКСТ"

    def get_preset_names(self) -> list:
        """Возвращает отсортированный список имен пресетов"""
        return sorted(self.load_prompts().keys())
    
    def create_defaults_if_missing(self) -> bool:
        """
        Создает файл с дефолтными промптами если его нет.
        
        Returns:
            True если файл был создан или уже существует
        """
        if os.path.exists(self.prompts_file):
            return True
        
        default_prompts = self._get_default_prompts()
        return self.save_prompts(default_prompts)
    
    def _get_default_prompts(self) -> Dict:
        """Возвращает дефолтные промпты для перевода с английского на популярные языки"""
        return {
            "English to Spanish": {
                "translate": "Translate the following English phrase or sentence into Spanish accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Spanish. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Spanish:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Spanish]\nCONTEXT: [briefly explain key vocabulary, verb conjugations, gender/number agreement, grammatical points, and provide 1–3 similar example sentences with English translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to French": {
                "translate": "Translate the following English phrase or sentence into French accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in French. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to French:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into French]\nCONTEXT: [briefly explain key vocabulary, French verb tenses, gender agreement, grammatical points, and provide 1–3 similar example sentences with English translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to German": {
                "translate": "Translate the following English phrase or sentence into German accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in German. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to German:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into German]\nCONTEXT: [briefly explain key vocabulary, German cases (nominative, accusative, dative, genitive), verb placement, and provide 1–3 similar example sentences with English translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Russian": {
                "translate": "Translate the following English phrase or sentence into Russian accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Russian. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Russian:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Russian]\nCONTEXT: [briefly explain key vocabulary, Russian cases, verb aspects (perfective/imperfective), word order, and provide 1–3 similar example sentences with English translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Chinese (Mandarin)": {
                "translate": "Translate the following English phrase or sentence into Chinese (Simplified) accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Chinese. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Chinese (Simplified):\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Simplified Chinese with Pinyin in parentheses]\nCONTEXT: [briefly explain key vocabulary, Chinese grammar patterns, measure words, particle usage, and provide 1–3 similar example sentences with Pinyin and English translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Japanese": {
                "translate": "Translate the following English phrase or sentence into Japanese accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Japanese. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Japanese:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Japanese (Kanji/Kana) with Romaji in parentheses]\nCONTEXT: [briefly explain key vocabulary, Japanese particles, politeness levels (polite/casual), grammar points, and provide 1–3 similar example sentences with Romaji and English translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Italian": {
                "translate": "Translate the following English phrase or sentence into Italian accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Italian. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Italian:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Italian]\nCONTEXT: [briefly explain key vocabulary, Italian verb conjugations, articles, preposition contractions, and provide 1–3 similar example sentences with English translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Portuguese": {
                "translate": "Translate the following English phrase or sentence into Portuguese accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Portuguese. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Portuguese:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Portuguese]\nCONTEXT: [briefly explain key vocabulary, Portuguese verb tenses, gender agreement, pronoun placement, and provide 1–3 similar example sentences with English translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Arabic": {
                "translate": "Translate the following English phrase or sentence into Arabic accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Arabic. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Arabic:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Arabic]\nCONTEXT: [briefly explain key vocabulary, Arabic root system, verb forms, sentence structure (nominal/verbal), and provide 1–3 similar example sentences with transliteration and English translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Hindi": {
                "translate": "Translate the following English phrase or sentence into Hindi accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Hindi. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Hindi:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Hindi]\nCONTEXT: [briefly explain key vocabulary, Hindi postpositions, verb-subject agreement, gender in Hindi nouns, and provide 1–3 similar example sentences with English translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            }
        }


# Глобальный экземпляр менеджерa промптов
prompts_manager = PromptsManager()


def update_active_prompts(translate_prompt: str, context_prompt: str, delimiter: str = "КОНТЕКСТ"):
    """
    Обновляет активные промпты в текущем сеансе.
    Совместимость со старым кодом.
    """
    from core.app_state import app_state
    app_state.translate_prompt = translate_prompt
    app_state.context_prompt = context_prompt
    app_state.context_delimiter = delimiter


def rename_prompt_preset(old_name: str, new_name: str) -> bool:
    """
    Переименовывает пресет и обновляет UI.
    Совместимость со старым кодом.
    """
    from core.app_state import app_state
    
    if not prompts_manager.rename_preset(old_name, new_name):
        return False
    
    # Обновляем UI главного окна если пресет был выбран
    try:
        if app_state.main_window_components and "vars" in app_state.main_window_components:
            prompt_var = app_state.main_window_components["vars"].get("prompt_var")
            if prompt_var and prompt_var.get() == old_name:
                prompt_var.set(new_name)
            
            # Обновляем список в комбобоксе
            prompt_combo = app_state.main_window_components["widgets"].get("prompt_combo")
            if prompt_combo:
                prompt_combo.configure(values=prompts_manager.get_preset_names())
    except Exception as e:
        print(f"⚠️ Ошибка обновления UI после переименования: {e}")
    
    return True
