"""
אפליקציית ניתוח וחיפוש ניקוד - ממשק גרפי
Nikud Analysis and Search Application - GUI
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
from pathlib import Path
import json
from datetime import datetime
import threading
from typing import Dict, List, Optional

from nikud_analyzer import NikudAnalyzer
from search_engine import DatabaseManager, SearchEngine
from excel_exporter import ExcelExporter
from progress_dialog import ProgressDialog, ProgressRunner, BatchProcessor
from tehilim_loader import TehilimLoader


class NikudApp:
    """האפליקציה הראשית לניתוח וחיפוש ניקוד"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("מערכת ניתוח וחיפוש ניקוד")
        self.root.geometry("1200x800")

        # הגדרת כיוון RTL
        self.root.option_add('*Text.Font', 'Arial 10')
        self.root.option_add('*Entry.Font', 'Arial 10')

        # אתחול רכיבי המערכת
        self.analyzer = NikudAnalyzer()
        self.db = DatabaseManager("nikud_database.db")
        self.engine = SearchEngine(self.db, self.analyzer)
        self.exporter = ExcelExporter()

        # משתני מצב
        self.current_results = []
        self.selected_rules = []

        # בניית הממשק
        self.setup_gui()

        # טעינת כללי ניקוד אם קיים קובץ
        self.load_nikud_rules()

        # טעינת מילות תהילים אוטומטית אם קיים קובץ - אחרי שהחלון נטען
        self.root.after(1000, self.load_tehilim_if_exists)

    def setup_gui(self):
        """בניית ממשק המשתמש"""
        # יצירת תפריט
        self.create_menu()

        # יצירת הכרטיסיות
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # כרטיסיית טעינת טקסט
        self.create_load_tab()

        # כרטיסיית חיפוש
        self.create_search_tab()

        # כרטיסיית תוצאות
        self.create_results_tab()

        # כרטיסיית סטטיסטיקות
        self.create_stats_tab()

        # סרגל מצב
        self.create_status_bar()

    def create_menu(self):
        """יצירת תפריט ראשי"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # תפריט קובץ
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="קובץ", menu=file_menu)
        file_menu.add_command(label="טען טקסט", command=self.load_text_file)
        file_menu.add_command(label="טען כללי ניקוד", command=self.load_rules_file)
        file_menu.add_command(label="טען מילים מתהילים", command=self.load_tehilim_manually)
        file_menu.add_separator()
        file_menu.add_command(label="ייצא לאקסל", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="יציאה", command=self.root.quit)

        # תפריט עריכה
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="עריכה", menu=edit_menu)
        edit_menu.add_command(label="נקה חיפוש", command=self.clear_search)
        edit_menu.add_command(label="נקה תוצאות", command=self.clear_results)

        # תפריט עזרה
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="עזרה", menu=help_menu)
        help_menu.add_command(label="מדריך", command=self.show_help)
        help_menu.add_command(label="אודות", command=self.show_about)

    def create_load_tab(self):
        """יצירת כרטיסיית טעינת טקסט"""
        load_frame = ttk.Frame(self.notebook)
        self.notebook.add(load_frame, text="טעינת טקסט")

        # אזור בחירת מקור
        source_frame = ttk.LabelFrame(load_frame, text="בחר מקור טקסט")
        source_frame.pack(fill='x', padx=10, pady=10)

        ttk.Button(source_frame, text="טען מקובץ טקסט",
                  command=self.load_text_file).pack(side='right', padx=5, pady=5)
        ttk.Button(source_frame, text="טען מקובץ DOCX",
                  command=self.load_docx_file).pack(side='right', padx=5, pady=5)

        # אזור הזנת טקסט
        text_frame = ttk.LabelFrame(load_frame, text="או הזן טקסט ישירות")
        text_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.text_input = scrolledtext.ScrolledText(text_frame, height=15,
                                                    font=('Arial', 11), wrap=tk.WORD)
        self.text_input.pack(fill='both', expand=True, padx=5, pady=5)

        # אזור פרטי טקסט
        details_frame = ttk.LabelFrame(load_frame, text="פרטי הטקסט")
        details_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(details_frame, text="שם המקור:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.source_name_var = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.source_name_var, width=30).grid(
            row=0, column=1, padx=5, pady=5)

        ttk.Label(details_frame, text="קטגוריה:").grid(row=0, column=2, sticky='e', padx=5, pady=5)
        self.category_var = tk.StringVar()
        ttk.Entry(details_frame, textvariable=self.category_var, width=30).grid(
            row=0, column=3, padx=5, pady=5)

        # כפתור טעינה
        ttk.Button(load_frame, text="טען טקסט למערכת",
                  command=self.process_text, style='Accent.TButton').pack(pady=10)

    def create_search_tab(self):
        """יצירת כרטיסיית חיפוש"""
        search_frame = ttk.Frame(self.notebook)
        self.notebook.add(search_frame, text="חיפוש וסינון")

        # אזור חיפוש בסיסי
        basic_frame = ttk.LabelFrame(search_frame, text="חיפוש בסיסי")
        basic_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(basic_frame, text="מילה:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.search_word_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.search_word_var, width=20).grid(
            row=0, column=1, padx=5, pady=5)

        ttk.Label(basic_frame, text="מילה ללא ניקוד:").grid(row=0, column=2, sticky='e', padx=5, pady=5)
        self.search_plain_var = tk.StringVar()
        ttk.Entry(basic_frame, textvariable=self.search_plain_var, width=20).grid(
            row=0, column=3, padx=5, pady=5)

        # אזור סינון לפי כללים
        rules_frame = ttk.LabelFrame(search_frame, text="סינון לפי כללי ניקוד")
        rules_frame.pack(fill='both', expand=True, padx=10, pady=5)

        # יצירת notebook לקטגוריות כללים
        rules_notebook = ttk.Notebook(rules_frame)
        rules_notebook.pack(fill='both', expand=True, padx=5, pady=5)

        # כרטיסיית הברות
        self.create_syllable_filters(rules_notebook)

        # כרטיסיית סימני ניקוד
        self.create_nikud_filters(rules_notebook)

        # כרטיסיית שווא
        self.create_shva_filters(rules_notebook)

        # כרטיסיית מקרים מיוחדים
        self.create_special_filters(rules_notebook)

        # כפתור חיפוש
        ttk.Button(search_frame, text="בצע חיפוש",
                  command=self.perform_search, style='Accent.TButton').pack(pady=10)

    def create_syllable_filters(self, parent):
        """יצירת פילטרים להברות"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="הברות")

        # סוג הברה
        ttk.Label(frame, text="סוג הברה:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.syllable_type_var = tk.StringVar()
        syllable_combo = ttk.Combobox(frame, textvariable=self.syllable_type_var,
                                      values=["", "פתוחה", "סגורה", "לא ידוע"])
        syllable_combo.grid(row=0, column=1, padx=5, pady=5)

        # סיומות
        endings_frame = ttk.LabelFrame(frame, text="מסתיים ב")
        endings_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='ew')

        self.ending_vars = {}
        endings = ["א", "ה", "ה דגושה", "ע", "קמץ", "צירה י", "חיריק י", "מלאופום", "חולם", "ח ופתח"]
        for i, ending in enumerate(endings):
            var = tk.BooleanVar()
            self.ending_vars[ending] = var
            ttk.Checkbutton(endings_frame, text=ending, variable=var).grid(
                row=i//5, column=i%5, padx=5, pady=2, sticky='w')

    def create_nikud_filters(self, parent):
        """יצירת פילטרים לסימני ניקוד"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="סימני ניקוד")

        # מכיל
        contains_frame = ttk.LabelFrame(frame, text="מכיל")
        contains_frame.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')

        self.contains_vars = {}
        nikud_types = ["קמץ", "פתח", "צירה", "סגול", "חיריק", "שורוק", "חולם", "שווא"]
        for i, nikud in enumerate(nikud_types):
            var = tk.BooleanVar()
            self.contains_vars[nikud] = var
            ttk.Checkbutton(contains_frame, text=nikud, variable=var).grid(
                row=i//2, column=i%2, padx=5, pady=2, sticky='w')

        # לא מכיל
        not_contains_frame = ttk.LabelFrame(frame, text="לא מכיל")
        not_contains_frame.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')

        self.not_contains_vars = {}
        for i, nikud in enumerate(nikud_types):
            var = tk.BooleanVar()
            self.not_contains_vars[nikud] = var
            ttk.Checkbutton(not_contains_frame, text=nikud, variable=var).grid(
                row=i//2, column=i%2, padx=5, pady=2, sticky='w')

    def create_shva_filters(self, parent):
        """יצירת פילטרים לשווא"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="שווא")

        # יש/אין שווא
        ttk.Label(frame, text="שווא במילה:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        self.has_shva_var = tk.StringVar()
        shva_combo = ttk.Combobox(frame, textvariable=self.has_shva_var,
                                  values=["", "יש", "אין"])
        shva_combo.grid(row=0, column=1, padx=5, pady=5)

        # סוגי שווא
        shva_types_frame = ttk.LabelFrame(frame, text="סוגי שווא")
        shva_types_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='ew')

        self.shva_type_vars = {}
        shva_types = ["נע", "נח", "שני שווא נע", "שני שווא נח", "נע ונח"]
        for i, shva_type in enumerate(shva_types):
            var = tk.BooleanVar()
            self.shva_type_vars[shva_type] = var
            ttk.Checkbutton(shva_types_frame, text=shva_type, variable=var).grid(
                row=i//3, column=i%3, padx=5, pady=2, sticky='w')

    def create_special_filters(self, parent):
        """יצירת פילטרים למקרים מיוחדים"""
        frame = ttk.Frame(parent)
        parent.add(frame, text="מקרים מיוחדים")

        self.special_vars = {}
        special_cases = ["קמץ קטן", "פתח גנובה", "שני שוואים", "דגש"]
        for i, case in enumerate(special_cases):
            var = tk.BooleanVar()
            self.special_vars[case] = var
            ttk.Checkbutton(frame, text=case, variable=var).grid(
                row=i//2, column=i%2, padx=10, pady=5, sticky='w')

    def create_results_tab(self):
        """יצירת כרטיסיית תוצאות"""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="תוצאות")

        # סרגל כלים לתוצאות
        toolbar_frame = ttk.Frame(results_frame)
        toolbar_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(toolbar_frame, text="ייצא לאקסל",
                  command=self.export_results).pack(side='right', padx=5)
        ttk.Button(toolbar_frame, text="נקה תוצאות",
                  command=self.clear_results).pack(side='right', padx=5)

        self.results_count_label = ttk.Label(toolbar_frame, text="תוצאות: 0")
        self.results_count_label.pack(side='left', padx=5)

        # טבלת תוצאות
        self.create_results_table(results_frame)

    def create_results_table(self, parent):
        """יצירת טבלת התוצאות"""
        # יצירת frame עם scrollbar
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical")
        hsb = ttk.Scrollbar(table_frame, orient="horizontal")

        # Treeview
        columns = ('מילה', 'ללא ניקוד', 'סוג הברה', 'שווא', 'דגש', 'מקרים מיוחדים', 'מקור')
        self.results_tree = ttk.Treeview(table_frame, columns=columns,
                                         yscrollcommand=vsb.set,
                                         xscrollcommand=hsb.set, show='headings')

        vsb.config(command=self.results_tree.yview)
        hsb.config(command=self.results_tree.xview)

        # הגדרת עמודות
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=100)

        # פריסה
        self.results_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # אירוע לחיצה כפולה
        self.results_tree.bind('<Double-Button-1>', self.show_word_details)

    def create_stats_tab(self):
        """יצירת כרטיסיית סטטיסטיקות"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="סטטיסטיקות")

        # כפתור רענון
        ttk.Button(stats_frame, text="רענן סטטיסטיקות",
                  command=self.update_statistics).pack(pady=10)

        # אזור הצגת סטטיסטיקות
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=20,
                                                    font=('Courier', 10), wrap=tk.WORD)
        self.stats_text.pack(fill='both', expand=True, padx=10, pady=5)

    def create_status_bar(self):
        """יצירת סרגל מצב"""
        self.status_bar = ttk.Label(self.root, text="מוכן", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_nikud_rules(self):
        """טעינת כללי ניקוד מקובץ ברירת מחדל"""
        rules_file = Path("רשימה לסינון.xlsx")
        if rules_file.exists():
            try:
                self.db.load_rules_from_excel(str(rules_file))
                self.update_status("כללי ניקוד נטענו בהצלחה")
            except Exception as e:
                print(f"שגיאה בטעינת כללי ניקוד: {e}")

    def load_tehilim_if_exists(self):
        """טעינת מילות תהילים אוטומטית אם הקובץ קיים"""
        tehilim_file = Path("מילים מתהילים.xlsx")
        if tehilim_file.exists():
            try:
                # בדיקה אם כבר נטען
                cursor = self.db.conn.execute(
                    "SELECT COUNT(*) FROM sources WHERE name = 'ספר תהילים - מילים מנותחות'"
                )
                if cursor.fetchone()[0] == 0:
                    self.update_status("טוען מילים מתהילים...")
                    self.load_tehilim_file_with_progress()
            except Exception as e:
                print(f"שגיאה בטעינת תהילים: {e}")

    def load_tehilim_file_with_progress(self):
        """טעינת קובץ תהילים עם בר התקדמות"""
        def load_with_progress(progress: ProgressDialog):
            try:
                loader = TehilimLoader(self.db, self.analyzer)
                tehilim_file = "מילים מתהילים.xlsx"

                # טעינת המילים
                results = loader.load_tehilim_file(tehilim_file, progress)

                # טעינת כללים נוספים
                rules_count = loader.load_additional_rules(tehilim_file)
                if rules_count > 0:
                    progress.set_details(f"נטענו {rules_count} כללי ניקוד נוספים")

                return results
            except Exception as e:
                raise e

        try:
            # הרצה עם בר התקדמות
            results = ProgressRunner.run_with_progress(
                self.root,
                load_with_progress,
                "טעינת מילים מתהילים",
                "טוען 6,693 מילים מתהילים למסד נתונים..."
            )

            if results:
                self.update_status(
                    f"נטענו {results['loaded_words']} מילים מתהילים"
                )
                self.update_statistics()
                messagebox.showinfo(
                    "טעינת תהילים",
                    f"נטענו בהצלחה:\n"
                    f"• {results['loaded_words']} מילים\n"
                    f"• {len(results.get('new_rules', []))} כללים חדשים"
                )
        except Exception as e:
            print(f"שגיאה בטעינת תהילים: {e}")

    def load_tehilim_manually(self):
        """טעינת קובץ תהילים ידנית"""
        filename = filedialog.askopenfilename(
            title="בחר קובץ מילים מתהילים",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile="מילים מתהילים.xlsx"
        )
        if filename:
            def load_with_progress(progress: ProgressDialog):
                try:
                    loader = TehilimLoader(self.db, self.analyzer)
                    results = loader.load_tehilim_file(filename, progress)

                    # טעינת כללים נוספים
                    rules_count = loader.load_additional_rules(filename)
                    if rules_count > 0:
                        progress.set_details(f"נטענו {rules_count} כללי ניקוד נוספים")

                    return results
                except Exception as e:
                    raise e

            try:
                results = ProgressRunner.run_with_progress(
                    self.root,
                    load_with_progress,
                    "טעינת מילים מתהילים",
                    "טוען מילים מתהילים למסד נתונים..."
                )

                if results:
                    self.update_status(f"נטענו {results['loaded_words']} מילים מתהילים")
                    self.update_statistics()
                    messagebox.showinfo(
                        "טעינת תהילים",
                        f"נטענו בהצלחה:\n"
                        f"• {results['loaded_words']} מילים\n"
                        f"• דילגנו על {results['skipped']}\n"
                        f"• שגיאות: {results['errors']}\n"
                        f"• כללים חדשים: {len(results.get('new_rules', []))}"
                    )
            except Exception as e:
                messagebox.showerror("שגיאה", f"שגיאה בטעינת תהילים:\n{e}")

    def load_text_file(self):
        """טעינת קובץ טקסט"""
        filename = filedialog.askopenfilename(
            title="בחר קובץ טקסט",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    text = file.read()
                    self.text_input.delete('1.0', tk.END)
                    self.text_input.insert('1.0', text)
                    self.source_name_var.set(Path(filename).stem)
                    self.update_status(f"הקובץ {filename} נטען בהצלחה")
            except Exception as e:
                messagebox.showerror("שגיאה", f"לא ניתן לטעון את הקובץ:\n{e}")

    def load_docx_file(self):
        """טעינת קובץ DOCX"""
        try:
            import docx
            filename = filedialog.askopenfilename(
                title="בחר קובץ Word",
                filetypes=[("Word files", "*.docx"), ("All files", "*.*")]
            )
            if filename:
                doc = docx.Document(filename)
                text = '\n'.join([para.text for para in doc.paragraphs])
                self.text_input.delete('1.0', tk.END)
                self.text_input.insert('1.0', text)
                self.source_name_var.set(Path(filename).stem)
                self.update_status(f"הקובץ {filename} נטען בהצלחה")
        except ImportError:
            messagebox.showerror("שגיאה", "יש להתקין את הספריה python-docx")
        except Exception as e:
            messagebox.showerror("שגיאה", f"לא ניתן לטעון את הקובץ:\n{e}")

    def load_rules_file(self):
        """טעינת קובץ כללי ניקוד"""
        filename = filedialog.askopenfilename(
            title="בחר קובץ כללי ניקוד",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.db.load_rules_from_excel(filename)
                self.update_status(f"כללי ניקוד נטענו מ-{filename}")
                messagebox.showinfo("הצלחה", "כללי הניקוד נטענו בהצלחה")
            except Exception as e:
                messagebox.showerror("שגיאה", f"לא ניתן לטעון כללי ניקוד:\n{e}")

    def process_text(self):
        """עיבוד וטעינת טקסט למערכת עם בר התקדמות"""
        text = self.text_input.get('1.0', tk.END).strip()
        source_name = self.source_name_var.get() or "טקסט ללא שם"
        category = self.category_var.get()

        if not text:
            messagebox.showwarning("אזהרה", "אנא הזן טקסט לעיבוד")
            return

        def process_with_progress(progress: ProgressDialog):
            """עיבוד עם התקדמות"""
            try:
                # שלב 1: ניתוח טקסט
                progress.set_message("מנתח טקסט...")
                progress.update(10, "מפצל לרמת מילים...")

                # ניתוח המילים
                analyses = self.analyzer.analyze_text(text)
                total_words = len(analyses)
                progress.set_max(total_words + 20)  # +20 לשלבים נוספים

                # שלב 2: יצירת מקור במסד נתונים
                progress.update(15, "יוצר רשומת מקור במסד נתונים...")
                source_id = self.db.add_source(source_name, text)

                # שלב 3: הוספת קטגוריה
                category_id = None
                if category:
                    progress.update(20, "מוסיף קטגוריה...")
                    category_id = self.db.add_category(category)

                # שלב 4: שמירת המילים המנותחות
                sentences = text.split('.')  # פיצול למשפטים לצורך הקשר
                progress.set_message("שומר מילים במסד נתונים...")

                for i, analysis in enumerate(analyses):
                    if progress.is_cancelled:
                        self.db.conn.rollback()
                        return None

                    # עדכון התקדמות
                    progress.update(
                        20 + i,
                        f"שומר מילה {i+1} מתוך {total_words}",
                        f"{analysis.word} ({analysis.word_plain})"
                    )

                    # מציאת ההקשר
                    context = ""
                    for sentence in sentences:
                        if analysis.word in sentence:
                            context = sentence.strip()
                            break

                    # שמירה במסד
                    self.db.add_word(
                        analysis=analysis,
                        source_id=source_id,
                        position=i,
                        context=context,
                        category_id=category_id
                    )

                # שלב 5: סיום ושמירה
                progress.update(
                    total_words + 20,
                    "משלים את העיבוד...",
                    f"נשמרו {total_words} מילים"
                )
                self.db.conn.commit()

                return source_id

            except Exception as e:
                self.db.conn.rollback()
                raise e

        try:
            # הרצה עם בר התקדמות
            source_id = ProgressRunner.run_with_progress(
                self.root,
                process_with_progress,
                f"טוען טקסט: {source_name}",
                "מעבד ומנתח טקסט..."
            )

            if source_id:
                self.update_status(f"הטקסט נטען בהצלחה (מזהה: {source_id})")
                self.update_statistics()
                messagebox.showinfo("הצלחה", "הטקסט נטען ונותח בהצלחה")
            else:
                self.update_status("העיבוד בוטל")

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בעיבוד הטקסט:\n{e}")

    def perform_search(self):
        """ביצוע חיפוש עם בר התקדמות"""
        filters = self.build_filters()

        def search_with_progress(progress: ProgressDialog):
            """חיפוש עם התקדמות"""
            try:
                # שלב 1: בניית שאילתה
                progress.update(20, "בונה שאילתת חיפוש...")
                query, params = self.engine.build_query(filters)

                # שלב 2: ביצוע החיפוש
                progress.update(40, "מבצע חיפוש במסד נתונים...")
                cursor = self.engine.db.conn.execute(query, params)

                # שלב 3: עיבוד תוצאות
                progress.update(60, "מעבד תוצאות...")
                columns = [description[0] for description in cursor.description]
                results = []

                rows = cursor.fetchall()
                total_rows = len(rows)

                if total_rows > 0:
                    progress.set_max(total_rows)

                for i, row in enumerate(rows):
                    if progress.is_cancelled:
                        return []

                    progress.update(
                        i,
                        f"מעבד תוצאה {i+1} מתוך {total_rows}",
                        row[1] if len(row) > 1 else ""  # המילה
                    )

                    result = dict(zip(columns, row))
                    # פענוח JSON
                    if result.get('shva_types'):
                        result['shva_types'] = json.loads(result['shva_types'])
                    if result.get('nikud_marks'):
                        result['nikud_marks'] = json.loads(result['nikud_marks'])
                    if result.get('special_cases'):
                        result['special_cases'] = json.loads(result['special_cases'])
                    results.append(result)

                progress.update(total_rows, "החיפוש הושלם!", f"נמצאו {total_rows} תוצאות")
                return results

            except Exception as e:
                raise e

        try:
            # הרצה עם בר התקדמות
            results = ProgressRunner.run_with_progress(
                self.root,
                search_with_progress,
                "מבצע חיפוש",
                "מחפש במסד נתונים..."
            )

            if results is not None:
                self.display_results(results)
                self.update_status(f"נמצאו {len(results)} תוצאות")

        except Exception as e:
            messagebox.showerror("שגיאה", f"שגיאה בחיפוש:\n{e}")

    def build_filters(self) -> Dict:
        """בניית מילון סינונים מהממשק"""
        filters = {}

        # חיפוש בסיסי
        if self.search_word_var.get():
            filters['word'] = self.search_word_var.get()
        if self.search_plain_var.get():
            filters['word_plain'] = self.search_plain_var.get()

        # סוג הברה
        if self.syllable_type_var.get():
            filters['syllable_type'] = self.syllable_type_var.get()

        # שווא
        if self.has_shva_var.get() == "יש":
            filters['has_shva'] = True
        elif self.has_shva_var.get() == "אין":
            filters['has_shva'] = False

        # דגש
        if self.special_vars.get("דגש", tk.BooleanVar()).get():
            filters['has_dagesh'] = True

        return filters

    def display_results(self, results: List[Dict]):
        """הצגת תוצאות בטבלה"""
        # ניקוי הטבלה
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # הוספת התוצאות
        for result in results:
            values = (
                result.get('word', ''),
                result.get('word_plain', ''),
                result.get('syllable_type', ''),
                'כן' if result.get('has_shva') else 'לא',
                'כן' if result.get('has_dagesh') else 'לא',
                ', '.join(result.get('special_cases', [])),
                result.get('source_name', '')
            )
            self.results_tree.insert('', 'end', values=values)

        # עדכון מונה
        self.results_count_label.config(text=f"תוצאות: {len(results)}")
        self.current_results = results

        # מעבר לכרטיסיית תוצאות
        self.notebook.select(2)

    def show_word_details(self, event):
        """הצגת פרטי מילה בלחיצה כפולה"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            word = item['values'][0]

            # חיפוש הנתונים המלאים
            for result in self.current_results:
                if result.get('word') == word:
                    self.show_details_window(result)
                    break

    def show_details_window(self, word_data: Dict):
        """חלון פרטי מילה"""
        details_window = tk.Toplevel(self.root)
        details_window.title(f"פרטי המילה: {word_data.get('word')}")
        details_window.geometry("600x500")

        # יצירת טקסט עם פרטים
        text = scrolledtext.ScrolledText(details_window, font=('Arial', 10), wrap=tk.WORD)
        text.pack(fill='both', expand=True, padx=10, pady=10)

        details = f"""
מילה: {word_data.get('word')}
מילה ללא ניקוד: {word_data.get('word_plain')}
תבנית ניקוד: {word_data.get('nikud_pattern')}
סוג הברה: {word_data.get('syllable_type')}
יש שווא: {'כן' if word_data.get('has_shva') else 'לא'}
סוגי שווא: {', '.join(word_data.get('shva_types', []))}
סימני ניקוד: {', '.join(word_data.get('nikud_marks', []))}
יש דגש: {'כן' if word_data.get('has_dagesh') else 'לא'}
הברה פתוחה: {'כן' if word_data.get('has_open_syllable') else 'לא'}
הברה סגורה: {'כן' if word_data.get('has_closed_syllable') else 'לא'}
מקרים מיוחדים: {', '.join(word_data.get('special_cases', []))}
הקשר: {word_data.get('context', '')}
מקור: {word_data.get('source_name', '')}
קטגוריה: {word_data.get('category_name', '')}
מיקום: {word_data.get('position', 0)}
"""
        text.insert('1.0', details)
        text.config(state='disabled')

    def export_results(self):
        """ייצוא תוצאות לאקסל עם בר התקדמות"""
        if not self.current_results:
            messagebox.showwarning("אזהרה", "אין תוצאות לייצוא")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=f"תוצאות_ניקוד_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )

        if filename:
            def export_with_progress(progress: ProgressDialog):
                """ייצוא עם התקדמות"""
                try:
                    progress.set_max(100)

                    # שלב 1: הכנת הנתונים
                    progress.update(10, "מכין נתונים לייצוא...")
                    df = self.exporter.prepare_dataframe(self.current_results)

                    # שלב 2: יצירת קובץ אקסל
                    progress.update(30, "יוצר קובץ אקסל...")
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        # גיליון תוצאות
                        progress.update(40, "כותב גיליון תוצאות...")
                        df.to_excel(writer, sheet_name='תוצאות חיפוש', index=False)

                        # עיצוב
                        progress.update(50, "מעצב את הגיליון...")
                        workbook = writer.book
                        worksheet = writer.sheets['תוצאות חיפוש']
                        self.exporter.format_worksheet(worksheet, df, True)

                        # גיליון סטטיסטיקות
                        progress.update(60, "יוצר גיליון סטטיסטיקות...")
                        self.exporter.add_statistics_sheet(workbook, df)

                        # טבלת Pivot
                        progress.update(70, "יוצר טבלת Pivot...")
                        self.exporter.add_pivot_sheet(workbook, df)

                        # גיליון הסברים
                        progress.update(80, "מוסיף גיליון הסברים...")
                        self.exporter.add_info_sheet(workbook)

                        # שמירה
                        progress.update(90, "שומר קובץ...")

                    progress.update(100, "הייצוא הושלם!", f"נשמר ב: {filename}")
                    return filename

                except Exception as e:
                    raise e

            try:
                # הרצה עם בר התקדמות
                result = ProgressRunner.run_with_progress(
                    self.root,
                    export_with_progress,
                    "ייצוא לאקסל",
                    f"מייצא {len(self.current_results)} תוצאות..."
                )

                if result:
                    self.update_status(f"התוצאות יוצאו ל-{filename}")
                    messagebox.showinfo("הצלחה", f"הקובץ נשמר בהצלחה:\n{filename}")

            except Exception as e:
                messagebox.showerror("שגיאה", f"שגיאה בייצוא:\n{e}")

    def clear_search(self):
        """ניקוי שדות החיפוש"""
        self.search_word_var.set("")
        self.search_plain_var.set("")
        self.syllable_type_var.set("")
        self.has_shva_var.set("")

        # ניקוי checkbox-ים
        for var_dict in [self.ending_vars, self.contains_vars,
                        self.not_contains_vars, self.shva_type_vars,
                        self.special_vars]:
            for var in var_dict.values():
                var.set(False)

        self.update_status("שדות החיפוש נוקו")

    def clear_results(self):
        """ניקוי תוצאות"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        self.current_results = []
        self.results_count_label.config(text="תוצאות: 0")
        self.update_status("התוצאות נוקו")

    def update_statistics(self):
        """עדכון סטטיסטיקות"""
        try:
            stats = self.engine.get_statistics()
            stats_text = f"""
========================================
           סטטיסטיקות המערכת
========================================

סך הכל מילים במסד: {stats.get('total_words', 0)}
מילים ייחודיות: {stats.get('unique_words', 0)}

התפלגות סוגי הברות:
"""
            for syllable_type, count in stats.get('syllable_distribution', {}).items():
                stats_text += f"  {syllable_type}: {count}\n"

            stats_text += f"""
מילים עם שווא: {stats.get('words_with_shva', 0)}
מילים עם דגש: {stats.get('words_with_dagesh', 0)}

מספר מקורות: {stats.get('total_sources', 0)}
מספר קטגוריות: {stats.get('total_categories', 0)}

עדכון אחרון: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self.stats_text.delete('1.0', tk.END)
            self.stats_text.insert('1.0', stats_text)
        except Exception as e:
            print(f"שגיאה בעדכון סטטיסטיקות: {e}")

    def update_status(self, message: str):
        """עדכון סרגל המצב"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()

    def show_help(self):
        """הצגת עזרה"""
        help_text = """
מערכת ניתוח וחיפוש ניקוד
========================

1. טעינת טקסט:
   - טען קובץ טקסט או DOCX
   - או הזן/הדבק טקסט ישירות
   - ציין שם מקור וקטגוריה (אופציונלי)
   - לחץ "טען טקסט למערכת"

2. חיפוש וסינון:
   - השתמש בחיפוש בסיסי למציאת מילים
   - בחר כללי סינון מהכרטיסיות
   - ניתן לשלב מספר כללים
   - לחץ "בצע חיפוש"

3. תוצאות:
   - צפה בתוצאות בטבלה
   - לחץ פעמיים על מילה לפרטים מלאים
   - ייצא לאקסל לעיבוד נוסף

4. סטטיסטיקות:
   - צפה בנתונים על המסד
   - לחץ "רענן" לעדכון
"""
        messagebox.showinfo("עזרה", help_text)

    def show_about(self):
        """הצגת אודות"""
        about_text = """
מערכת ניתוח וחיפוש ניקוד
גרסה 1.0

פותח עבור ניתוח טקסטים עבריים
עם דגש על כללי ניקוד מורכבים

© 2024
"""
        messagebox.showinfo("אודות", about_text)

    def run(self):
        """הפעלת האפליקציה"""
        self.update_statistics()
        self.root.mainloop()


def main():
    """נקודת הכניסה הראשית"""
    app = NikudApp()
    app.run()


if __name__ == "__main__":
    main()