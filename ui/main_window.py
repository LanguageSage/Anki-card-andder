# -*- coding: utf-8 -*-
"""
Главное окно приложения Anki German Helper.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import time
import os
import json
import sys

from core import audio_utils
from ui.theme_manager import theme_manager
from core.clipboard_manager import setup_text_widget_context_menu, GlobalClipboardManager
from core.localization import localization_manager
from modules.batch_generator.ui import create_batch_panel


class ToolTip:
    """Класс для создания всплывающих подсказок"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
    
    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        frame = tk.Frame(self.tooltip_window, background="#2b2b2b", relief="solid", borderwidth=1)
        frame.pack()
        label = tk.Label(frame, text=self.text, justify="left",
                        background="#2b2b2b", fg="#ffffff", relief="solid", borderwidth=0,
                        font=("Arial", 10), padx=5, pady=3)
        label.pack()
    
    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def ask_string_dialog(parent, title, prompt, initial_value=""):
    """Универсальная функция для ввода текста с поддержкой буфера обмена
    Возвращает введенный текст или None если отменено
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title(title)
    dialog.geometry("450x180")
    dialog.transient(parent)
    dialog.grab_set()
    # dialog.attributes("-topmost", True)
    dialog.focus_force()
    
    result = [None]
    
    ctk.CTkLabel(dialog, text=prompt, font=("Roboto", 15)).pack(pady=(20, 10), padx=20)
    
    entry = ctk.CTkEntry(dialog, font=("Roboto", 15), height=35)
    entry.pack(pady=10, padx=20, fill="x")
    if initial_value:
        entry.insert(0, initial_value)
        entry.select_range(0, tk.END)
    entry.focus_set()
    
    setup_text_widget_context_menu(entry)
    
    def on_ok():
        if entry.get().strip():
            result[0] = entry.get().strip()
            dialog.destroy()
    
    entry.bind("<Return>", lambda e: on_ok())
    dialog.bind("<Escape>", lambda e: dialog.destroy())
    
    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(pady=15, padx=20, fill="x")
    ctk.CTkButton(btn_frame, text=localization_manager.get_text("ok"), command=on_ok, font=("Roboto", 13), 
                  width=100, height=35, fg_color="#2CC985", hover_color="#26AD72").pack(side="left", padx=10, expand=True)
    ctk.CTkButton(btn_frame, text=localization_manager.get_text("cancel"), command=dialog.destroy, font=("Roboto", 13),
                  width=100, height=35, fg_color="#FF5555", hover_color="#D63C3C").pack(side="right", padx=10, expand=True)
    
    dialog.wait_window()
    return result[0]


def show_help_window(title, file_name):
    """Открывает страницу справки в браузере"""
    try:
        import webbrowser
        
        # Базовый URL документации
        base_url = "https://LanguageSage.github.io/Anki-card-andder/help.html"
        
        # Определяем якорь (anchor) на основе имени запрашиваемого файла
        anchor = ""
        file_name_lower = file_name.lower()
        if "audio" in file_name_lower or "tts" in file_name_lower:
            anchor = "#audio"
        elif "ai" in file_name_lower:
            anchor = "#ai"
        elif "anki" in file_name_lower:
            anchor = "#anki"
        elif "main" in file_name_lower:
            anchor = "#main"
        elif "prompts" in file_name_lower or "промпт" in file_name_lower:
            anchor = "#prompts"
            
        # Формируем полный URL
        url = f"{base_url}{anchor}"
        
        # Открываем в браузере
        webbrowser.open(url)
        
    except Exception as e:
        messagebox.showerror(localization_manager.get_text("error"), f"Не удалось открыть справку: {e}")


def populate_main_window(dependencies, root, settings, main_frame, widgets, tvars, master_container=None):
    """
    Заполняет основное окно виджетами.
    """
    from core.app_state import app_state
    main_window_components = app_state.main_window_components
    last_prompt = settings.get("LAST_PROMPT", "")

    def save_all_ui_settings(event=None):
        """Универсальная функция для мгновенного сохранения всех настроек UI"""
        try:
            current_settings = dependencies.load_settings()

            # Собираем данные из всех виджетов
            if "deck_var" in tvars:
                raw_deck = tvars["deck_var"].get()
                clean_deck = dependencies.clean_deck_name(raw_deck) if hasattr(dependencies, 'clean_deck_name') else raw_deck
                current_settings["LAST_DECK"] = clean_deck
            
            if hasattr(app_state, 'ollama_model'):
                current_settings["OLLAMA_MODEL"] = app_state.ollama_model

            if "context_var" in tvars:
                current_settings["CONTEXT_ENABLED"] = tvars["context_var"].get()
            if "auto_generate_var" in tvars:
                current_settings["AUTO_GENERATE_ON_COPY"] = tvars["auto_generate_var"].get()
            if "pause_monitoring_var" in tvars:
                current_settings["PAUSE_CLIPBOARD_MONITORING"] = not tvars["pause_monitoring_var"].get()
            if "sound_source_var" in tvars:
                current_settings["SOUND_SOURCE"] = tvars["sound_source_var"].get()
            if "prompt_var" in tvars:
                current_settings["LAST_PROMPT"] = tvars["prompt_var"].get()
            if "audio_enabled_var" in tvars:
                current_settings["AUDIO_ENABLED"] = tvars["audio_enabled_var"].get()
            if "auto_add_to_anki_var" in tvars:
                current_settings["AUTO_ADD_TO_ANKI"] = tvars["auto_add_to_anki_var"].get()

            dependencies.save_settings(current_settings)
        except Exception as e:
            print(f"Ошибка фонового сохранения настроек: {e}")

    # ========================================
    # SIDEBAR LOGIC
    # ========================================
    right_panel = [None]
    sidebar_visible = [False]

    # Изначально (при старте) у нас только одна колонка на всю ширину
    if master_container:
        master_container.grid_columnconfigure(0, weight=1, uniform="")
        master_container.grid_columnconfigure(1, weight=0, uniform="") 
        master_container.grid_rowconfigure(0, weight=1)

    # Меняем pack на grid для левой панели
    main_frame.pack_forget() 
    main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def toggle_sidebar():
        if not master_container:
            return
            
        if not sidebar_visible[0]:
            # === РЕЖИМ: ДВЕ ПАНЕЛИ (ПОКАЗАТЬ) ===
            master_container.grid_columnconfigure(0, weight=1, uniform="group1")
            master_container.grid_columnconfigure(1, weight=1, uniform="group1")
            
            main_frame.grid_configure(padx=(10, 5))
            
            if right_panel[0] is None:
                # Создаем панель пакетной обработки
                right_panel[0] = create_batch_panel(
                    master_container, 
                    dependencies.start_batch_processing,
                    dependencies.stop_batch_processing
                )
            
            # Показываем правую панель
            right_panel[0].grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
            
            root.geometry("1000x750")
            sidebar_visible[0] = True
        else:
            # === РЕЖИМ: ОДНА ПАНЕЛЬ (СКРЫТЬ) ===
            main_frame.grid_configure(padx=10)
            
            if right_panel[0]:
                right_panel[0].grid_forget()
            
            master_container.grid_columnconfigure(0, weight=1, uniform="")
            master_container.grid_columnconfigure(1, weight=0, uniform="")
            
            root.geometry("500x750")
            sidebar_visible[0] = False

    # ========================================
    # HEADER
    # ========================================
    header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    header_frame.pack(fill="x", pady=0)
    tvars["pin_var"] = tk.BooleanVar(value=False)
    
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

    # Кнопка Help в хедере (перемещена влево от пакета)
    help_btn = ctk.CTkButton(header_frame, text=localization_manager.get_text("help"), width=50, height=30, 
                             fg_color="transparent", border_width=1, 
                             command=lambda: show_help_window("Главное окно", "Main_Window_Help.txt"))
    help_btn.pack(side="left", padx=(5, 5))
    widgets["help_btn"] = help_btn
    ToolTip(help_btn, localization_manager.get_text("help_tooltip"))

    # === LANGUAGE SELECTOR (выпадающий список по клику, справа от Help) ===
    language_display = {"ru": "RU", "en": "EN"}
    current_lang_code = localization_manager.language
    
    lang_popup = [None]
    _lang_opening = [False]
    
    def show_lang_menu():
        if _lang_opening[0]:
            return
        if lang_popup[0] is not None:
            hide_lang_menu()
            return
        
        _lang_opening[0] = True
        
        p = tk.Toplevel(root)
        p.wm_overrideredirect(True)
        p.attributes("-topmost", True)
        p.configure(bg="#2b2b2b")
        
        btn = widgets["lang_btn"]
        x = btn.winfo_rootx()
        y = btn.winfo_rooty() + btn.winfo_height() + 2
        p.geometry(f"+{x}+{y}")
        
        f = ctk.CTkFrame(p, fg_color="#333333", border_width=1, border_color="#555555", corner_radius=4)
        f.pack(fill="both", expand=True)
        
        def set_language(lang_code):
            hide_lang_menu()
            if lang_code != localization_manager.language:
                localization_manager.language = lang_code
                try:
                    current_settings = dependencies.load_settings()
                    current_settings["UI_LANGUAGE"] = lang_code
                    dependencies.save_settings(current_settings)
                except Exception as e:
                    print(f"⚠️ Ошибка сохранения языка: {e}")
        
        cur = localization_manager.language
        b_ru = ctk.CTkButton(f, text="🇷🇺 Русский", width=100, height=28, 
                             fg_color="transparent", hover_color="#444444",
                             text_color="#2cc985" if cur == "ru" else "white", anchor="w",
                             command=lambda: set_language("ru"))
        b_ru.pack(pady=(2, 0), padx=2)
        
        b_en = ctk.CTkButton(f, text="🇬🇧 English", width=100, height=28, 
                             fg_color="transparent", hover_color="#444444",
                             text_color="#2cc985" if cur == "en" else "white", anchor="w",
                             command=lambda: set_language("en"))
        b_en.pack(pady=(0, 2), padx=2)
        
        lang_popup[0] = p
        _lang_opening[0] = False
        
        def check_leave():
            if lang_popup[0] is None:
                return
            try:
                rx, ry = p.winfo_pointerxy()
                bx, by = btn.winfo_rootx(), btn.winfo_rooty()
                bw, bh = btn.winfo_width(), btn.winfo_height()
                px, py = p.winfo_rootx(), p.winfo_rooty()
                pw, ph = p.winfo_width(), p.winfo_height()
                
                in_btn = (bx-5 <= rx <= bx+bw+5) and (by-5 <= ry <= by+bh+5)
                in_pop = (px-5 <= rx <= px+pw+5) and (py-5 <= ry <= py+ph+5)
                
                if not (in_btn or in_pop):
                    hide_lang_menu()
                else:
                    p.after(100, check_leave)
            except tk.TclError:
                lang_popup[0] = None
        
        p.after(500, check_leave)
    
    def hide_lang_menu():
        if lang_popup[0]:
            try:
                lang_popup[0].destroy()
            except Exception:
                pass
            lang_popup[0] = None
    
    lang_btn = ctk.CTkButton(header_frame, text=f"🌐 {language_display.get(current_lang_code, 'RU')}", 
                             width=55, height=30,
                             fg_color="transparent", border_width=1,
                             command=show_lang_menu)
    lang_btn.pack(side="left", padx=(0, 5))
    widgets["lang_btn"] = lang_btn
    
    # === Функция обновления текстов UI при смене языка ===
    def refresh_ui_texts(new_lang):
        """Обновляет все тексты главного окна после смены языка."""
        # Обновить кнопку языка
        lang_display = {"ru": "RU", "en": "EN"}
        widgets["lang_btn"].configure(text=f"🌐 {lang_display.get(new_lang, 'RU')}")
        
        # Кнопка Help
        widgets["help_btn"].configure(text=localization_manager.get_text("help"))
        
        # Настройки
        widgets["font_settings_btn"].configure(text="⚙")
        
        # Чекбоксы и лейблы
        if "context_check" in widgets:
            widgets["context_check"].configure(text=localization_manager.get_text("context_enabled"))
        if "pause_monitoring_check" in widgets:
            widgets["pause_monitoring_check"].configure(text=localization_manager.get_text("clipboard_monitoring"))
        
        # Генерация
        if "generate_btn" in widgets:
            widgets["generate_btn"].configure(text=localization_manager.get_text("generate"))
        
        # Кнопки действий
        if "add_btn" in widgets:
            widgets["add_btn"].configure(text="✅ " + localization_manager.get_text("add_to_anki"))
        
        # AI модель
        if "ai_model_label" in widgets:
            from core.app_state import app_state
            model_text = app_state.ollama_model or localization_manager.get_text("ai_not_configured")
            widgets["ai_model_label"].configure(text=f"⚡ {model_text}")
        
        # Заголовок окна
        root.title(localization_manager.get_text("app_title"))
        
        # Ссылка обновления
        if "check_updates_label" in widgets:
            widgets["check_updates_label"].configure(text=localization_manager.get_text("check_updates"))
        
        # Кнопка Пакет
        if "batch_btn" in widgets:
            widgets["batch_btn"].configure(text=localization_manager.get_text("batch_btn_label"))
    
    localization_manager.add_observer(refresh_ui_texts)

    # Кнопка Пакет в правой части хедера (как было раньше)
    # Используем закругления с одной стороны (15, 0, 0, 15) для обратного эффекта "стрелки"
    batch_btn = ctk.CTkButton(header_frame, text=localization_manager.get_text("batch_btn_label"), width=80, height=30, 
                             fg_color="#8B4513", hover_color="#A0522D",
                             corner_radius=10,
                             command=toggle_sidebar)
    batch_btn.pack(side="right", padx=(5, 5))
    widgets["batch_btn"] = batch_btn
    ToolTip(batch_btn, localization_manager.get_text("batch_tooltip"))
    
    sound_source = settings.get("SOUND_SOURCE", "original")
    tvars["sound_source_var"] = tk.StringVar(value=sound_source)
    
    widgets["font_settings_btn"] = ctk.CTkButton(header_frame, text="⚙", width=40, height=30, command=lambda: dependencies.open_settings_window(root, dependencies))
    widgets["font_settings_btn"].pack(side="right", padx=(5, 0))
    ToolTip(widgets["font_settings_btn"], localization_manager.get_text("open_settings"))
    
    def play_selected_audio_wrapper():
        play_selected_audio(widgets, tvars, dependencies, root)
    
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

    widgets["font_sound_btn"] = ctk.CTkButton(header_frame, text="" if audio_active_img else "🔊", 
                                              image=audio_active_img, width=40, height=30, 
                                              command=play_selected_audio_wrapper, 
                                              fg_color="transparent", hover=False)
    
    # Store references to prevent garbage collection
    widgets["font_sound_btn"].image_active = audio_active_img
    widgets["font_sound_btn"].image_inactive = audio_inactive_img

    widgets["font_sound_btn"].pack(side="right", padx=5)
    ToolTip(widgets["font_sound_btn"], localization_manager.get_text("play_audio"))

    popup_menu = [None]

    def show_menu(event=None):
        if not tvars.get("audio_enabled_var", tk.BooleanVar(value=True)).get():
            return
        if popup_menu[0] is not None:
            return
            
        p = tk.Toplevel(root)
        p.wm_overrideredirect(True)
        p.attributes("-topmost", True)
        p.configure(bg="#2b2b2b")
        
        btn = widgets["font_sound_btn"]
        x = btn.winfo_rootx()
        y = btn.winfo_rooty() + btn.winfo_height() + 2
        p.geometry(f"+{x}+{y}")
        
        f = ctk.CTkFrame(p, fg_color="#333333", border_width=1, border_color="#555555", corner_radius=4)
        f.pack(fill="both", expand=True)
        
        def set_source(val):
            tvars["sound_source_var"].set(val)
            save_all_ui_settings()
            hide_menu()
            
        val = tvars["sound_source_var"].get()
        b1 = ctk.CTkButton(f, text="🇩🇪 " + localization_manager.get_text("sound_source_original"), width=80, height=28, fg_color="transparent", hover_color="#444444",
                           text_color="#2cc985" if val == "original" else "white", anchor="w",
                           command=lambda: set_source("original"))
        b1.pack(pady=(2, 0), padx=2)
        
        b2 = ctk.CTkButton(f, text="🇷🇺 " + localization_manager.get_text("sound_source_translation"), width=80, height=28, fg_color="transparent", hover_color="#444444",
                           text_color="#2cc985" if val == "translation" else "white", anchor="w",
                           command=lambda: set_source("translation"))
        b2.pack(pady=(0, 2), padx=2)
        
        popup_menu[0] = p
        
        def check_leave():
            if popup_menu[0] is None: return
            rx, ry = p.winfo_pointerxy()
            bx, by = btn.winfo_rootx(), btn.winfo_rooty()
            bw, bh = btn.winfo_width(), btn.winfo_height()
            px, py = p.winfo_rootx(), p.winfo_rooty()
            pw, ph = p.winfo_width(), p.winfo_height()
            
            in_btn = (bx-5 <= rx <= bx+bw+5) and (by-5 <= ry <= by+bh+5)
            in_pop = (px-5 <= rx <= px+pw+5) and (py-5 <= ry <= py+ph+5)
            
            if not (in_btn or in_pop):
                hide_menu()
            else:
                p.after(100, check_leave)
        
        p.after(100, check_leave)

    def hide_menu():
        if popup_menu[0]:
            popup_menu[0].destroy()
            popup_menu[0] = None

    widgets["font_sound_btn"].bind("<Enter>", show_menu)
    
    def toggle_audio_btn_state():
        if tvars.get("audio_enabled_var") and tvars["audio_enabled_var"].get():
            widgets["font_sound_btn"].configure(image=widgets["font_sound_btn"].image_active, state="normal")
        else:
            widgets["font_sound_btn"].configure(image=widgets["font_sound_btn"].image_inactive, state="disabled")
        save_all_ui_settings()

    tvars["audio_enabled_var"] = tk.BooleanVar(value=settings.get("AUDIO_ENABLED", True))
    widgets["audio_enabled_check"] = ctk.CTkCheckBox(header_frame, text="", variable=tvars["audio_enabled_var"], width=24, command=toggle_audio_btn_state)
    widgets["audio_enabled_check"].pack(side="right", padx=5)
    ToolTip(widgets["audio_enabled_check"], localization_manager.get_text("audio_enabled_tooltip"))
    toggle_audio_btn_state()

    # ========================================
    # INPUT FIELDS
    # ========================================
    # Используем списки для мутабельности при смене языка
    placeholders = {
        "german": [localization_manager.get_text("placeholder_german")],
        "translation": [localization_manager.get_text("placeholder_translation")],
        "context": [localization_manager.get_text("placeholder_context")],
    }

    widgets["german_text"] = ctk.CTkTextbox(main_frame, height=70, font=("Roboto", 14), text_color="gray")
    widgets["german_text"].insert("1.0", placeholders["german"][0])
    widgets["german_text"].pack(pady=(0, 5), padx=5, fill="both", expand=True)
    
    widgets["translation_text"] = ctk.CTkTextbox(main_frame, height=70, font=("Roboto", 14), text_color="gray")
    widgets["translation_text"].insert("1.0", placeholders["translation"][0])
    widgets["translation_text"].pack(pady=(0, 5), padx=5, fill="both", expand=True)
    
    widgets["context_widget"] = ctk.CTkTextbox(main_frame, height=180, font=("Roboto", 12), text_color="gray")
    widgets["context_widget"].insert("1.0", placeholders["context"][0])
    widgets["context_widget"].pack(pady=(0, 5), padx=5, fill="both", expand=True)

    def setup_placeholder(widget, placeholder_holder):
        """placeholder_holder — list с одним элементом [текст], мутабельный."""
        def on_focus_in(event):
            if widget.get("1.0", "end-1c").strip() == placeholder_holder[0]:
                widget.delete("1.0", "end")
                widget.configure(text_color=("gray10", "gray90"))
        
        def on_focus_out(event):
            if not widget.get("1.0", "end-1c").strip():
                widget.insert("1.0", placeholder_holder[0])
                widget.configure(text_color="gray")
        
        widget.bind("<FocusIn>", on_focus_in)
        widget.bind("<FocusOut>", on_focus_out)

    setup_placeholder(widgets["german_text"], placeholders["german"])
    setup_placeholder(widgets["translation_text"], placeholders["translation"])
    setup_placeholder(widgets["context_widget"], placeholders["context"])

    def _update_placeholders(new_lang):
        """Обновляет placeholder-тексты при смене языка."""
        widget_map = {
            "german": ("german_text", "placeholder_german"),
            "translation": ("translation_text", "placeholder_translation"),
            "context": ("context_widget", "placeholder_context"),
        }
        for key, (widget_name, loc_key) in widget_map.items():
            old_ph = placeholders[key][0]
            new_ph = localization_manager.get_text(loc_key)
            placeholders[key][0] = new_ph
            # Если виджет сейчас показывает старый placeholder, заменить
            w = widgets.get(widget_name)
            if w and w.get("1.0", "end-1c").strip() == old_ph:
                w.delete("1.0", "end")
                w.insert("1.0", new_ph)
    
    localization_manager.add_observer(_update_placeholders)

    widgets["clipboard_handlers"] = []
    widgets["clipboard_handlers"].append(setup_text_widget_context_menu(widgets["german_text"]))
    widgets["clipboard_handlers"].append(setup_text_widget_context_menu(widgets["translation_text"]))
    widgets["clipboard_handlers"].append(setup_text_widget_context_menu(widgets["context_widget"]))
    
    # ========================================
    # CONTROLS
    # ========================================
    controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    controls_frame.pack(fill="x", pady=5, padx=5)
    tvars["prompt_var"] = tk.StringVar(value="")
    widgets["prompt_combo"] = ctk.CTkComboBox(controls_frame, variable=tvars["prompt_var"], values=[""], width=200)
    widgets["prompt_combo"].pack(side="left", padx=(0, 10))
    
    # Индикатор буфера перенесен сюда
    animation_label = ctk.CTkLabel(controls_frame, text="", font=("Roboto", 12), anchor="w")
    animation_label.pack(side="left", padx=5)
    root.animation_label = animation_label

    import webbrowser
    check_updates_label = ctk.CTkLabel(
        controls_frame,
        text=localization_manager.get_text("check_updates"),
        font=("Roboto", 11, "underline"),
        text_color=("#5a9fd4", "#5a9fd4"),
        cursor="hand2"
    )
    check_updates_label.pack(side="right", padx=5)
    widgets["check_updates_label"] = check_updates_label
    check_updates_label.bind("<Button-1>", lambda e: webbrowser.open("https://LanguageSage.github.io/Anki-card-andder/"))
    
    def on_prompt_select(choice):
        """Применяет выбранный промпт к приложению"""
        if not choice or choice.strip() == "":
            return
        try:
            from core.prompts_manager import prompts_manager
            preset = prompts_manager.get_preset(choice)
            if preset:
                new_translate = preset.get("translate", preset.get("translation", ""))
                new_context = preset.get("context", "")
                new_delimiter = preset.get("delimiter", "КОНТЕКСТ")
                
                if hasattr(dependencies, "update_active_prompts"):
                    dependencies.update_active_prompts(new_translate, new_context, new_delimiter)
                
                if "prompt_status_label" in widgets:
                    widgets["prompt_status_label"].configure(text=f"✅ {choice}", text_color="#2CC985")
                    root.after(1500, lambda: widgets["prompt_status_label"].configure(
                        text=f"Промпт: {choice}", text_color=("#888888", "#888888")))
                
                from core.settings_manager import load_settings, save_settings
                current_settings = load_settings(update_app_state=False)
                current_settings["TRANSLATE_PROMPT"] = new_translate
                current_settings["CONTEXT_PROMPT"] = new_context
                current_settings["CONTEXT_DELIMITER"] = new_delimiter
                current_settings["LAST_PROMPT"] = choice
                save_settings(current_settings)
                
                print(f"✅ Промпт '{choice}' применён (разделитель: {new_delimiter})")
            else:
                print(f"⚠️ Промпт '{choice}' не найден")
        except Exception as e:
            print(f"Ошибка применения промпта: {e}")
            import traceback
            traceback.print_exc()
    
    widgets["prompt_combo"].configure(command=on_prompt_select)
    ToolTip(widgets["prompt_combo"], localization_manager.get_text("prompt_saved", name=""))

    # ========================================
    # GENERATION CONTROLS
    # ========================================
    gen_frame = ctk.CTkFrame(main_frame)
    gen_frame.pack(fill="x", pady=5, padx=5)
    checks_frame = ctk.CTkFrame(gen_frame, fg_color="transparent")
    checks_frame.pack(side="left", padx=5, pady=5)
    tvars["context_var"] = tk.BooleanVar(value=settings.get("CONTEXT_ENABLED", False))
    widgets["context_check"] = ctk.CTkCheckBox(checks_frame, text=localization_manager.get_text("context_enabled"), variable=tvars["context_var"], command=save_all_ui_settings)
    widgets["context_check"].pack(anchor="w", pady=2)
    ToolTip(widgets["context_check"], localization_manager.get_text("context_enabled_tooltip"))
    
    pause_setting = settings.get("PAUSE_CLIPBOARD_MONITORING", True)
    tvars["pause_monitoring_var"] = tk.BooleanVar(value=not pause_setting)
    tvars["pause_monitoring_var"].trace_add("write", dependencies.update_pause_monitoring_flag)
    widgets["pause_monitoring_check"] = ctk.CTkCheckBox(checks_frame, text=localization_manager.get_text("clipboard_monitoring"), variable=tvars["pause_monitoring_var"])
    widgets["pause_monitoring_check"].pack(anchor="w", pady=2)
    ToolTip(widgets["pause_monitoring_check"], localization_manager.get_text("clipboard_monitoring_tooltip"))
    dependencies.update_pause_monitoring_flag()
    
    btns_frame = ctk.CTkFrame(gen_frame, fg_color="transparent")
    btns_frame.pack(side="left", fill="both", expand=True, padx=10)
    
    top_gen_row = ctk.CTkFrame(btns_frame, fg_color="transparent")
    top_gen_row.pack(fill="x", pady=(0, 5))
    
    auto_label = ctk.CTkLabel(top_gen_row, text=localization_manager.get_text("auto_generate"), font=("Roboto", 12))
    auto_label.pack(side="left", padx=(0, 2))
    
    def on_auto_generate_toggle():
        if tvars.get("collector_mode_var") and tvars["collector_mode_var"].get():
            messagebox.showwarning(
                "Режим Собирателя", 
                "Нельзя включить автогенерацию при активном режиме собирателя.\nСначала выключите '📋 Собиратель' в правой панели."
            )
            tvars["auto_generate_var"].set(False)
            return
        dependencies.update_auto_generate_flag()
        save_all_ui_settings()

    tvars["auto_generate_var"] = tk.BooleanVar(value=settings.get("AUTO_GENERATE_ON_COPY", True))
    widgets["auto_generate_check"] = ctk.CTkCheckBox(top_gen_row, text="", variable=tvars["auto_generate_var"], width=20, command=on_auto_generate_toggle)
    widgets["auto_generate_check"].pack(side="left", padx=(0, 5))
    ToolTip(widgets["auto_generate_check"], localization_manager.get_text("auto_generate_tooltip"))
    dependencies.update_auto_generate_flag()
    
    widgets["generate_btn"] = ctk.CTkButton(top_gen_row, text=localization_manager.get_text("generate"), command=dependencies.generate_action, height=40, width=130)
    widgets["generate_btn"].pack(side="left", fill="x", expand=True)
    
    # Индикатор текущей AI модели (кликабельный для быстрого доступа к настройкам AI)
    ai_indicator_frame = ctk.CTkFrame(gen_frame)
    ai_indicator_frame.pack(side="right", padx=5, pady=5)
    
    # Логотип Wordy (перемещен из хедера)
    try:
        from PIL import Image
        from core.settings_manager import get_resource_path
        logo_path = get_resource_path(os.path.join("assets", "logo.png"))
        if os.path.exists(logo_path):
            img = Image.open(logo_path)
            aspect_ratio = img.width / img.height
            new_width = int(25 * aspect_ratio)
            # Изменили размер на чуть поменьше (25), так как он в нижнем блоке
            logo_image = ctk.CTkImage(light_image=img, dark_image=img, size=(new_width, 25))
            logo_label = ctk.CTkLabel(ai_indicator_frame, text="", image=logo_image)
            logo_label.pack(side="top", pady=(0, 2))
            widgets["logo_label"] = logo_label
    except Exception as e:
        print(f"Ошибка загрузки логотипа: {e}")
    
    # Скрытая переменная для модели (используется при генерации)
    tvars["ollama_var"] = tk.StringVar(value=settings.get("OLLAMA_MODEL", ""))
    
    ai_model_label = ctk.CTkLabel(
        ai_indicator_frame, 
        text=f"⚡ {settings.get('OLLAMA_MODEL', localization_manager.get_text('ai_not_configured'))}", 
        text_color=("#666666", "#aaaaaa"),
        font=("Roboto", 11),
        cursor="hand2"
    )
    ai_model_label.pack(side="top", pady=(0, 0))
    widgets["ai_model_label"] = ai_model_label
    
    def open_ai_settings():
        dependencies.open_settings_window(root, dependencies, initial_tab="AI")
    
    ai_model_label.bind("<Button-1>", lambda e: open_ai_settings())
    ToolTip(ai_model_label, localization_manager.get_text("ai_settings_btn_tooltip"))

    
    # ========================================
    # DECK SELECTION
    # ========================================
    deck_frame = ctk.CTkFrame(main_frame)
    deck_frame.pack(fill="x", pady=5, padx=5)
    cached_decks = [dependencies.DEFAULT_DECK_NAME]
    tvars["deck_var"] = tk.StringVar(value=settings.get("LAST_DECK", cached_decks[0]))
    initial_deck_values = [settings["LAST_DECK"]] if settings.get("LAST_DECK") else [localization_manager.get_text("loading")]
    widgets["deck_combo"] = ctk.CTkComboBox(deck_frame, variable=tvars["deck_var"], values=initial_deck_values, state="disabled")
    widgets["deck_combo"].pack(side="left", fill="x", expand=True, padx=5, pady=5)
    ToolTip(widgets["deck_combo"], localization_manager.get_text("deck_selection_tooltip"))
    
    def refresh_decks_button():
        try:
            current_full = tvars["deck_var"].get()
            current_clean = dependencies.clean_deck_name(current_full) if hasattr(dependencies, 'clean_deck_name') else current_full
            
            decks = dependencies.get_deck_names()
            if isinstance(decks, list) and decks:
                cached_decks[:] = decks
                widgets["deck_combo"].configure(values=decks, state="normal")
                
                found_match = False
                if current_clean:
                    for deck_str in decks:
                        deck_clean = dependencies.clean_deck_name(deck_str) if hasattr(dependencies, 'clean_deck_name') else deck_str
                        if deck_clean == current_clean:
                            tvars["deck_var"].set(deck_str)
                            found_match = True
                            break
                
                if not found_match:
                    if not current_full or current_full in [localization_manager.get_text("loading"), localization_manager.get_text("anki_not_available"), localization_manager.get_text("decks_not_found")]:
                        tvars["deck_var"].set(decks[0])
                    elif current_full not in decks:
                        tvars["deck_var"].set(decks[0])

            elif decks == "ANKI_CONNECT_ERROR":
                widgets["deck_combo"].configure(values=[localization_manager.get_text("anki_not_available")], state="disabled")
                tvars["deck_var"].set(localization_manager.get_text("anki_not_available"))
                messagebox.showwarning(localization_manager.get_text("warning"), "Не удалось подключиться к AnkiConnect.\nУбедитесь, что Anki запущен с установленным AnkiConnect.")
            else:
                widgets["deck_combo"].configure(values=[localization_manager.get_text("decks_not_found")], state="disabled")
                tvars["deck_var"].set(localization_manager.get_text("decks_not_found"))
        except Exception as e:
            print(f"Ошибка обновления колод: {e}")
    
    widgets["refresh_decks_btn"] = ctk.CTkButton(deck_frame, text="🔄", width=30, command=refresh_decks_button)
    widgets["refresh_decks_btn"].pack(side="left", padx=5)
    ToolTip(widgets["refresh_decks_btn"], localization_manager.get_text("refresh_decks"))
    
    def on_create_deck():
        """Создает новую колоду используя универсальный диалог"""
        new_name = ask_string_dialog(root, localization_manager.get_text("create_deck"), localization_manager.get_text("new_deck_name"))
        if new_name and dependencies.create_deck(new_name):
            decks = dependencies.get_deck_names() or [new_name]
            widgets["deck_combo"].configure(values=decks)
            tvars["deck_var"].set(new_name)
            messagebox.showinfo(localization_manager.get_text("success"), localization_manager.get_text("deck_created", name=new_name))
    
    widgets["create_deck_btn"] = ctk.CTkButton(deck_frame, text="+", width=30, command=on_create_deck)
    widgets["create_deck_btn"].pack(side="left", padx=5)
    ToolTip(widgets["create_deck_btn"], localization_manager.get_text("create_deck"))



    # ========================================
    # BOTTOM ACTIONS
    # ========================================
    action_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    action_frame.pack(fill="x", pady=10, padx=5)
    
    status_left_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
    status_left_frame.pack(side="left", padx=5)
    
    widgets["processing_indicator"] = ctk.CTkLabel(status_left_frame, text="", font=("Roboto", 10), text_color=("#5a9fd4", "#5a9fd4"))
    widgets["processing_indicator"].pack(side="left", padx=(0, 10))
    
    widgets["prompt_status_label"] = ctk.CTkLabel(status_left_frame, text="", font=("Roboto", 10), text_color=("#888888", "#888888"))
    widgets["prompt_status_label"].pack(side="left", padx=0)
    
    add_to_anki_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
    add_to_anki_frame.pack(side="right", padx=5)
    
    auto_add_label = ctk.CTkLabel(add_to_anki_frame, text=localization_manager.get_text("auto_add"), font=("Roboto", 12))
    auto_add_label.pack(side="left", padx=(0, 2))
    
    tvars["auto_add_to_anki_var"] = tk.BooleanVar(value=settings.get("AUTO_ADD_TO_ANKI", False))
    widgets["auto_add_to_anki_check"] = ctk.CTkCheckBox(add_to_anki_frame, text="", variable=tvars["auto_add_to_anki_var"], width=20, command=save_all_ui_settings)
    widgets["auto_add_to_anki_check"].pack(side="left", padx=(0, 5))
    ToolTip(widgets["auto_add_to_anki_check"], localization_manager.get_text("auto_add_tooltip"))
    
    widgets["add_btn"] = ctk.CTkButton(add_to_anki_frame, text="✅ " + localization_manager.get_text("add_to_anki"), command=dependencies.on_yes_action, width=100, fg_color="#2CC985", hover_color="#26AD72")
    widgets["add_btn"].pack(side="left")
    
    main_window_components.update({"widgets": widgets, "vars": tvars, "root": root, "refresh_decks_command": refresh_decks_button})

    # ========================================
    # FINAL SETUP AND BINDINGS
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
        from core.app_state import app_state
        dependencies.stop_clipboard_monitoring()
        current_settings = load_settings(update_app_state=False)
        
        raw_deck = tvars["deck_var"].get()
        current_settings["LAST_DECK"] = dependencies.clean_deck_name(raw_deck) if hasattr(dependencies, 'clean_deck_name') else raw_deck
        # OLLAMA_MODEL теперь сохраняется только через настройки AI
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

    def play_selected_audio(widgets, tvars, dependencies, root):
        source = tvars["sound_source_var"].get()
        text_widget = widgets["translation_text"] if source == "translation" else widgets["german_text"]
        text = text_widget.get("1.0", tk.END).strip()
        
        if not text or text == placeholders["german"][0] or text == placeholders["translation"][0]:
            if not text:
                messagebox.showwarning(localization_manager.get_text("warning"), localization_manager.get_text("empty_field_warning"))
            return
        
        def worker():
            try:
                lang = getattr(dependencies, "TTS_LANG", "de")
                tld = getattr(dependencies, "TTS_TLD", "de")
                speed_level = getattr(dependencies, "TTS_SPEED_LEVEL", 0)
                audio_utils.play_text_audio(text, lang, speed_level, tld, parent=root)
            except Exception as e:
                messagebox.showerror(localization_manager.get_text("error"), f"Не удалось воспроизвести аудио: {e}")
        
        dependencies.threading.Thread(target=worker, daemon=True).start()

    def deferred_load():
        from core.prompts_manager import prompts_manager
        try:
            prompt_names = prompts_manager.get_preset_names()
            widgets["prompt_combo"].configure(values=prompt_names)
            if last_prompt and last_prompt in prompt_names:
                tvars["prompt_var"].set(last_prompt)
                if "prompt_status_label" in widgets:
                    widgets["prompt_status_label"].configure(text=localization_manager.get_text("prompt_label", name=last_prompt))
                on_prompt_select(last_prompt)
        except Exception as e:
            print(f"Ошибка обновления промптов: {e}")
        
        if tvars["pause_monitoring_var"].get():
            root.animation_label.pack(expand=True)
            root._animation_running = True
            root.start_animation()
        else:
            root.animation_label.pack(expand=True)
            root.animation_label.configure(text="")
        
        dependencies.threading.Thread(target=dependencies.load_background_data_worker, args=(dependencies.results_queue,), daemon=True).start()
    
    def start_animation():
        """Запускает анимацию заголовка с точками"""
        if not hasattr(root, '_animation_running'):
            root._animation_running = False
        
        if not root._animation_running:
            return
        
        dots = ["", ".", "..", "..."]
        if not hasattr(root, '_animation_index'):
            root._animation_index = 0
        
        root.animation_label.configure(text=f"{localization_manager.get_text('clipboard_indicator')}{dots[root._animation_index]}")
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
    root.bind("<Control-S>", on_ctrl_s) # Для случая с Caps Lock или русской раскладки
    
    global_clipboard_manager = GlobalClipboardManager(root, widgets["clipboard_handlers"])


def build_main_window(dependencies, root, settings, start_time=None):
    """
    Создаёт и настраивает виджеты в главном окне.
    """
    root.title(localization_manager.get_text("app_title"))
    root.geometry("500x750")
    
    # Контейнер для боковой панели
    master_container = ctk.CTkFrame(root, fg_color="transparent")
    master_container.pack(fill="both", expand=True)
    
    # Левая панель (Main)
    left_panel = ctk.CTkFrame(master_container)
    
    widgets = {}
    tvars = {}

    root.after(10, lambda: populate_main_window(dependencies, root, settings, left_panel, widgets, tvars, master_container))
    
    return root
