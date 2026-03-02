# -*- coding: utf-8 -*-
"""
Секция полей ввода: german_text, translation_text, context_widget + placeholder-система.
"""
import customtkinter as ctk

from core.localization import localization_manager
from core.clipboard_manager import setup_text_widget_context_menu


def build_input_fields(main_frame, widgets, tvars):
    """Создаёт поля ввода с placeholder-системой.
    
    Returns:
        dict: placeholders — мутабельные списки с текстами placeholder.
    """
    placeholders = {
        "german": [localization_manager.get_text("placeholder_german")],
        "translation": [localization_manager.get_text("placeholder_translation")],
        "context": [localization_manager.get_text("placeholder_context")],
    }

    # === TEXT FIELDS ===
    widgets["german_text"] = ctk.CTkTextbox(main_frame, height=70, font=("Roboto", 14), text_color="gray")
    widgets["german_text"].insert("1.0", placeholders["german"][0])
    widgets["german_text"].pack(pady=(0, 5), padx=5, fill="both", expand=True)

    widgets["translation_text"] = ctk.CTkTextbox(main_frame, height=70, font=("Roboto", 14), text_color="gray")
    widgets["translation_text"].insert("1.0", placeholders["translation"][0])
    widgets["translation_text"].pack(pady=(0, 5), padx=5, fill="both", expand=True)

    widgets["context_widget"] = ctk.CTkTextbox(main_frame, height=180, font=("Roboto", 12), text_color="gray")
    widgets["context_widget"].insert("1.0", placeholders["context"][0])
    widgets["context_widget"].pack(pady=(0, 5), padx=5, fill="both", expand=True)

    # === PLACEHOLDER LOGIC ===
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

    # === PLACEHOLDER LANGUAGE UPDATE ===
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
            w = widgets.get(widget_name)
            if w and w.get("1.0", "end-1c").strip() == old_ph:
                w.delete("1.0", "end")
                w.insert("1.0", new_ph)

    localization_manager.add_observer(_update_placeholders)

    # === CONTEXT MENUS ===
    widgets["clipboard_handlers"] = []
    widgets["clipboard_handlers"].append(setup_text_widget_context_menu(widgets["german_text"]))
    widgets["clipboard_handlers"].append(setup_text_widget_context_menu(widgets["translation_text"]))
    widgets["clipboard_handlers"].append(setup_text_widget_context_menu(widgets["context_widget"]))

    return placeholders
