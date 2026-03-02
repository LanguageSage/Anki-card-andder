# -*- coding: utf-8 -*-
"""
Утилита для создания popup-меню с автоскрытием.
Извлечена из повторяющегося паттерна в show_lang_menu / show_menu.
"""
import tkinter as tk
import customtkinter as ctk


def create_popup_menu(root, anchor_widget, items, popup_ref, opening_flag=None):
    """Создаёт popup-меню под кнопкой с автоскрытием при уходе мыши.
    
    Args:
        root: корневое окно
        anchor_widget: кнопка-якорь, под которой появится popup
        items: список dict — {"text": str, "command": callable, "active": bool}
        popup_ref: list с одним элементом [None] — мутабельная ссылка на popup
        opening_flag: list с одним элементом [bool] — защита от двойного открытия
    
    Returns:
        Toplevel popup окно
    """
    if opening_flag and opening_flag[0]:
        return None
    if popup_ref[0] is not None:
        destroy_popup(popup_ref)
        return None
    
    if opening_flag:
        opening_flag[0] = True
    
    p = tk.Toplevel(root)
    p.wm_overrideredirect(True)
    p.attributes("-topmost", True)
    p.configure(bg="#2b2b2b")
    
    x = anchor_widget.winfo_rootx()
    y = anchor_widget.winfo_rooty() + anchor_widget.winfo_height() + 2
    p.geometry(f"+{x}+{y}")
    
    f = ctk.CTkFrame(p, fg_color="#333333", border_width=1, border_color="#555555", corner_radius=4)
    f.pack(fill="both", expand=True)
    
    for i, item in enumerate(items):
        pady = (2, 0) if i == 0 else ((0, 2) if i == len(items) - 1 else (0, 0))
        btn = ctk.CTkButton(
            f, text=item["text"], width=item.get("width", 100), height=28,
            fg_color="transparent", hover_color="#444444",
            text_color="#2cc985" if item.get("active", False) else "white",
            anchor="w", command=item["command"]
        )
        btn.pack(pady=pady, padx=2)
    
    popup_ref[0] = p
    if opening_flag:
        opening_flag[0] = False
    
    # Автоскрытие при уходе мыши
    def check_leave():
        if popup_ref[0] is None:
            return
        try:
            rx, ry = p.winfo_pointerxy()
            bx, by = anchor_widget.winfo_rootx(), anchor_widget.winfo_rooty()
            bw, bh = anchor_widget.winfo_width(), anchor_widget.winfo_height()
            px, py = p.winfo_rootx(), p.winfo_rooty()
            pw, ph = p.winfo_width(), p.winfo_height()
            
            in_btn = (bx - 5 <= rx <= bx + bw + 5) and (by - 5 <= ry <= by + bh + 5)
            in_pop = (px - 5 <= rx <= px + pw + 5) and (py - 5 <= ry <= py + ph + 5)
            
            if not (in_btn or in_pop):
                destroy_popup(popup_ref)
            else:
                p.after(100, check_leave)
        except tk.TclError:
            popup_ref[0] = None
    
    p.after(500, check_leave)
    return p


def destroy_popup(popup_ref):
    """Безопасно уничтожает popup-меню."""
    if popup_ref[0]:
        try:
            popup_ref[0].destroy()
        except Exception:
            pass
        popup_ref[0] = None
