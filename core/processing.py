# -*- coding: utf-8 -*-
"""
Обработка очередей сообщений.
"""
import tkinter as tk
from tkinter import messagebox
import queue
import threading
import os

from core.app_state import app_state
from core.settings_manager import load_settings, DEFAULT_DECK_NAME
from core import audio_utils
from api.anki_api import anki_api
from core.workers import add_to_anki_worker, format_clipboard_text
from core.localization import localization_manager
# NOTE: update_processing_indicator импортируется внутри функций чтобы избежать циклического импорта


def process_clipboard_queue(root):
    """Обрабатывает очередь буфера обмена"""
    from core.ui_callbacks import update_processing_indicator
    
    if not root or not root.winfo_exists():
        return
    
    try:
        new_text = app_state.clipboard_queue.get_nowait()
        print(f"📥 Обработка текста из очереди: {len(new_text)} символов")
        
        widgets = app_state.main_window_components["widgets"]
        tvars = app_state.main_window_components["vars"]
        app_state.main_window_components["original_phrase"] = new_text
        
        widgets["german_text"].configure(text_color=("gray10", "gray90"))
        widgets["german_text"].delete("1.0", tk.END)
        widgets["german_text"].insert("1.0", format_clipboard_text(new_text))
        
        widgets["translation_text"].configure(text_color=("gray10", "gray90"))
        widgets["translation_text"].delete("1.0", tk.END)
        
        widgets["context_widget"].configure(text_color=("gray10", "gray90"))
        widgets["context_widget"].delete("1.0", tk.END)
        
        root.deiconify()
        root.focus_force()
        widgets["german_text"].focus_set()
        
        # Режим собирателя - дописываем текст в панель пакетной обработки
        collector_enabled = tvars.get("collector_mode_var") and tvars["collector_mode_var"].get()
        if collector_enabled:
            batch_input = widgets.get("batch_input")
            if batch_input:
                try:
                    # Получаем текущее содержимое панели пакета
                    current_batch_text = batch_input.get("1.0", "end-1c").strip()
                    formatted_new_text = format_clipboard_text(new_text)
                    
                    # Проверка на плейсхолдер
                    is_placeholder = False
                    if hasattr(app_state, 'batch_panel') and app_state.batch_panel:
                        if current_batch_text == app_state.batch_panel.placeholder_text:
                            is_placeholder = True
                    
                    if is_placeholder:
                        batch_input.delete("1.0", "end")
                        batch_input.configure(text_color=("gray10", "gray90"))
                        batch_input.insert("1.0", formatted_new_text)
                        print(f"📋 Собиратель: плейсхолдер заменен на текст ({len(formatted_new_text)} символов)")
                    # Проверка на дубликат в самом списке пакета
                    elif current_batch_text:
                        existing_lines = [line.strip() for line in current_batch_text.split('\n')]
                        if formatted_new_text.strip() in existing_lines:
                            print(f"📋 Собиратель: дубликат проигнорирован ({formatted_new_text[:30]}...)")
                        else:
                            batch_input.insert("end", "\n" + formatted_new_text)
                            print(f"📋 Собиратель: текст добавлен в пакет ({len(formatted_new_text)} символов)")
                    else:
                        batch_input.insert("1.0", formatted_new_text)
                        print(f"📋 Собиратель: текст добавлен в пакет ({len(formatted_new_text)} символов)")
                except Exception as e:
                    print(f"Ошибка добавления в пакет: {e}")

        auto_gen_enabled = app_state.get_checkbox_value("auto_generate_var", default=False)
        if auto_gen_enabled:
            # Ограничиваем автогенерацию только короткими фразами (до 100 слов)
            word_count = len(new_text.split())
            if word_count <= 100:
                print(f"🤖 Автогенерация включена, запуск генерации")
                update_processing_indicator(animate=True)
                app_state.main_window_components["generate_function"]()
            else:
                print(f"⏩ Текст слишком длинный для автогенерации ({word_count} слов), только добавлено в список")
    except queue.Empty:
        pass
    except Exception as e:
        print(f"❌ Ошибка в process_clipboard_queue: {e}")
    finally:
        if root and root.winfo_exists():
            root.after(50, process_clipboard_queue, root)


