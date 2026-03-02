# -*- coding: utf-8 -*-
"""
Секция выбора колоды Anki.
"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from core.localization import localization_manager


def build_deck_selector(root, main_frame, widgets, tvars, settings, dependencies, save_all_ui_settings):
    """Создаёт блок выбора колоды: комбобокс, refresh, create."""
    from ui.main_window import ToolTip, ask_string_dialog

    deck_frame = ctk.CTkFrame(main_frame)
    deck_frame.pack(fill="x", pady=5, padx=5)
    cached_decks = [dependencies.DEFAULT_DECK_NAME]

    tvars["deck_var"] = tk.StringVar(value=settings.get("LAST_DECK", cached_decks[0]))
    initial_deck_values = [settings["LAST_DECK"]] if settings.get("LAST_DECK") else [localization_manager.get_text("loading")]

    widgets["deck_combo"] = ctk.CTkComboBox(
        deck_frame, variable=tvars["deck_var"],
        values=initial_deck_values, state="disabled"
    )
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
                    status_texts = [
                        localization_manager.get_text("loading"),
                        localization_manager.get_text("anki_not_available"),
                        localization_manager.get_text("decks_not_found"),
                    ]
                    if not current_full or current_full in status_texts:
                        tvars["deck_var"].set(decks[0])
                    elif current_full not in decks:
                        tvars["deck_var"].set(decks[0])

            elif decks == "ANKI_CONNECT_ERROR":
                widgets["deck_combo"].configure(
                    values=[localization_manager.get_text("anki_not_available")], state="disabled"
                )
                tvars["deck_var"].set(localization_manager.get_text("anki_not_available"))
                messagebox.showwarning(
                    localization_manager.get_text("warning"),
                    "Не удалось подключиться к AnkiConnect.\nУбедитесь, что Anki запущен с установленным AnkiConnect."
                )
            else:
                widgets["deck_combo"].configure(
                    values=[localization_manager.get_text("decks_not_found")], state="disabled"
                )
                tvars["deck_var"].set(localization_manager.get_text("decks_not_found"))
        except Exception as e:
            print(f"Ошибка обновления колод: {e}")

    widgets["refresh_decks_btn"] = ctk.CTkButton(deck_frame, text="🔄", width=30, command=refresh_decks_button)
    widgets["refresh_decks_btn"].pack(side="left", padx=5)
    ToolTip(widgets["refresh_decks_btn"], localization_manager.get_text("refresh_decks"))

    def on_create_deck():
        """Создает новую колоду используя универсальный диалог"""
        new_name = ask_string_dialog(
            root,
            localization_manager.get_text("create_deck"),
            localization_manager.get_text("new_deck_name")
        )
        if new_name and dependencies.create_deck(new_name):
            decks = dependencies.get_deck_names() or [new_name]
            widgets["deck_combo"].configure(values=decks)
            tvars["deck_var"].set(new_name)
            messagebox.showinfo(
                localization_manager.get_text("success"),
                localization_manager.get_text("deck_created", name=new_name)
            )

    widgets["create_deck_btn"] = ctk.CTkButton(deck_frame, text="+", width=30, command=on_create_deck)
    widgets["create_deck_btn"].pack(side="left", padx=5)
    ToolTip(widgets["create_deck_btn"], localization_manager.get_text("create_deck"))

    return refresh_decks_button
