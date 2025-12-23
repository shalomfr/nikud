"""
חלון התקדמות עם אחוזים אמיתיים
Progress Dialog with Real Percentage
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import Callable, Optional, Any


class ProgressDialog:
    """חלון התקדמות מתקדם עם אחוזים אמיתיים"""

    def __init__(self, parent, title="מעבד...", message="אנא המתן..."):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)

        # מרכז החלון
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # משתנים
        self.current_value = 0
        self.max_value = 100
        self.is_cancelled = False
        self.start_time = time.time()

        self.setup_ui(message)
        self.center_window()

    def setup_ui(self, message):
        """בניית ממשק החלון"""
        # כותרת
        self.message_label = ttk.Label(self.dialog, text=message, font=('Arial', 11))
        self.message_label.pack(pady=(20, 10))

        # תווית אחוזים
        self.percent_label = ttk.Label(self.dialog, text="0%", font=('Arial', 14, 'bold'))
        self.percent_label.pack(pady=5)

        # בר התקדמות
        self.progress_bar = ttk.Progressbar(
            self.dialog,
            mode='determinate',
            length=350,
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(pady=10)

        # תווית פרטים
        self.details_label = ttk.Label(self.dialog, text="", font=('Arial', 9))
        self.details_label.pack(pady=5)

        # תווית זמן
        self.time_label = ttk.Label(self.dialog, text="זמן שחלף: 0:00", font=('Arial', 9))
        self.time_label.pack(pady=5)

        # כפתור ביטול
        self.cancel_button = ttk.Button(
            self.dialog,
            text="ביטול",
            command=self.cancel
        )
        self.cancel_button.pack(pady=(10, 20))

        # עיצוב הבר
        style = ttk.Style()
        style.configure(
            "Custom.Horizontal.TProgressbar",
            thickness=25,
            troughcolor='#E0E0E0',
            background='#4CAF50'
        )

    def center_window(self):
        """מרכוז החלון"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def set_max(self, max_value: int):
        """הגדרת הערך המקסימלי"""
        self.max_value = max(1, max_value)
        self.progress_bar['maximum'] = self.max_value

    def update(self, value: int, message: Optional[str] = None, details: Optional[str] = None):
        """עדכון ההתקדמות"""
        if self.is_cancelled:
            return False

        self.current_value = min(value, self.max_value)
        self.progress_bar['value'] = self.current_value

        # חישוב אחוזים
        percent = int((self.current_value / self.max_value) * 100)
        self.percent_label.config(text=f"{percent}%")

        # עדכון הודעה
        if message:
            self.message_label.config(text=message)

        # עדכון פרטים
        if details:
            self.details_label.config(text=details)
        else:
            self.details_label.config(text=f"{self.current_value} מתוך {self.max_value}")

        # עדכון זמן
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.time_label.config(text=f"זמן שחלף: {minutes}:{seconds:02d}")

        # עדכון הצבע לפי התקדמות
        if percent < 33:
            color = '#f44336'  # אדום
        elif percent < 66:
            color = '#FF9800'  # כתום
        else:
            color = '#4CAF50'  # ירוק

        style = ttk.Style()
        style.configure("Custom.Horizontal.TProgressbar", background=color)

        # עדכון הממשק
        self.dialog.update()

        return not self.is_cancelled

    def increment(self, amount: int = 1, message: Optional[str] = None):
        """הוספה להתקדמות"""
        return self.update(self.current_value + amount, message)

    def set_message(self, message: str):
        """עדכון ההודעה"""
        self.message_label.config(text=message)
        self.dialog.update()

    def set_details(self, details: str):
        """עדכון הפרטים"""
        self.details_label.config(text=details)
        self.dialog.update()

    def cancel(self):
        """ביטול הפעולה"""
        self.is_cancelled = True
        self.cancel_button.config(state='disabled')
        self.set_message("מבטל...")

    def close(self):
        """סגירת החלון"""
        try:
            self.dialog.destroy()
        except:
            pass

    def pulse(self):
        """מצב פעימה (כשלא יודעים את הכמות)"""
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(10)

    def stop_pulse(self):
        """עצירת הפעימה"""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')


class ProgressRunner:
    """מריץ פעולות עם בר התקדמות"""

    @staticmethod
    def run_with_progress(parent, func: Callable, title: str = "מעבד...",
                          message: str = "אנא המתן...", *args, **kwargs) -> Any:
        """הרצת פונקציה עם בר התקדמות"""
        result = [None]
        error = [None]

        def worker():
            try:
                result[0] = func(progress, *args, **kwargs)
            except Exception as e:
                error[0] = e
            finally:
                parent.after(0, progress.close)

        progress = ProgressDialog(parent, title, message)
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()

        # המתנה לסיום
        parent.wait_window(progress.dialog)

        if error[0]:
            raise error[0]

        return result[0]


class BatchProcessor:
    """מעבד אצווה עם התקדמות מפורטת"""

    def __init__(self, progress_dialog: ProgressDialog):
        self.progress = progress_dialog
        self.cancelled = False

    def process_items(self, items: list, process_func: Callable,
                     item_name: str = "פריט") -> list:
        """עיבוד רשימת פריטים עם התקדמות"""
        results = []
        total = len(items)
        self.progress.set_max(total)

        for i, item in enumerate(items):
            if self.progress.is_cancelled:
                self.cancelled = True
                break

            # עדכון התקדמות
            self.progress.update(
                i,
                f"מעבד {item_name} {i+1} מתוך {total}",
                str(item)[:50] if item else ""
            )

            # עיבוד הפריט
            try:
                result = process_func(item)
                results.append(result)
            except Exception as e:
                print(f"שגיאה בעיבוד {item}: {e}")
                results.append(None)

        # סיום
        if not self.cancelled:
            self.progress.update(total, "הושלם!", f"עובדו {total} {item_name}ים")

        return results


# דוגמה לשימוש
if __name__ == "__main__":
    root = tk.Tk()
    root.title("בדיקת בר התקדמות")
    root.geometry("300x150")

    def long_task(progress: ProgressDialog):
        """משימה ארוכה לדוגמה"""
        items = list(range(100))
        progress.set_max(len(items))

        for i, item in enumerate(items):
            if progress.is_cancelled:
                break

            # סימולציה של עבודה
            time.sleep(0.05)

            # עדכון התקדמות
            progress.update(
                i + 1,
                f"מעבד פריט {i+1}",
                f"ערך: {item}"
            )

        return "הושלם!"

    def run_task():
        try:
            result = ProgressRunner.run_with_progress(
                root,
                long_task,
                "עיבוד נתונים",
                "מעבד 100 פריטים..."
            )
            tk.messagebox.showinfo("הושלם", f"תוצאה: {result}")
        except Exception as e:
            tk.messagebox.showerror("שגיאה", str(e))

    ttk.Button(root, text="הפעל משימה ארוכה", command=run_task).pack(pady=50)

    root.mainloop()