def process_results_queue(root):
    """Обрабатывает очередь результатов"""
    from core.ui_callbacks import update_processing_indicator
    
    try:
        message, data = app_state.results_queue.get_nowait()
        widgets = app_state.main_window_components["widgets"]
        tvars = app_state.main_window_components["vars"]
        
        if message == "ollama_ok":
            app_state.generation_running = False
            translation, context = data
            widgets["translation_text"].configure(text_color=("gray10", "gray90"))
            widgets["translation_text"].delete("1.0", tk.END)
            widgets["translation_text"].insert("1.0", translation)
            
            widgets["context_widget"].configure(text_color=("gray10", "gray90"))
            widgets["context_widget"].delete("1.0", tk.END)
            widgets["context_widget"].insert("1.0", context)
            widgets["generate_btn"].configure(
                text=localization_manager.get_text("generate"), state="normal",
                fg_color="#2CC985", hover_color="#26AD72", text_color="white"
            )
            update_processing_indicator("✅ Готово", animate=False)
            root.after(2000, lambda: update_processing_indicator("", animate=False))

            # Фоновая предзагрузка аудио для мгновенного добавления
            german_phrase = widgets["german_text"].get("1.0", tk.END).strip()
            audio_enabled = tvars.get("audio_enabled_var", tk.BooleanVar(value=True)).get()
            if audio_enabled and german_phrase:
                def prefetch():
                    audio_utils.generate_audio(
                        german_phrase, app_state.tts.lang, app_state.tts.speed_level, app_state.tts.tld, debug=False
                    )
                threading.Thread(target=prefetch, daemon=True).start()
            
            auto_add_var = tvars.get("auto_add_to_anki_var")
            if auto_add_var and auto_add_var.get():
                print("🤖 Авто-добавление в Anki...")
                root.after(100, app_state.main_window_components.get("on_yes_action_func", lambda: None))
                
        elif message == "ollama_error":
            app_state.generation_running = False
            err_str = str(data)
            is_conn = err_str == "OLLAMA_CONNECT_ERROR"
            update_processing_indicator(f"❌ {'Ollama недоступен' if is_conn else 'Ошибка'}", animate=False)
            if not is_conn:
                messagebox.showerror(localization_manager.get_text("error"), err_str)
            widgets["generate_btn"].configure(
                text=localization_manager.get_text("generate"), state="normal",
                fg_color="#2CC985", hover_color="#26AD72", text_color="white"
            )
            root.after(3000, lambda: update_processing_indicator("", animate=False))
            
        elif message == "audio_ok":
            audio_path = data
            update_processing_indicator("📤 Добавление...", animate=False)
            
            raw_deck_name = tvars["deck_var"].get().strip() or DEFAULT_DECK_NAME
            deck_name = anki_api.clean_deck_name(raw_deck_name)
            
            threading.Thread(target=add_to_anki_worker, args=(
                app_state.results_queue,
                widgets["german_text"].get("1.0", tk.END).strip(),
                widgets["translation_text"].get("1.0", tk.END).strip(),
                widgets["context_widget"].get("1.0", tk.END).strip(),
                deck_name,
                audio_path, False, app_state.force_replace_flag
            ), daemon=True).start()
            
        elif message == "anki_ok":
            if data:
                app_state.force_replace_flag = False
                audio_utils.play_sound("success")
                widgets["add_btn"].configure(
                    fg_color="#2CC985", hover_color="#26AD72", text_color="white"
                )
            update_processing_indicator("✅ Готово!", animate=False)
            if "add_btn" in widgets:
                widgets["add_btn"].configure(
                    state="normal",
                    text="✅ " + localization_manager.get_text("add_to_anki")
                )
            if data:
                root.after(1500, app_state.main_window_components["on_action_complete"])
            root.after(2000, lambda: update_processing_indicator("", animate=False))

        elif message == "batch_log":
            _handle_batch_log(widgets, data)
        elif message == "batch_log_append":
            _handle_batch_log_append(widgets, data)
        elif message == "batch_progress":
            _handle_batch_progress(widgets, data)
        elif message == "batch_done":
            _handle_batch_done(widgets)

        elif message == "anki_error":
            err_str = str(data)
            update_processing_indicator("❌ Ошибка Anki", animate=False)
            messagebox.showerror(
                localization_manager.get_text("error"),
                f"Не удалось добавить в Anki:\n{err_str}", parent=root
            )
            root.after(3000, lambda: update_processing_indicator("", animate=False))
            if "add_btn" in widgets:
                widgets["add_btn"].configure(
                    state="normal",
                    text="✅ " + localization_manager.get_text("add_to_anki")
                )

        elif message == "audio_error":
            err_str = str(data)
            update_processing_indicator("❌ Ошибка аудио", animate=False)
            messagebox.showerror(
                localization_manager.get_text("error"),
                f"Не удалось сгенерировать озвучку:\n{err_str}", parent=root
            )
            root.after(3000, lambda: update_processing_indicator("", animate=False))
            if "add_btn" in widgets:
                widgets["add_btn"].configure(
                    state="normal",
                    text="✅ " + localization_manager.get_text("add_to_anki")
                )

        elif message == "anki_duplicate":
            phrase, translation, context, deck_name, audio_path, existing_ids = data
            
            # Разблокируем кнопку для выбора
            if "add_btn" in widgets:
                widgets["add_btn"].configure(state="normal", text="✅ " + localization_manager.get_text("add_to_anki"))

            if messagebox.askyesno("Дубликат обнаружен", 
                                   f"В Anki уже есть карточка с фразой:\n\"{phrase}\"\n\nУдалить старую версию и добавить новую?", 
                                   parent=root):
                update_processing_indicator("🗑 Удаление...", animate=False)
                
                def delete_and_add_worker():
                    if anki_api.delete_notes(existing_ids):
                        add_to_anki_worker(app_state.results_queue, phrase, translation, context, deck_name, audio_path, confirm_delete=True)
                    else:
                        app_state.results_queue.put(("anki_error", "Не удалось удалить старую версию карточки."))
                
                threading.Thread(target=delete_and_add_worker, daemon=True).start()
            else:
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                    except OSError:
                        pass
                update_processing_indicator("Отменено", animate=False)
                root.after(2000, lambda: update_processing_indicator("", animate=False))
                
        elif message == "models_ok":
            if data == "OLLAMA_CONNECT_ERROR":
                print("⚠️ Ollama недоступен")
                if "ai_model_label" in widgets:
                    widgets["ai_model_label"].configure(text="⚠️ Ollama недоступен", text_color="#ff5555")
            elif data:
                current_model = app_state.ollama_model or (tvars.get("ollama_var").get() if "ollama_var" in tvars else "")
                
                # Если текущая модель не в списке или не задана, выбираем первую доступную
                if not current_model or current_model not in data:
                    new_model = data[0]
                    print(f"🔄 Модель '{current_model}' не найдена. Авто-выбор: '{new_model}'")
                    
                    app_state.ollama_model = new_model
                    if "ollama_var" in tvars:
                        tvars["ollama_var"].set(new_model)
                    
                    if "ai_model_label" in widgets:
                        widgets["ai_model_label"].configure(text=f"⚡ {new_model}")
                    
                    # Сохраняем настройки, чтобы выбор применился при следующем запуске
                    try:
                        settings = load_settings(update_app_state=False)
                        settings["OLLAMA_MODEL"] = new_model
                        from core.settings_manager import save_settings
                        save_settings(settings)
                        print(f"✅ Настройки обновлены: OLLAMA_MODEL={new_model}")
                    except Exception as e:
                        print(f"⚠️ Ошибка сохранения авто-выбранной модели: {e}")
                else:
                    if "ai_model_label" in widgets:
                        widgets["ai_model_label"].configure(text=f"⚡ {current_model}")
                
                print(f"✅ Ollama модели загружены: {len(data)} шт, текущая: {app_state.ollama_model}")
                
        elif message == "decks_ok":
            var = tvars["deck_var"]
            combo = widgets["deck_combo"]
            
            if data == "ANKI_CONNECT_ERROR":
                combo.configure(values=["AnkiConnect недоступен"], state="disabled")
                var.set("AnkiConnect недоступен")
            elif data:
                combo.configure(state="normal", values=data)
                settings = load_settings(update_app_state=False)
                last_deck = settings.get("LAST_DECK", "")
                
                found = False
                if last_deck:
                    for deck in data:
                        if anki_api.clean_deck_name(deck) == last_deck:
                            var.set(deck)
                            found = True
                            break
                
                if not found and data:
                    var.set(data[0])
                            
        elif message in ["models_error", "decks_error"]:
            pass
            
    except queue.Empty:
        pass
    except Exception as e:
        print(f"❌ Ошибка в process_results_queue: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if root and root.winfo_exists():
            root.after(50, process_results_queue, root)


# =====================================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ОБРАБОТКИ СООБЩЕНИЙ
# =====================================================================================

def _handle_batch_log(widgets, data):
    """Добавляет новую строку в лог пакетной обработки."""
    if "batch_log" in widgets:
        import time
        widgets["batch_log"].configure(state="normal")
        widgets["batch_log"].insert("end", f"[{time.strftime('%H:%M:%S')}] {data}\n")
        widgets["batch_log"].see("end")
        widgets["batch_log"].configure(state="disabled")


def _handle_batch_log_append(widgets, data):
    """Дописывает текст в конец последней строки лога."""
    if "batch_log" in widgets:
        widgets["batch_log"].configure(state="normal")
        # end-2c — это конец текста перед нашим переносом строки.
        widgets["batch_log"].insert("end-2c", f" {data}")
        widgets["batch_log"].see("end")
        widgets["batch_log"].configure(state="disabled")


def _handle_batch_progress(widgets, data):
    """Обновляет прогресс пакетной обработки."""
    current, total, phrase = data
    if "batch_progress_bar" in widgets:
        widgets["batch_progress_bar"].set(current / total)
    if "batch_status_label" in widgets:
        widgets["batch_status_label"].configure(text=f"Обработка {current}/{total}: {phrase[:25]}...")


def _handle_batch_done(widgets):
    """Обрабатывает завершение пакетной обработки."""
    app_state.batch_running = False
    app_state.batch_paused = False
    
    if "batch_status_label" in widgets:
        widgets["batch_status_label"].configure(text="✅ Завершено")
    
    # Сбрасываем состояние панели через ее метод
    if hasattr(app_state, 'batch_panel') and app_state.batch_panel:
        app_state.batch_panel.reset_state()
    
    audio_utils.play_sound("success")
