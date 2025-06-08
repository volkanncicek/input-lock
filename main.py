import sys
import threading
import time
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import messagebox
from typing import Any, Dict, List, Optional, Set, Union

import darkdetect
import pywinstyles
import sv_ttk
from PIL import Image, ImageTk
from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode

from config import ASSETS_DIR, FONT_FAMILY, THEME_CONFIG
from localization import DEFAULT_LANGUAGE, TRANSLATIONS, detect_system_language


@dataclass
class AppConfig:

  lock_duration_seconds: int = 60 * 2
  unlock_sequence: List[str] = field(default_factory=lambda: ["shift", "alt_l", "l"])
  language: str = field(default_factory=detect_system_language)


class LocalizationManager:
  def __init__(self, language: str = DEFAULT_LANGUAGE):
    self.language = language

  def get_text(self, key: str) -> str:
    for lang_code in (self.language, DEFAULT_LANGUAGE):
      text = TRANSLATIONS.get(lang_code, {}).get(key)
      if text is not None:
        return text
    return f"<KEY:'{key}'_NOT_FOUND>"


class ThemeManager:
  def __init__(self):
    self.current_theme = self._detect_system_theme()

  def _detect_system_theme(self) -> str:
    try:
      detected_theme = darkdetect.theme()
      return "dark" if detected_theme == "Dark" else "light"
    except Exception:
      return "dark"

  def get_color(self, color_key: str) -> str:
    return THEME_CONFIG[self.current_theme].get(color_key, "#000000")

  def apply_system_theme(self):
    try:
      sv_ttk.set_theme(self.current_theme)
    except Exception:
      sv_ttk.set_theme("dark")

  def apply_titlebar_theme(self, window: tk.Tk):
    try:
      bg_color = self.get_color("background")
      version = sys.getwindowsversion()

      if version.major >= 10 and version.build >= 22000:  # Windows 11
        pywinstyles.change_header_color(window, bg_color)
        pywinstyles.change_border_color(window, bg_color)
      elif version.major == 10:  # Windows 10
        is_dark = self.current_theme == "dark"
        pywinstyles.apply_style(window, "dark" if is_dark else "normal")
        window.attributes("-alpha", 0.99)
        window.attributes("-alpha", 1)
    except Exception:
      # Silently fail if theming is not possible (e.g., non-Windows OS)
      pass


