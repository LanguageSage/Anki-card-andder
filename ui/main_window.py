# -*- coding: utf-8 -*-
"""
Главное окно приложения Anki German Helper.
Оркестрирует построение UI, делегируя секциям из ui/sections/.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import sys

from core.clipboard_manager import setup_text_widget_context_menu
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
    Оркестрирует построение UI, делегируя секциям из ui/sections/.
    """
    from core.app_state import app_state
    main_window_components = app_state.main_window_components
    last_prompt = settings.get("LAST_PROMPT", "")

    def save_all_ui_settings(event=None):
        """Универсальная функция для мгновенного сохранения всех настроек UI"""
        try:
            current_settings = dependencies.load_settings()

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

    if master_container:
        master_container.grid_columnconfigure(0, weight=1, uniform="")
        master_container.grid_columnconfigure(1, weight=0, uniform="")
        master_container.grid_rowconfigure(0, weight=1)

    main_frame.pack_forget()
    main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def toggle_sidebar():
        if not master_container:
            return
        if not sidebar_visible[0]:
            master_container.grid_columnconfigure(0, weight=1, uniform="group1")
            master_container.grid_columnconfigure(1, weight=1, uniform="group1")
            main_frame.grid_configure(padx=(10, 5))
            if right_panel[0] is None:
                right_panel[0] = create_batch_panel(
                    master_container,
                    dependencies.start_batch_processing,
                    dependencies.stop_batch_processing
                )
            right_panel[0].grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
            root.geometry("1000x750")
            sidebar_visible[0] = True
        else:
            main_frame.grid_configure(padx=10)
            if right_panel[0]:
                right_panel[0].grid_forget()
            master_container.grid_columnconfigure(0, weight=1, uniform="")
            master_container.grid_columnconfigure(1, weight=0, uniform="")
            root.geometry("500x750")
            sidebar_visible[0] = False

    # ========================================
    # ПОСТРОЕНИЕ СЕКЦИЙ UI
    # ========================================
    from ui.sections.header import build_header
    from ui.sections.input_fields import build_input_fields
    from ui.sections.controls import build_controls
    from ui.sections.deck_selector import build_deck_selector
    from ui.sections.bottom_actions import build_bottom_actions

    build_header(root, main_frame, widgets, tvars, settings, dependencies, toggle_sidebar, save_all_ui_settings)
    placeholders = build_input_fields(main_frame, widgets, tvars)
    on_prompt_select_fn = build_controls(root, main_frame, widgets, tvars, settings, dependencies, save_all_ui_settings)
    refresh_decks_fn = build_deck_selector(root, main_frame, widgets, tvars, settings, dependencies, save_all_ui_settings)
    build_bottom_actions(root, main_frame, widgets, tvars, settings, dependencies,
                         save_all_ui_settings, placeholders, last_prompt, on_prompt_select_fn)

    main_window_components.update({
        "widgets": widgets, "vars": tvars, "root": root,
        "refresh_decks_command": refresh_decks_fn
    })


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
