import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
from utils.excel_utils import get_columns, read_excel, write_excel
from translators.google_translator import GoogleTranslator
from translators.openai_translator import OpenAITranslator
import threading
from queue import Queue

LANGUAGES = {
    "英文": "en",
    "日文": "ja",
    "德文": "de",
    "法文": "fr",
    "中文": "zh-cn"
}

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel多语言翻译工具")

        self.file_path = ""
        self.output_dir = ""
        self.columns = []
        self.column_vars = {}

        self.task_queue = Queue()
        self.progress_queue = Queue()

        # 文件选择
        tk.Button(root, text="选择Excel文件", command=self.choose_file).pack(pady=5)
        self.file_label = tk.Label(root, text="未选择文件")
        self.file_label.pack()

        # 列选择区域
        self.column_frame = tk.LabelFrame(root, text="选择需要翻译的列")
        self.column_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 全选 / 全不选 按钮
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="全选列", command=self.select_all_columns).pack(side="left", padx=5)
        tk.Button(btn_frame, text="全不选列", command=self.deselect_all_columns).pack(side="left", padx=5)

        # 语言选择
        tk.Label(root, text="选择翻译语言（多选）").pack()
        self.lang_listbox = tk.Listbox(root, selectmode=tk.MULTIPLE)
        for lang in LANGUAGES.keys():
            self.lang_listbox.insert(tk.END, lang)
        self.lang_listbox.pack()

        # 翻译插件选择
        tk.Label(root, text="选择翻译插件").pack()
        self.plugin_var = tk.StringVar(value="Google")
        self.plugin_menu = ttk.Combobox(root, textvariable=self.plugin_var, values=["Google", "OpenAI"])
        self.plugin_menu.pack()

        # 输出文件夹选择
        tk.Button(root, text="选择导出文件夹", command=self.choose_output_dir).pack(pady=5)
        self.output_label = tk.Label(root, text="未选择文件夹")
        self.output_label.pack()

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=10, pady=10)
        self.progress_label = tk.Label(root, text="")
        self.progress_label.pack()

        # 开始翻译按钮
        tk.Button(root, text="开始翻译", command=self.start_translation_thread).pack(pady=10)

        # GUI 定时更新
        self.root.after(100, self.update_progress)

    # 文件选择
    def choose_file(self):
        self.file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if self.file_path:
            self.file_label.config(text=os.path.basename(self.file_path))
            self.load_columns()

    # 加载列并去掉全空列
    def load_columns(self):
        all_columns, data = read_excel(self.file_path)
        non_empty_columns = [col for col in all_columns if any(row[col] not in (None, "") for row in data)]
        self.columns = non_empty_columns

        # 清空旧的列勾选框
        for widget in self.column_frame.winfo_children():
            widget.destroy()

        self.column_vars = {}
        for col in self.columns:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.column_frame, text=col, variable=var)
            chk.pack(anchor='w')
            self.column_vars[col] = var

    # 全选 / 全不选
    def select_all_columns(self):
        for var in self.column_vars.values():
            var.set(True)

    def deselect_all_columns(self):
        for var in self.column_vars.values():
            var.set(False)

    # 输出文件夹选择
    def choose_output_dir(self):
        self.output_dir = filedialog.askdirectory()
        if self.output_dir:
            self.output_label.config(text=self.output_dir)

    # 启动线程
    def start_translation_thread(self):
        threading.Thread(target=self.translate_file, daemon=True).start()

    # 翻译逻辑（线程安全）
    def translate_file(self):
        if not self.file_path or not self.output_dir:
            self.progress_queue.put(("error", "请先选择文件和导出文件夹"))
            return

        # 获取选中列
        selected_columns = [col for col, var in self.column_vars.items() if var.get()]
        if not selected_columns:
            self.progress_queue.put(("error", "请至少选择一列进行翻译"))
            return

        # 获取选中语言
        selected_indices = self.lang_listbox.curselection()
        if not selected_indices:
            self.progress_queue.put(("error", "请至少选择一种语言"))
            return
        selected_languages = [self.lang_listbox.get(i) for i in selected_indices]

        # 初始化翻译插件
        plugin_choice = self.plugin_var.get()
        if plugin_choice == "Google":
            translator = GoogleTranslator()
        else:
            api_key = simpledialog.askstring("OpenAI API Key", "请输入OpenAI API Key")
            if not api_key:
                self.progress_queue.put(("error", "必须输入OpenAI API Key"))
                return
            translator = OpenAITranslator(api_key=api_key)

        _, data = read_excel(self.file_path)
        total_tasks = len(selected_languages) * len(data)
        completed_tasks = 0

        for lang_name in selected_languages:
            lang_code = LANGUAGES[lang_name]
            translated_data = []
            for row in data:
                new_row = {}
                for col, val in row.items():
                    if col in selected_columns:
                        val_str = "" if val is None else str(val)
                        new_row[col] = translator.translate(val_str, lang_code)
                    else:
                        new_row[col] = val
                translated_data.append(new_row)

                # 更新进度队列
                completed_tasks += 1
                progress = completed_tasks / total_tasks * 100
                self.progress_queue.put(("progress", progress, completed_tasks, total_tasks))

            # 保存 Excel
            output_file = os.path.join(
                self.output_dir,
                f"{os.path.splitext(os.path.basename(self.file_path))[0]}_{lang_code}.xlsx"
            )
            write_excel(translated_data, output_file)

        self.progress_queue.put(("done", "翻译完成！"))

    # GUI 定时更新函数
    def update_progress(self):
        try:
            while True:
                item = self.progress_queue.get_nowait()
                if item[0] == "progress":
                    _, progress, completed, total = item
                    self.progress_var.set(progress)
                    self.progress_label.config(text=f"翻译进度: {completed}/{total}")
                elif item[0] == "error":
                    _, msg = item
                    messagebox.showerror("错误", msg)
                elif item[0] == "done":
                    _, msg = item
                    self.progress_var.set(100)
                    self.progress_label.config(text=msg)
                    messagebox.showinfo("完成", msg)
        except:
            pass
        self.root.after(100, self.update_progress)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("700x650")
    app = TranslatorApp(root)
    root.mainloop()