class ImageManager:
  def __init__(self, theme_manager: ThemeManager):
    self.theme_manager = theme_manager
    self._cache = {}

  def load_png_image(self, png_path: Path, size: tuple) -> ImageTk.PhotoImage:
    cache_key = (png_path, size, self.theme_manager.current_theme)
    if cache_key in self._cache:
      return self._cache[cache_key]

    img = Image.open(png_path).convert("RGBA")
    img = self._make_square(img)
    img = self._apply_theme_colors(img)
    img = img.resize(size, Image.Resampling.LANCZOS)
    photo_image = ImageTk.PhotoImage(img)
    self._cache[cache_key] = photo_image
    return photo_image

  def _make_square(self, img: Image.Image) -> Image.Image:
    x, y = img.size
    if x != y:
      max_side = max(x, y)
      new_img = Image.new("RGBA", (max_side, max_side), (0, 0, 0, 0))
      new_img.paste(img, ((max_side - x) // 2, (max_side - y) // 2))
      return new_img
    return img

  def _apply_theme_colors(self, img: Image.Image) -> Image.Image:
    if self.theme_manager.current_theme == "dark":
      try:
        data = img.getdata()
        new_data = []
        for item in data:
          if item[0] < 10 and item[1] < 10 and item[2] < 10:  # convert black pixels to white
            new_data.append((255, 255, 255, item[3]))
          else:
            new_data.append(item)
        img.putdata(new_data)
      except Exception:
        pass
    return img


class KeyboardManager:
  def __init__(self, unlock_sequence: List[str]):
    self.unlock_sequence = self._parse_unlock_sequence(unlock_sequence)
    self.pressed_keys: Set[Union[Key, KeyCode]] = set()
    self.key_sequence: List[Union[Key, KeyCode]] = []
    self.keyboard_listener: Optional[keyboard.Listener] = None

  def _parse_unlock_sequence(self, sequence: List[str]) -> List[Union[Key, KeyCode]]:
    return [self._parse_key(key_str) for key_str in sequence]

  def _parse_key(self, key_str: str) -> Union[Key, KeyCode]:
    key_str = key_str.lower().strip()
    if hasattr(keyboard.Key, key_str):
      return getattr(keyboard.Key, key_str)
    if len(key_str) == 1:
      return KeyCode.from_char(key_str)
    raise ValueError(f"Invalid key identifier: '{key_str}'")

  def _normalize_key(self, key: Union[Key, KeyCode]) -> Union[Key, KeyCode]:
    if isinstance(key, KeyCode) and key.char:
      return KeyCode.from_char(key.char.lower())
    return key

  def start_listening(self, unlock_callback):
    if self.keyboard_listener is None:
      self.keyboard_listener = keyboard.Listener(
        on_press=lambda key: self._on_key_press(key, unlock_callback),
        on_release=self._on_key_release,
        suppress=False,
      )
      self.keyboard_listener.start()

  def stop_listening(self):
    if self.keyboard_listener:
      self.keyboard_listener.stop()
      self.keyboard_listener = None
    self.pressed_keys.clear()
    self.key_sequence.clear()

  def _on_key_press(self, key: Optional[Union[Key, KeyCode]], unlock_callback):
    if not key:
      return

    normalized_key = self._normalize_key(key)
    self.pressed_keys.add(normalized_key)

    if normalized_key not in self.key_sequence:
      self.key_sequence.append(normalized_key)

    if self._check_unlock_sequence():
      unlock_callback()

  def _on_key_release(self, key: Optional[Union[Key, KeyCode]]):
    if not key:
      return

    normalized = self._normalize_key(key)
    self.pressed_keys.discard(normalized)
    self.key_sequence.clear()

  def _check_unlock_sequence(self) -> bool:
    if len(self.pressed_keys) < len(self.unlock_sequence):
      return False

    recent_sequence = self.key_sequence[-len(self.unlock_sequence) :]
    return set(recent_sequence) == set(self.unlock_sequence) and recent_sequence == self.unlock_sequence


class MouseManager:
  def __init__(self):
    self.mouse_listener: Optional[mouse.Listener] = None
    self.suppress_input = False

  def start_listening(self):
    if self.mouse_listener is None:
      self.mouse_listener = mouse.Listener(
        on_click=self._on_mouse_click,
        on_scroll=self._on_mouse_scroll,
        on_move=self._on_mouse_move,
        suppress=False,
      )
      self.mouse_listener.start()

  def stop_listening(self):
    if self.mouse_listener:
      self.mouse_listener.stop()
      self.mouse_listener = None
    self.suppress_input = False

  def enable_suppression(self):
    self.suppress_input = True
    if self.mouse_listener:
      self.stop_listening()
      self.mouse_listener = mouse.Listener(
        on_click=self._on_mouse_click,
        on_scroll=self._on_mouse_scroll,
        on_move=self._on_mouse_move,
        suppress=True,
      )
      self.mouse_listener.start()

  def disable_suppression(self):
    self.suppress_input = False

  def _on_mouse_click(self, x, y, button, pressed):
    if self.suppress_input:
      return False
    return True

  def _on_mouse_scroll(self, x, y, dx, dy):
    if self.suppress_input:
      return False
    return True

  def _on_mouse_move(self, x, y):
    if self.suppress_input:
      return False
    return True


class InputManager:
  def __init__(self, unlock_sequence: List[str]):
    self.keyboard_manager = KeyboardManager(unlock_sequence)
    self.mouse_manager = MouseManager()

  def start_listening(self, unlock_callback):
    self.keyboard_manager.start_listening(unlock_callback)
    self.mouse_manager.start_listening()

  def stop_listening(self):
    self.keyboard_manager.stop_listening()
    self.mouse_manager.stop_listening()

  def enable_input_suppression(self):
    self.mouse_manager.enable_suppression()

  def disable_input_suppression(self):
    self.mouse_manager.disable_suppression()


class CustomButton(tk.Button):
  def __init__(self, master, *args, hover_color: Optional[str] = None, **kwargs):
    super().__init__(master, *args, **kwargs)
    self._setup_styling(hover_color)

  def _setup_styling(self, hover_color: Optional[str]):
    self.configure(
      relief=tk.FLAT,
      bd=0,
      cursor="hand2",
      highlightthickness=0,
    )
    self.default_bg = self["bg"]
    self.hover_color = hover_color
    self.bind("<Enter>", self._on_enter)
    self.bind("<Leave>", self._on_leave)

  def _on_enter(self, event: tk.Event):
    if self["state"] != tk.DISABLED and self.hover_color:
      self["bg"] = self.hover_color

  def _on_leave(self, event: tk.Event):
    if self["state"] != tk.DISABLED:
      self["bg"] = self.default_bg


class LockOverlay:
  def __init__(
    self,
    parent: tk.Tk,
    theme_manager: ThemeManager,
    localization: LocalizationManager,
    image_manager: ImageManager,
    unlock_combo: str,
  ):
    self.parent = parent
    self.theme_manager = theme_manager
    self.localization = localization
    self.image_manager = image_manager
    self.unlock_combo = unlock_combo
    self.window: Optional[tk.Toplevel] = None
    self.timer_label: Optional[tk.Label] = None
    self.countdown_seconds = 0
    self.clean_image_ref: Optional[ImageTk.PhotoImage] = None

  def create(self, countdown_seconds: int):
    self.countdown_seconds = countdown_seconds
    self.window = tk.Toplevel(self.parent)
    self._setup_window()
    self._create_widgets()
    self._start_timer_updates()

  def _setup_window(self):
    assert self.window is not None
    self.window.attributes("-fullscreen", True)
    self.window.attributes("-alpha", 0.95)
    self.window.attributes("-topmost", True)
    self.window.configure(bg=self.theme_manager.get_color("overlay_bg"))
    self.window.protocol("WM_DELETE_WINDOW", lambda: None)

  def _create_widgets(self):
    overlay_frame = tk.Frame(self.window, bg=self.theme_manager.get_color("overlay_bg"))
    overlay_frame.pack(expand=True, fill=tk.BOTH)

    content_frame = tk.Frame(overlay_frame, bg=self.theme_manager.get_color("overlay_bg"))
    content_frame.place(relx=0.5, rely=0.5, anchor="center")

    detailed_message = self.localization.get_text("locked_detailed_message").format(minutes=self.countdown_seconds // 60, combo=self.unlock_combo)
    tk.Label(
      content_frame,
      text=detailed_message,
      font=(FONT_FAMILY, 18),
      fg=self.theme_manager.get_color("text_color"),
      bg=self.theme_manager.get_color("overlay_bg"),
      justify=tk.CENTER,
      wraplength=800,
    ).pack(pady=(0, 30))

    self.clean_image_ref = self.image_manager.load_png_image(ASSETS_DIR / "step-clean.png", (120, 120))
    img_label = tk.Label(content_frame, image=self.clean_image_ref, bg=self.theme_manager.get_color("overlay_bg"))
    img_label.pack(pady=(0, 30))

    self.timer_label = tk.Label(
      content_frame,
      font=(FONT_FAMILY, 48, "bold"),
      fg=self.theme_manager.get_color("text_color"),
      bg=self.theme_manager.get_color("overlay_bg"),
    )
    self.timer_label.pack()

  def _start_timer_updates(self):
    self._update_timer_display()

  def _update_timer_display(self):
    if self.window and self.window.winfo_exists() and self.timer_label and self.countdown_seconds >= 0:
      mins, secs = divmod(self.countdown_seconds, 60)
      self.timer_label.config(text=f"{mins:02d}:{secs:02d}")

      if self.countdown_seconds > 0:
        self.window.after(1000, self._update_timer_display)

  def update_countdown(self, seconds: int):
    self.countdown_seconds = seconds

  def destroy(self):
    if self.window:
      self.window.destroy()
      self.window = None


class CleanLockApp:
  def __init__(self, root: tk.Tk):
    self.root = root
    self.config = AppConfig()

    self.theme_manager = ThemeManager()
    self.localization = LocalizationManager(self.config.language)
    self.image_manager = ImageManager(self.theme_manager)
    self.input_manager = InputManager(self.config.unlock_sequence)

    self.is_locked = False
    self.countdown_seconds = 0
    self.timer_thread: Optional[threading.Thread] = None
    self.overlay: Optional[LockOverlay] = None

    self.widgets: Dict[str, Any] = {}

    self._initialize_app()

  def _initialize_app(self):
    self.theme_manager.apply_system_theme()
    self._setup_main_window()
    self._create_ui()
    self._update_ui_texts()

  def _setup_main_window(self):
    self.root.geometry("800x550")
    self.root.resizable(False, False)
    self.root.overrideredirect(True)
    self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    self.root.configure(bg=self.theme_manager.get_color("background"))
    self._center_window()

  def _center_window(self):
    self.root.update_idletasks()
    width = self.root.winfo_width()
    height = self.root.winfo_height()
    x = (self.root.winfo_screenwidth() // 2) - (width // 2)
    y = (self.root.winfo_screenheight() // 2) - (height // 2)
    self.root.geometry(f"{width}x{height}+{x}+{y}")

  def _create_ui(self):
    main_frame = tk.Frame(self.root, bg=self.theme_manager.get_color("background"), padx=40, pady=20)
    main_frame.pack(expand=True, fill=tk.BOTH)

    self._create_header(main_frame)
    self._create_steps_section(main_frame)
    self._create_buttons(main_frame)

  def _create_header(self, parent):
    self.widgets["icon"] = tk.Label(
      parent,
      text="🧼",
      font=("Segoe UI Emoji", 48),
      fg=self.theme_manager.get_color("text_color"),
      bg=self.theme_manager.get_color("background"),
    )
    self.widgets["icon"].pack(pady=(10, 0))

    self.widgets["title"] = tk.Label(
      parent,
      font=(FONT_FAMILY, 24, "bold"),
      fg=self.theme_manager.get_color("text_color"),
      bg=self.theme_manager.get_color("background"),
    )
    self.widgets["title"].pack(pady=(5, 10))

    self.widgets["description"] = tk.Label(
      parent,
      justify=tk.CENTER,
      font=(FONT_FAMILY, 11),
      fg=self.theme_manager.get_color("text_muted"),
      bg=self.theme_manager.get_color("background"),
      wraplength=700,
    )
    self.widgets["description"].pack(pady=(10, 30))

  def _create_steps_section(self, parent):
    steps_container = tk.Frame(parent, bg=self.theme_manager.get_color("background"))
    steps_container.pack(pady=(5, 5), fill=tk.X, expand=False)

    images = {
      "step-lock": self.image_manager.load_png_image(ASSETS_DIR / "step-lock.png", (120, 100)),
      "step-clean": self.image_manager.load_png_image(ASSETS_DIR / "step-clean.png", (120, 100)),
      "step-done": self.image_manager.load_png_image(ASSETS_DIR / "step-done.png", (120, 100)),
      "separator-right": self.image_manager.load_png_image(ASSETS_DIR / "separator-right.png", (40, 40)),
      "separator-left": self.image_manager.load_png_image(ASSETS_DIR / "separator-left.png", (40, 40)),
    }

    self._create_step_column(steps_container, "lock", images["step-lock"])
    self._create_arrow_separator(steps_container, images["separator-right"])
    self._create_step_column(steps_container, "clean", images["step-clean"])
    self._create_arrow_separator(steps_container, images["separator-left"])
    self._create_step_column(steps_container, "done", images["step-done"], show_unlock_info=True)

  def _create_step_column(
    self,
    parent,
    step_name: str,
    image: ImageTk.PhotoImage,
    show_unlock_info: bool = False,
  ):
    column = tk.Frame(parent, bg=self.theme_manager.get_color("background"))

    self.widgets[f"{step_name}_step"] = tk.Label(
      column,
      font=(FONT_FAMILY, 14, "bold"),
      fg=self.theme_manager.get_color("text_color"),
      bg=self.theme_manager.get_color("background"),
    )
    self.widgets[f"{step_name}_step"].pack(pady=(0, 4))

    img_label = tk.Label(column, image=image, bg=self.theme_manager.get_color("background"))
    img_label.image = image  # type: ignore
    img_label.pack()

    if show_unlock_info:
      self.widgets["unlock_info"] = tk.Label(
        column,
        font=(FONT_FAMILY, 8),
        justify=tk.CENTER,
        fg=self.theme_manager.get_color("text_muted"),
        bg=self.theme_manager.get_color("background"),
      )
      self.widgets["unlock_info"].pack(pady=(4, 0))
    else:
      tk.Label(
        column,
        text="",
        font=(FONT_FAMILY, 8),
        height=2,
        bg=self.theme_manager.get_color("background"),
      ).pack(pady=(4, 0))

    column.pack(side=tk.LEFT, padx=30, expand=True)

  def _create_arrow_separator(self, parent, arrow_image: ImageTk.PhotoImage):
    arrow_col = tk.Frame(parent, bg=self.theme_manager.get_color("background"))

    img_label = tk.Label(arrow_col, image=arrow_image, bg=self.theme_manager.get_color("background"))
    img_label.image = arrow_image  # type: ignore
    img_label.pack()

    tk.Label(
      arrow_col,
      text="",
      font=(FONT_FAMILY, 11, "bold"),
      bg=self.theme_manager.get_color("background"),
    ).pack()
    arrow_col.pack(side=tk.LEFT, padx=8)

  def _create_timer_separator(self, parent):
    timer_col = tk.Frame(parent, bg=self.theme_manager.get_color("background"))
    canvas = tk.Canvas(
      timer_col,
      width=40,
      height=40,
      bg=self.theme_manager.get_color("background"),
      highlightthickness=0,
    )
    canvas.create_oval(4, 4, 36, 36, outline=self.theme_manager.get_color("text_muted"), width=2)
    canvas.create_text(
      20,
      20,
      text="🕒",
      font=("Segoe UI Emoji", 16),
      fill=self.theme_manager.get_color("text_muted"),
    )
    canvas.pack()

    tk.Label(
      timer_col,
      text=f"{self.config.lock_duration_seconds // 60} mins",
      font=(FONT_FAMILY, 11, "bold"),
      fg=self.theme_manager.get_color("text_color"),
      bg=self.theme_manager.get_color("background"),
    ).pack()
    timer_col.pack(side=tk.LEFT, padx=8)

  def _create_buttons(self, parent):
    container = tk.Frame(parent, bg=self.theme_manager.get_color("background"), height=56)
    container.pack(side=tk.BOTTOM, fill=tk.X, pady=(30, 16))
    container.pack_propagate(False)

    style = {
      "font": (FONT_FAMILY, 11, "bold"),
      "padx": 0,
      "pady": 6,
      "width": 2,
      "height": 1,
    }

    self.widgets["lock_button"] = CustomButton(
      container,
      command=self._start_locking_process,
      bg=self.theme_manager.get_color("button_primary_bg"),
      fg=self.theme_manager.get_color("button_primary_fg"),
      hover_color=self.theme_manager.get_color("button_primary_hover"),
      **style,
    )

    self.widgets["exit_button"] = CustomButton(
      container,
      command=self._on_closing,
      bg=self.theme_manager.get_color("button_secondary_bg"),
      fg=self.theme_manager.get_color("button_secondary_fg"),
      hover_color=self.theme_manager.get_color("button_secondary_hover"),
      **style,
    )

    self.widgets["lock_button"].pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8))
    self.widgets["exit_button"].pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(8, 0))

  def _update_ui_texts(self):
    self.root.title(self.localization.get_text("app_title"))
    self.widgets["title"].config(text=self.localization.get_text("title"))
    self.widgets["description"].config(text=self.localization.get_text("description"))
    self.widgets["lock_button"].config(text=self.localization.get_text("lock_button"))
    self.widgets["exit_button"].config(text=self.localization.get_text("exit_button"))
    self.widgets["lock_step"].config(text=self.localization.get_text("step_lock"))
    self.widgets["clean_step"].config(text=self.localization.get_text("step_clean"))
    self.widgets["done_step"].config(text=self.localization.get_text("step_done"))

    unlock_combo = self._format_unlock_combo()
    unlock_info_text = self.localization.get_text("unlock_info_format").format(minutes=self.config.lock_duration_seconds // 60, combo=unlock_combo)
    self.widgets["unlock_info"].config(text=unlock_info_text)

  def _format_unlock_combo(self) -> str:
    return " + ".join(k.replace("_l", "").replace("_r", "").replace("shift", "Shift").replace("alt", "Alt").title() for k in self.config.unlock_sequence)

  def _start_locking_process(self):
    if self.is_locked:
      return

    self.is_locked = True
    self.countdown_seconds = self.config.lock_duration_seconds

    self.widgets["lock_button"].config(state=tk.DISABLED)
    self.widgets["exit_button"].config(state=tk.DISABLED)
    self.root.withdraw()

    self._create_lock_overlay()
    self._start_input_monitoring()
    self._start_countdown_timer()

  def _create_lock_overlay(self):
    self.overlay = LockOverlay(self.root, self.theme_manager, self.localization, self.image_manager, self._format_unlock_combo())
    self.overlay.create(self.countdown_seconds)

  def _start_input_monitoring(self):
    self.input_manager.start_listening(self._unlock_system_callback)
    self.input_manager.enable_input_suppression()

  def _start_countdown_timer(self):
    self.timer_thread = threading.Thread(target=self._countdown_worker, daemon=True)
    self.timer_thread.start()

  def _countdown_worker(self):
    while self.countdown_seconds > 0 and self.is_locked:
      time.sleep(1)
      if self.is_locked:
        self.countdown_seconds -= 1
        if self.overlay:
          self.overlay.update_countdown(self.countdown_seconds)

    if self.is_locked:
      self.root.after(0, self._unlock_system)

  def _unlock_system_callback(self):
    self.root.after(0, self._unlock_system)

  def _unlock_system(self):
    if not self.is_locked:
      return

    self.is_locked = False
    self.input_manager.disable_input_suppression()
    self.input_manager.stop_listening()

    if self.overlay:
      self.overlay.destroy()
      self.overlay = None

    self.root.deiconify()
    self.widgets["lock_button"].config(state=tk.NORMAL)
    self.widgets["exit_button"].config(state=tk.NORMAL)

  def _on_closing(self):
    if self.is_locked:
      messagebox.showwarning(
        self.localization.get_text("warning_locked"),
        self.localization.get_text("warning_locked_message"),
      )
      return

    self.input_manager.stop_listening()
    self.root.destroy()
    sys.exit(0)

  def run(self):
    self.root.mainloop()


def main():
  root = tk.Tk()
  app = CleanLockApp(root)
  app.theme_manager.apply_titlebar_theme(root)
  app.run()


if __name__ == "__main__":
  main()
