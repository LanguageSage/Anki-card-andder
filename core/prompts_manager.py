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
                "context": "Analyze the following English sentence and translate it to Spanish:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Spanish]\nCONTEXT: [Explain the English grammar of the sentence, key vocabulary, phrasal verbs, or idioms in Spanish. The entire explanation must be written in Spanish for Spanish-speaking learners of English. Provide 1–3 similar English sentences as examples with Spanish translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to French": {
                "translate": "Translate the following English phrase or sentence into French accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in French. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to French:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into French]\nCONTEXT: [Explain the English grammar of the sentence, key vocabulary, phrasal verbs, or idioms in French. The entire explanation must be written in French for French-speaking learners of English. Provide 1–3 similar English sentences as examples with French translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to German": {
                "translate": "Translate the following English phrase or sentence into German accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in German. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to German:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into German]\nCONTEXT: [Explain the English grammar of the sentence, key vocabulary, phrasal verbs, or idioms in German. The entire explanation must be written in German for German-speaking learners of English. Provide 1–3 similar English sentences as examples with German translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Russian": {
                "translate": "Переведи следующую английскую фразу или предложение на русский язык качественно:\n\n\"{phrase}\"\n\nОтветь только переводом на русском языке. Не используй в ответе кавычки, маркдаун или любой дополнительный текст.",
                "context": "Проанализируй следующее английское предложение и переведи его на русский язык:\n\n\"{phrase}\"\n\nОтветь строго в следующем формате (не добавляй ничего лишнего, без таблиц и маркдауна):\n\nTRANSLATION: [качественный перевод на русский язык]\nCONTEXT: [Подробно объясни грамматику английского предложения (времена, конструкции, модальные глаголы), ключевые английские слова, фразовые глаголы или идиомы. Все объяснения должны быть написаны исключительно на русском языке для людей, изучающих английский. Приведи 1-3 похожих примера предложений на английском языке с переводом на русский. Избегай таблиц.]",
                "delimiter": "CONTEXT"
            },
            "English to Chinese (Mandarin)": {
                "translate": "Translate the following English phrase or sentence into Chinese (Simplified) accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Chinese. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Chinese (Simplified):\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Simplified Chinese with Pinyin in parentheses]\nCONTEXT: [Explain the English grammar of the sentence, key vocabulary, phrasal verbs, or idioms in Simplified Chinese. The entire explanation must be written in Simplified Chinese for Chinese-speaking learners of English. Provide 1–3 similar English sentences as examples with Pinyin and Simplified Chinese translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Japanese": {
                "translate": "Translate the following English phrase or sentence into Japanese accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Japanese. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Japanese:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Japanese (Kanji/Kana) with Romaji in parentheses]\nCONTEXT: [Explain the English grammar of the sentence, key vocabulary, phrasal verbs, or idioms in Japanese. The entire explanation must be written in Japanese for Japanese-speaking learners of English. Provide 1–3 similar English sentences as examples with Japanese and Romaji translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Italian": {
                "translate": "Translate the following English phrase or sentence into Italian accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Italian. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Italian:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Italian]\nCONTEXT: [Explain the English grammar of the sentence, key vocabulary, phrasal verbs, or idioms in Italian. The entire explanation must be written in Italian for Italian-speaking learners of English. Provide 1–3 similar English sentences as examples with Italian translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Portuguese": {
                "translate": "Translate the following English phrase or sentence into Portuguese accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Portuguese. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Portuguese:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Portuguese]\nCONTEXT: [Explain the English grammar of the sentence, key vocabulary, phrasal verbs, or idioms in Portuguese. The entire explanation must be written in Portuguese for Portuguese-speaking learners of English. Provide 1–3 similar English sentences as examples with Portuguese translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Arabic": {
                "translate": "Translate the following English phrase or sentence into Arabic accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Arabic. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Arabic:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Arabic]\nCONTEXT: [Explain the English grammar of the sentence, key vocabulary, phrasal verbs, or idioms in Arabic. The entire explanation must be written in Arabic for Arabic-speaking learners of English. Provide 1–3 similar English sentences as examples with Arabic translations. Avoid tables.]",
                "delimiter": "CONTEXT"
            },
            "English to Hindi": {
                "translate": "Translate the following English phrase or sentence into Hindi accurately:\n\n\"{phrase}\"\n\nRespond ONLY with the translation in Hindi. Do not use quotes, markdown, or any extra text.",
                "context": "Analyze the following English sentence and translate it to Hindi:\n\n\"{phrase}\"\n\nRespond strictly in the following format (do not add any extra commentary or markdown):\n\nTRANSLATION: [natural and accurate translation into Hindi]\nCONTEXT: [Explain the English grammar of the sentence, key vocabulary, phrasal verbs, or idioms in Hindi. The entire explanation must be written in Hindi for Hindi-speaking learners of English. Provide 1–3 similar English sentences as examples with Hindi translations. Avoid tables.]",
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
