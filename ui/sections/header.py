# -*- coding: utf-8 -*-
"""
Секция хедера главного окна: pin, help, language selector, batch, audio, settings.
"""
import tkinter as tk
import customtkinter as ctk
import os

from core.localization import localization_manager
from core import audio_utils
from ui.sections.popup_menu import create_popup_menu, destroy_popup


def build_header(root, main_frame, widgets, tvars, settings, dependencies, toggle_sidebar, save_all_ui_settings):
    """Создаёт хедер с кнопками управления."""
    from ui.main_window import ToolTip, show_help_window

    header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    header_frame.pack(fill="x", pady=0)
    tvars["pin_var"] = tk.BooleanVar(value=False)

    # === PIN BUTTON ===
    def toggle_pin():
        current_state = tvars["pin_var"].get()
        new_state = not current_state
        tvars["pin_var"].set(new_state)
        root.attributes("-topmost", new_state)
        if new_state:
            pin_btn.configure(text="✅", fg_color="#2cc985")
        else:
            pin_btn.configure(text="📌", fg_color="#1f538d")

    pin_btn = ctk.CTkButton(header_frame, text="📌", command=toggle_pin, width=40, height=30)
    pin_btn.pack(side="left", padx=(0, 5))
    widgets["pin_btn"] = pin_btn

    # === HELP BUTTON ===
    help_btn = ctk.CTkButton(
        header_frame, text=localization_manager.get_text("help"), width=50, height=30,
        fg_color="transparent", border_width=1,
        command=lambda: show_help_window("Главное окно", "Main_Window_Help.txt")
    )
    help_btn.pack(side="left", padx=(5, 5))
    widgets["help_btn"] = help_btn
    ToolTip(help_btn, localization_manager.get_text("help_tooltip"))

    # === LANGUAGE SELECTOR ===
    _build_language_selector(root, header_frame, widgets, dependencies)

    # === BATCH BUTTON ===
    batch_btn = ctk.CTkButton(
        header_frame, text=localization_manager.get_text("batch_btn_label"),
        width=80, height=30, fg_color="#8B4513", hover_color="#A0522D",
        corner_radius=10, command=toggle_sidebar
    )
    batch_btn.pack(side="right", padx=(5, 5))
    widgets["batch_btn"] = batch_btn
    ToolTip(batch_btn, localization_manager.get_text("batch_tooltip"))

    # === AUDIO CONTROLS ===
    tvars["sound_source_var"] = tk.StringVar(value=settings.get("SOUND_SOURCE", "original"))
    _build_audio_controls(root, header_frame, widgets, tvars, settings, dependencies, save_all_ui_settings)

    # === SETTINGS BUTTON ===
    try:
        from PIL import Image
        from core.settings_manager import get_resource_path
        settings_icon_path = get_resource_path(os.path.join("assets", "settings_v2.png"))
        settings_img = ctk.CTkImage(light_image=Image.open(settings_icon_path), dark_image=Image.open(settings_icon_path), size=(20, 20))
    except Exception as e:
        print("Error loading settings icon:", e)
        settings_img = None

    widgets["font_settings_btn"] = ctk.CTkButton(
        header_frame, text="" if settings_img else "⚙",
        image=settings_img, width=40, height=30,
        command=lambda: dependencies.open_settings_window(root, dependencies),
        fg_color="transparent", hover_color="#444444"
    )
    widgets["font_settings_btn"].pack(side="right", padx=(5, 30))
    ToolTip(widgets["font_settings_btn"], localization_manager.get_text("open_settings"))

    # === UI TEXT REFRESH (language change observer) ===
    def refresh_ui_texts(new_lang):
        """Обновляет все тексты главного окна после смены языка."""
        lang_display = {"ru": "RU", "en": "EN"}
        widgets["lang_btn"].configure(text=f"🌐 {lang_display.get(new_lang, 'RU')}")
        widgets["help_btn"].configure(text=localization_manager.get_text("help"))
        if not widgets["font_settings_btn"].cget("image"):
            widgets["font_settings_btn"].configure(text="⚙")

        if "context_check" in widgets:
            widgets["context_check"].configure(text=localization_manager.get_text("context_enabled"))
        if "pause_monitoring_check" in widgets:
            widgets["pause_monitoring_check"].configure(text=localization_manager.get_text("clipboard_monitoring"))
        if "generate_btn" in widgets:
            widgets["generate_btn"].configure(text=localization_manager.get_text("generate"))
        if "add_btn" in widgets:
            widgets["add_btn"].configure(text="✅ " + localization_manager.get_text("add_to_anki"))
        if "ai_model_label" in widgets:
            from core.app_state import app_state
            model_text = app_state.ollama_model or localization_manager.get_text("ai_not_configured")
            widgets["ai_model_label"].configure(text=f"⚡ {model_text}")

        root.title(localization_manager.get_text("app_title"))

        if "check_updates_label" in widgets:
            widgets["check_updates_label"].configure(text=localization_manager.get_text("check_updates"))
        if "batch_btn" in widgets:
            widgets["batch_btn"].configure(text=localization_manager.get_text("batch_btn_label"))

    localization_manager.add_observer(refresh_ui_texts)


