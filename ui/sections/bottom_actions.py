# -*- coding: utf-8 -*-
"""
Секция нижних действий: добавление в Anki, горячие клавиши, финальная настройка.
"""
import sys
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from core.localization import localization_manager
from core.clipboard_manager import GlobalClipboardManager


def build_bottom_actions(root, main_frame, widgets, tvars, settings, dependencies,
                         save_all_ui_settings, placeholders, last_prompt, on_prompt_select_fn):
    """Создаёт нижнюю панель действий и выполняет финальную настройку окна.
    
    Args:
        placeholders: dict из build_input_fields
        last_prompt: str — последний использованный промпт
        on_prompt_select_fn: callable — функция обработки выбора промпта
    """
    from ui.main_window import ToolTip
    from core.app_state import app_state
    main_window_components = app_state.main_window_components

    # ========================================
    # ACTION FRAME
    # ========================================
    action_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    action_frame.pack(fill="x", pady=10, padx=5)

    status_left_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
    status_left_frame.pack(side="left", padx=5)

    widgets["processing_indicator"] = ctk.CTkLabel(
        status_left_frame, text="", font=("Roboto", 10),
        text_color=("#5a9fd4", "#5a9fd4")
    )
    widgets["processing_indicator"].pack(side="left", padx=(0, 10))

    widgets["prompt_status_label"] = ctk.CTkLabel(
        status_left_frame, text="", font=("Roboto", 10),
        text_color=("#888888", "#888888")
    )
    widgets["prompt_status_label"].pack(side="left", padx=0)

    # === ADD TO ANKI ===
    add_to_anki_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
    add_to_anki_frame.pack(side="right", padx=5)

    auto_add_label = ctk.CTkLabel(
        add_to_anki_frame, text=localization_manager.get_text("auto_add"),
        font=("Roboto", 12)
    )
    auto_add_label.pack(side="left", padx=(0, 2))

    tvars["auto_add_to_anki_var"] = tk.BooleanVar(value=settings.get("AUTO_ADD_TO_ANKI", False))
    widgets["auto_add_to_anki_check"] = ctk.CTkCheckBox(
        add_to_anki_frame, text="", variable=tvars["auto_add_to_anki_var"],
        width=20, command=save_all_ui_settings
    )
    widgets["auto_add_to_anki_check"].pack(side="left", padx=(0, 5))
    ToolTip(widgets["auto_add_to_anki_check"], localization_manager.get_text("auto_add_tooltip"))

    widgets["add_btn"] = ctk.CTkButton(
        add_to_anki_frame,
        text="✅ " + localization_manager.get_text("add_to_anki"),
        command=dependencies.on_yes_action,
        width=100, fg_color="#2CC985", hover_color="#26AD72"
    )
    widgets["add_btn"].pack(side="left")

    # ========================================
    # FINAL SETUP
    # ========================================
    def on_action_complete():
        last_phrase = main_window_components.get("original_phrase", "")
        try:
            import pyperclip
            pyperclip.copy(last_phrase)
        except ImportError:
            pass

    main_window_components["on_action_complete"] = on_action_complete

    def on_close():
        from core.settings_manager import load_settings, save_settings
        dependencies.stop_clipboard_monitoring()
        current_settings = load_settings(update_app_state=False)

        raw_deck = tvars["deck_var"].get()
        current_settings["LAST_DECK"] = dependencies.clean_deck_name(raw_deck) if hasattr(dependencies, 'clean_deck_name') else raw_deck
        current_settings["OLLAMA_MODEL"] = app_state.ollama_model
        current_settings["CONTEXT_ENABLED"] = tvars["context_var"].get()
        current_settings["AUTO_GENERATE_ON_COPY"] = tvars["auto_generate_var"].get()
        current_settings["PAUSE_CLIPBOARD_MONITORING"] = not tvars["pause_monitoring_var"].get()
        current_settings["SOUND_SOURCE"] = tvars["sound_source_var"].get()
        current_settings["LAST_PROMPT"] = tvars["prompt_var"].get()
        current_settings["AUDIO_ENABLED"] = tvars["audio_enabled_var"].get()
        current_settings["AUTO_ADD_TO_ANKI"] = tvars["auto_add_to_anki_var"].get()

        save_settings(current_settings)
        print("🛑 Остановка мониторинга буфера обмена и завершение приложения.")
        root.destroy()
        sys.exit(0)

    root.protocol("WM_DELETE_WINDOW", on_close)

    # ========================================
    # DEFERRED LOAD
    # ========================================
    def deferred_load():
        from core.prompts_manager import prompts_manager
        try:
            prompt_names = prompts_manager.get_preset_names()
            widgets["prompt_combo"].configure(values=prompt_names)
            if last_prompt and last_prompt in prompt_names:
                tvars["prompt_var"].set(last_prompt)
                if "prompt_status_label" in widgets:
                    widgets["prompt_status_label"].configure(
                        text=localization_manager.get_text("prompt_label", name=last_prompt)
                    )
                on_prompt_select_fn(last_prompt)
        except Exception as e:
            print(f"Ошибка обновления промптов: {e}")

        if tvars["pause_monitoring_var"].get():
            root.animation_label.pack(expand=True)
            root._animation_running = True
            root.start_animation()
        else:
            root.animation_label.pack(expand=True)
            root.animation_label.configure(text="")

        dependencies.threading.Thread(
            target=dependencies.load_background_data_worker,
            args=(dependencies.results_queue,), daemon=True
        ).start()

    # ========================================
    # ANIMATION
    # ========================================
    def start_animation():
        """Запускает анимацию заголовка с точками"""
        if not hasattr(root, '_animation_running'):
            root._animation_running = False

        if not root._animation_running:
            return

        dots = ["", ".", "..", "..."]
        if not hasattr(root, '_animation_index'):
            root._animation_index = 0

        root.animation_label.configure(
            text=f"{localization_manager.get_text('clipboard_indicator')}{dots[root._animation_index]}"
        )
        root._animation_index = (root._animation_index + 1) % len(dots)
        root._animation_job = root.after(500, start_animation)

    root.start_animation = start_animation
    root.after(100, deferred_load)

    # ========================================
    # GLOBAL HOTKEYS
    # ========================================
    def on_ctrl_enter(event=None):
        dependencies.generate_action()
        return "break"

    def on_ctrl_s(event=None):
        dependencies.on_yes_action()
        return "break"

    root.bind("<Control-Return>", on_ctrl_enter)
    root.bind("<Control-s>", on_ctrl_s)
    root.bind("<Control-S>", on_ctrl_s)

    GlobalClipboardManager(root, widgets["clipboard_handlers"])
