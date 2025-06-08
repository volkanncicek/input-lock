import locale

DEFAULT_LANGUAGE = "english"


TRANSLATIONS = {
  "english": {
    "app_title": "Clean Lock",
    "title": "Clean Lock",
    "description": "Temporarily disable input devices like the keyboard, mouse, and touchpad, allowing you to\nsafely clean your computer and accessories without accidental input.",
    "lock_button": "Lock",
    "exit_button": "Exit",
    "warning_locked": "Locked",
    "warning_locked_message": "Cannot perform this action while the system is locked.",
    "locked_message": "Press the configured key combination to unlock.",
    "locked_detailed_message": "Your computer and all connected devices are locked for {minutes} minutes.\nYou can begin to clean your computer.\nDo not disconnect any connected devices.\nTo exit at any time, press {combo}",
    "step_lock": "Lock",
    "step_clean": "Clean",
    "step_done": "Done",
    "unlock_info_format": "Unlocks after {minutes} mins or with\n{combo}",
  },
  "turkish": {
    "app_title": "Clean Lock",
    "title": "Clean Lock",
    "description": "Bilgisayarınızı ve aksesuarlarınızı yanlışlıkla girdi olmadan güvenli bir şekilde temizlemenize\nolanak tanımak için klavye, fare ve dokunmatik yüzey gibi giriş aygıtlarını geçici olarak devre dışı bırakın.",
    "lock_button": "Kilitle",
    "exit_button": "Çıkış",
    "warning_locked": "Kilitli",
    "warning_locked_message": "Sistem kilitliyken bu işlem yapılamaz.",
    "locked_message": "Kilidi açmak için ayarlanmış tuş kombinasyonuna basın.",
    "locked_detailed_message": "Bilgisayarınız ve tüm bağlı cihazlar {minutes} dakika boyunca kilitlendi.\nBilgisayarınızı temizlemeye başlayabilirsiniz.\nBağlı cihazların bağlantısını kesmeyin.\nİstediğiniz zaman çıkmak için {combo} tuşlarına basın",
    "step_lock": "Kilitle",
    "step_clean": "Temizle",
    "step_done": "Bitti",
    "unlock_info_format": "{minutes} dakika sonra veya\n{combo} ile açılır",
  },
}


def detect_system_language() -> str:
  """Detects the system language and returns supported language code."""
  try:
    system_locale = locale.getlocale()[0]
    if system_locale:
      # Extract language code (e.g., 'tr_TR' -> 'tr')
      lang_code = system_locale.split("_")[0].lower()
      # Return if supported, otherwise fallback to default
      return lang_code if lang_code in TRANSLATIONS else DEFAULT_LANGUAGE
  except Exception:
    pass
  return DEFAULT_LANGUAGE
