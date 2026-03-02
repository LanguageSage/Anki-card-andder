# -*- coding: utf-8 -*-
"""
Секция контролов: промпт-селектор, генерация, AI индикатор.
"""
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import os

from core.localization import localization_manager


def build_controls(root, main_frame, widgets, tvars, settings, dependencies, save_all_ui_settings):
    """Создаёт блок контролов: промпт, генерация, AI модель.
    
    Returns:
        callable: функция on_prompt_select для использования в deferred_load.
    """
    from ui.main_window import ToolTip

    # ========================================
    # PROMPT & UPDATES ROW
    # ========================================
    controls_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    controls_frame.pack(fill="x", pady=5, padx=5)
    tvars["prompt_var"] = tk.StringVar(value="")
    widgets["prompt_combo"] = ctk.CTkComboBox(controls_frame, variable=tvars["prompt_var"], values=[""], width=200)
    widgets["prompt_combo"].pack(side="left", padx=(0, 10))

    # Индикатор буфера
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

    # === PROMPT SELECT HANDLER ===
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
    widgets["context_check"] = ctk.CTkCheckBox(
        checks_frame, text=localization_manager.get_text("context_enabled"),
        variable=tvars["context_var"], command=save_all_ui_settings
    )
    widgets["context_check"].pack(anchor="w", pady=2)
    ToolTip(widgets["context_check"], localization_manager.get_text("context_enabled_tooltip"))

    pause_setting = settings.get("PAUSE_CLIPBOARD_MONITORING", True)
    tvars["pause_monitoring_var"] = tk.BooleanVar(value=not pause_setting)
    tvars["pause_monitoring_var"].trace_add("write", dependencies.update_pause_monitoring_flag)
    widgets["pause_monitoring_check"] = ctk.CTkCheckBox(
        checks_frame, text=localization_manager.get_text("clipboard_monitoring"),
        variable=tvars["pause_monitoring_var"]
    )
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
    widgets["auto_generate_check"] = ctk.CTkCheckBox(
        top_gen_row, text="", variable=tvars["auto_generate_var"],
        width=20, command=on_auto_generate_toggle
    )
    widgets["auto_generate_check"].pack(side="left", padx=(0, 5))
    ToolTip(widgets["auto_generate_check"], localization_manager.get_text("auto_generate_tooltip"))
    dependencies.update_auto_generate_flag()

    widgets["generate_btn"] = ctk.CTkButton(
        top_gen_row, text=localization_manager.get_text("generate"),
        command=dependencies.generate_action, height=40, width=130
    )
    widgets["generate_btn"].pack(side="left", fill="x", expand=True)

    # === AI MODEL INDICATOR ===
    ai_indicator_frame = ctk.CTkFrame(gen_frame)
    ai_indicator_frame.pack(side="right", padx=5, pady=5)

    # Логотип Wordy
    try:
        from PIL import Image
        from core.settings_manager import get_resource_path
        logo_path = get_resource_path(os.path.join("assets", "logo.png"))
        if os.path.exists(logo_path):
            img = Image.open(logo_path)
            aspect_ratio = img.width / img.height
            new_width = int(25 * aspect_ratio)
            logo_image = ctk.CTkImage(light_image=img, dark_image=img, size=(new_width, 25))
            logo_label = ctk.CTkLabel(ai_indicator_frame, text="", image=logo_image)
            logo_label.pack(side="top", pady=(0, 2))
            widgets["logo_label"] = logo_label
    except Exception as e:
        print(f"Ошибка загрузки логотипа: {e}")

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

    return on_prompt_select
