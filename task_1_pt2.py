import tkinter as tk  # Основная библиотека для GUI
from tkinter.scrolledtext import ScrolledText  # Текстовое поле с прокруткой
import os  # Для работы с файловой системой
import sys  # Для работы с аргументами командной строки


class VFSEmulator:
    def __init__(self, root, vfs_path=None, script_path=None):
        self.root = root
        self.root.title("finikato.OS(VFS)")
        self.root.configure(background="#7366BD")
        self.root.geometry("800x600")

        # Важно: устанавливаем текущую директорию как директорию программы
        self.program_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(self.program_dir)  # Меняем текущую рабочую директорию

        # Устанавливаем параметры, преобразуя пути в абсолютные
        self.vfs_path = os.path.abspath(vfs_path) if vfs_path else self.program_dir
        self.prompt = "VFS> "  # Фиксированное приглашение
        self.script_path = os.path.abspath(script_path) if script_path else None
        self.is_running = False  # Флаг состояния эмулятора

        # Создаем интерфейс в новом стиле
        self.create_gui()

        # Показываем диагностическую информацию о путях
        self.write_output(f"Программа запущена из: {self.program_dir}")
        self.write_output(f"Текущая рабочая директория: {os.getcwd()}")

        # Проверяем и показываем статус скрипта
        if self.script_path:
            exists = "НАЙДЕН" if os.path.exists(self.script_path) else "НЕ НАЙДЕН"
            self.write_output(f"Путь к скрипту: {self.script_path} ({exists})")

        # Инструкция по использованию
        self.write_output("\nКоманды: set vfs_path|script_path <значение>, start, exit")
        self.write_output("=" * 50)

        # Автозапуск, если указан скрипт и он существует
        if self.script_path and os.path.exists(self.script_path):
            self.root.after(100, self.start_emulator)  # Задержка для инициализации GUI

    def create_gui(self):
        """Создание графического интерфейса в новом стиле"""
        # Заголовок
        create = tk.Label(self.root, text="Меню Пользователя:", background="#FFFFFF",
                          font=("Comic Sans MS", 16))
        create.grid(column=0, row=0, padx=10, pady=10, columnspan=2)

        # Текстовое поле для вывода с прокруткой
        text_frame = tk.Frame(self.root)
        text_frame.grid(column=0, row=1, columnspan=2, padx=10, pady=10, sticky="nsew")

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Прокрутка
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Текстовое поле вывода
        self.output_area = tk.Text(text_frame, width=70, height=20, background="white",
                                   font=("Consolas", 10), yscrollcommand=scrollbar.set)
        self.output_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Связываем скроллбар с текстовым полем
        scrollbar.config(command=self.output_area.yview)

        # Начальное сообщение
        self.output_area.insert(tk.END, "Добро пожаловать в finikato.OS\nВведите команду\n")
        self.output_area.configure(state='disabled')

        # Поле ввода и кнопка
        input_frame = tk.Frame(self.root, background="#7366BD")
        input_frame.grid(column=0, row=2, columnspan=2, padx=10, pady=10)

        # Поле ввода
        self.entry = tk.Entry(input_frame, width=50, font=("Arial", 12))
        self.entry.pack(side=tk.LEFT, padx=5)
        self.entry.bind("<Return>", self.process_command)
        self.entry.focus()

        # Кнопка ввода
        self.btn = tk.Button(input_frame, text="Ввод", command=self.process_command,
                             font=("Comic Sans MS", 12), background="#4CAF50")
        self.btn.pack(side=tk.LEFT, padx=5)

        # Кнопки для быстрого доступа
        button_frame = tk.Frame(self.root, background="#7366BD")
        button_frame.grid(column=0, row=3, columnspan=2, pady=5)

        btn_clear = tk.Button(button_frame, text="Очистить вывод", command=self.clear_output,
                              font=("Comic Sans MS", 10), background="#FF5722")
        btn_clear.pack(side=tk.LEFT, padx=5)

    def write_output(self, text):
        """Вывод текста в область вывода с автоматической прокруткой"""
        self.output_area.configure(state='normal')
        self.output_area.insert(tk.END, text + "\n")
        self.output_area.see(tk.END)  # Автопрокрутка к новому тексту
        self.output_area.configure(state='disabled')  # Блокируем редактирование

    def clear_output(self):
        """Очистка текстового поля вывода"""
        self.output_area.configure(state='normal')
        self.output_area.delete(1.0, tk.END)
        self.output_area.insert(tk.END, "Введите команду\n")
        self.output_area.see(tk.END)
        self.output_area.configure(state='disabled')

    def process_command(self, event=None):
        """Обработка команд пользователя из поля ввода"""
        command = self.entry.get().strip()
        self.entry.delete(0, tk.END)  # Очищаем поле ввода

        if not command:
            return

        # Форматируем вывод в зависимости от режима (эмулятор/настройка)
        if self.is_running:
            self.write_output(f"{self.prompt}{command}")
        else:
            self.write_output(f"> {command}")

        # Простой split без учета кавычек
        parts = command.split()
        
        if not parts:
            return

        cmd = parts[0].lower()
        args = parts[1:]

        # Обработка команд в зависимости от режима работы
        if self.is_running:
            # Режим эмулятора VFS
            if cmd == "exit":
                self.is_running = False
                self.write_output("Эмулятор остановлен.")
            elif cmd == "ls":
                # Объединяем аргументы для поддержки путей с пробелами
                target = ' '.join(args) if args else self.current_dir
                self.write_output(f"Содержимое: {target}")
            elif cmd == "cd":
                # Объединяем аргументы для поддержки путей с пробелами
                target = ' '.join(args) if args else 'HOME'
                self.write_output(f"Смена директории: {target}")
            else:
                self.write_output(f"Неизвестная команда: {cmd}")
        else:
            # Режим настройки параметров
            if cmd == "set":
                self.process_set_command(args)
            elif cmd == "start":
                self.start_emulator()
            elif cmd == "exit":
                self.root.destroy()  # Завершение программы
            else:
                self.write_output(f"Неизвестная команда: {cmd}")

    def process_set_command(self, args):
        """Обработка команды set для установки параметров"""
        if len(args) < 2:
            self.write_output("Ошибка: команда set требует два аргумента")
            return

        # Берем первый аргумент как параметр
        param = args[0].lower()
        
        # Объединяем все остальные аргументы в значение (для поддержки путей с пробелами)
        value = ' '.join(args[1:])
        
        # Удаляем кавычки если они есть
        value = value.strip('"\'')

        # Установка разных параметров
        if param == "vfs_path":
            self.vfs_path = os.path.abspath(value)  # Преобразуем в абсолютный путь
            self.write_output(f"Путь к VFS установлен: {self.vfs_path}")
        elif param == "script_path":
            self.script_path = os.path.abspath(value)  # Преобразуем в абсолютный путь
            exists = "НАЙДЕН" if os.path.exists(self.script_path) else "НЕ НАЙДЕН"
            self.write_output(f"Путь к скрипту установлен: {self.script_path} ({exists})")
        else:
            self.write_output(f"Неизвестный параметра: {param}")

    def start_emulator(self):
        """Запуск эмулятора VFS"""
        self.write_output("=" * 50)
        self.write_output("ЗАПУСК ЭМУЛЯТОРА VFS")
        self.write_output("=" * 50)

        self.is_running = True
        self.current_dir = "/"  # Начальная директория эмулятора

        # Если указан скрипт и он существует - выполняем его
        if self.script_path and os.path.exists(self.script_path):
            self.execute_script()
        elif self.script_path:
            self.write_output(f"ОШИБКА: Скрипт не найден: {self.script_path}")

        self.write_output("Эмулятор запущен. Введите команды VFS или 'exit'.")

    def execute_script(self):
        """Выполнение скрипта команд"""
        self.write_output(f"ВЫПОЛНЕНИЕ СКРИПТА: {self.script_path}")

        try:
            # Открываем файл скрипта для чтения
            with open(self.script_path, 'r') as f:
                # Читаем и выполняем команды построчно
                for line_num, line in enumerate(f, 1):
                    line = line.strip()  # Убираем лишние пробелы

                    # Пропускаем пустые строки и комментарии
                    if not line or line.startswith('#'):
                        continue

                    # Показываем команду с приглашением (имитация ввода пользователя)
                    self.write_output(f"{self.prompt}{line}")

                    # Простой split без учета кавычек
                    parts = line.split()
                    
                    if not parts:
                        continue

                    cmd = parts[0].lower()
                    args = parts[1:]

                    # Обработка команд эмулятора
                    if cmd == "exit":
                        self.write_output("Завершение работы...")
                        self.is_running = False
                        break
                    elif cmd == "ls":
                        # Объединяем аргументы для поддержки путей с пробелами
                        target = ' '.join(args) if args else self.current_dir
                        self.write_output(f"Содержимое: {target}")
                    elif cmd == "cd":
                        # Объединяем аргументы для поддержки путей с пробелами
                        target = ' '.join(args) if args else 'HOME'
                        self.write_output(f"Смена директории: {target}")
                    else:
                        self.write_output(f"Неизвестная команда: {cmd}")
        except Exception as e:
            # Обработка ошибок при чтении/выполнении скрипта
            self.write_output(f"ОШИБКА ЧТЕНИЯ СКРИПТА: {e}")

        self.write_output("ВЫПОЛНЕНИЕ СКРИПТА ЗАВЕРШЕНО")