def _build_language_selector(root, header_frame, widgets, dependencies):
    """Строит кнопку выбора языка с popup-меню."""
    from ui.main_window import ToolTip

    language_display = {"ru": "RU", "en": "EN"}
    current_lang_code = localization_manager.language

    lang_popup = [None]
    _lang_opening = [False]

    def show_lang_menu():
        if _lang_opening[0]:
            return
        if lang_popup[0] is not None:
            destroy_popup(lang_popup)
            return

        _lang_opening[0] = True

        def set_language(lang_code):
            destroy_popup(lang_popup)
            if lang_code != localization_manager.language:
                localization_manager.language = lang_code
                try:
                    current_settings = dependencies.load_settings()
                    current_settings["UI_LANGUAGE"] = lang_code
                    dependencies.save_settings(current_settings)
                except Exception as e:
                    print(f"⚠️ Ошибка сохранения языка: {e}")

        cur = localization_manager.language
        items = [
            {"text": "🇷🇺 Русский", "command": lambda: set_language("ru"), "active": cur == "ru"},
            {"text": "🇬🇧 English", "command": lambda: set_language("en"), "active": cur == "en"},
        ]
        create_popup_menu(root, widgets["lang_btn"], items, lang_popup)
        _lang_opening[0] = False

    lang_btn = ctk.CTkButton(
        header_frame, text=f"🌐 {language_display.get(current_lang_code, 'RU')}",
        width=55, height=30, fg_color="transparent", border_width=1,
        command=show_lang_menu
    )
    lang_btn.pack(side="left", padx=(0, 5))
    widgets["lang_btn"] = lang_btn