# Главная функция программы
def main():
    # Инициализируем переменные для хранения путей как None
    vfs_path, script_path = None, None

    # Начинаем обработку аргументов командной строки с индекса 1 (индекс 0 - имя скрипта)
    i = 1
    # Проходим по всем аргументам командной строки
    while i < len(sys.argv):
        # Проверяем текущий аргумент как --vfs_path и наличие следующего аргумента
        if sys.argv[i] == "--vfs_path" and i + 1 < len(sys.argv):
            # Сохраняем следующий аргумент как путь к VFS
            vfs_path = sys.argv[i + 1]
            # Переходим через два аргумента (текущий и значение)
            i += 2
        # Проверяем текущий аргумент как --script_path и наличие следующего аргумента
        elif sys.argv[i] == "--script_path" and i + 1 < len(sys.argv):
            # Сохраняем следующий аргумент как путь к скрипту
            script_path = sys.argv[i + 1]
            # Переходим через два аргумента (текущий и значение)
            i += 2
        else:
            # Если аргумент не распознан, переходим к следующему
            i += 1

    # Создаем главное окно приложения
    root = tk.Tk()
    # Создаем экземпляр эмулятора VFS, передавая пути и главное окно
    app = VFSEmulator(root, vfs_path, script_path)
    # Запускаем главный цикл обработки событий GUI
    root.mainloop()

# Проверяем, запущен ли скрипт напрямую (а не импортирован как модуль)
if __name__ == "__main__":
    # Если скрипт запущен напрямую, вызываем главную функцию
    main()