def _build_audio_controls(root, header_frame, widgets, tvars, settings, dependencies, save_all_ui_settings):
    """Строит кнопку воспроизведения, чекбокс аудио и popup выбора источника."""
    from ui.main_window import ToolTip

    def play_selected_audio_wrapper():
        _play_selected_audio(widgets, tvars, dependencies, root)

    # Загрузка иконок
    try:
        from PIL import Image
        from core.settings_manager import get_resource_path
        audio_active_path = get_resource_path(os.path.join("assets", "audio_active.png"))
        audio_inactive_path = get_resource_path(os.path.join("assets", "audio_inactive.png"))
        audio_active_img = ctk.CTkImage(light_image=Image.open(audio_active_path), dark_image=Image.open(audio_active_path), size=(20, 20))
        audio_inactive_img = ctk.CTkImage(light_image=Image.open(audio_inactive_path), dark_image=Image.open(audio_inactive_path), size=(20, 20))
    except Exception as e:
        print("Error loading audio icons:", e)
        audio_active_img = None
        audio_inactive_img = None

    widgets["font_sound_btn"] = ctk.CTkButton(
        header_frame, text="" if audio_active_img else "🔊",
        image=audio_active_img, width=40, height=30,
        command=play_selected_audio_wrapper,
        fg_color="transparent", hover=False
    )
    widgets["font_sound_btn"].image_active = audio_active_img
    widgets["font_sound_btn"].image_inactive = audio_inactive_img
    widgets["font_sound_btn"].pack(side="right", padx=(0, 5))
    ToolTip(widgets["font_sound_btn"], localization_manager.get_text("play_audio"))

    # Popup выбора источника аудио
    popup_menu = [None]

    def show_menu(event=None):
        if not tvars.get("audio_enabled_var", tk.BooleanVar(value=True)).get():
            return
        if popup_menu[0] is not None:
            return

        def set_source(val):
            tvars["sound_source_var"].set(val)
            save_all_ui_settings()
            destroy_popup(popup_menu)

        val = tvars["sound_source_var"].get()
        items = [
            {"text": "🇩🇪 " + localization_manager.get_text("sound_source_original"),
             "command": lambda: set_source("original"), "active": val == "original", "width": 80},
            {"text": "🇷🇺 " + localization_manager.get_text("sound_source_translation"),
             "command": lambda: set_source("translation"), "active": val == "translation", "width": 80},
        ]
        create_popup_menu(root, widgets["font_sound_btn"], items, popup_menu)

    widgets["font_sound_btn"].bind("<Enter>", show_menu)

    # Чекбокс вкл/выкл аудио
    def toggle_audio_btn_state():
        if tvars.get("audio_enabled_var") and tvars["audio_enabled_var"].get():
            widgets["font_sound_btn"].configure(image=widgets["font_sound_btn"].image_active, state="normal")
        else:
            widgets["font_sound_btn"].configure(image=widgets["font_sound_btn"].image_inactive, state="disabled")
        save_all_ui_settings()

    tvars["audio_enabled_var"] = tk.BooleanVar(value=settings.get("AUDIO_ENABLED", True))
    widgets["audio_enabled_check"] = ctk.CTkCheckBox(
        header_frame, text="", variable=tvars["audio_enabled_var"],
        width=24, command=toggle_audio_btn_state
    )
    widgets["audio_enabled_check"].pack(side="right", padx=(5, 0))
    ToolTip(widgets["audio_enabled_check"], localization_manager.get_text("audio_enabled_tooltip"))
    toggle_audio_btn_state()


def _play_selected_audio(widgets, tvars, dependencies, root):
    """Воспроизводит аудио для выбранного текста."""
    from tkinter import messagebox

    source = tvars["sound_source_var"].get()
    text_widget = widgets["translation_text"] if source == "translation" else widgets["german_text"]
    text = text_widget.get("1.0", tk.END).strip()

    if not text:
        messagebox.showwarning(
            localization_manager.get_text("warning"),
            localization_manager.get_text("empty_field_warning")
        )
        return

    # Пропускаем placeholder-тексты
    placeholder_texts = [
        localization_manager.get_text("placeholder_german"),
        localization_manager.get_text("placeholder_translation"),
    ]
    if text in placeholder_texts:
        return

    def worker():
        try:
            lang = getattr(dependencies, "TTS_LANG", "de")
            tld = getattr(dependencies, "TTS_TLD", "de")
            speed_level = getattr(dependencies, "TTS_SPEED_LEVEL", 0)
            audio_utils.play_text_audio(text, lang, speed_level, tld, parent=root)
        except Exception as e:
            messagebox.showerror(
                localization_manager.get_text("error"),
                f"Не удалось воспроизвести аудио: {e}"
            )

    dependencies.threading.Thread(target=worker, daemon=True).start()
