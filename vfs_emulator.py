import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import os
import sys
import hashlib
import xml.etree.ElementTree as ET
import base64


class VFS:
    def __init__(self):
        self.files = {}  #словарь для хранения файлов {путь: содержимое}
        self.root = "/"  #корневая директория vfs
        self.name = ""  #имя vfs из xml
        self.sha256_hash = ""  #хэш sha-256 данных vfs
        self.loaded = False  #флаг загрузки vfs

    def load_from_xml(self, xml_path):
        """загрузка vfs из xml файла"""
        try:
            if not os.path.exists(xml_path):  #проверка существования файла
                return False, f"файл vfs не найден: {xml_path}"  #возврат ошибки

            #читаем файл для вычисления хеша в бинарном режиме
            with open(xml_path, 'rb') as f:  #открытие файла в бинарном режиме
                file_data = f.read()  #чтение всех данных файла
                self.sha256_hash = hashlib.sha256(file_data).hexdigest()  #вычисление sha-256 хеша

            #парсим xml с указанием кодировки
            with open(xml_path, 'r', encoding='utf-8') as f:  #открытие файла с кодировкой utf-8
                tree = ET.parse(f)  #парсинг xml дерева
                root = tree.getroot()  #получение корневого элемента

            #получаем имя vfs из атрибута xml
            self.name = root.get('name', 'unnamed_vfs')  #имя vfs или значение по умолчанию
            self.files = {}  #очищаем словарь файлов

            def process_element(element, current_path):  #внутренняя функция обработки элементов
                #рекурсивная обработка структуры xml
                for child in element:  #перебор всех дочерних элементов
                    if child.tag == 'directory':  #если элемент - директория
                        #обработка директории
                        dir_name = child.get('name', 'unnamed')  #получение имени директории
                        dir_path = os.path.join(current_path, dir_name).replace('\\', '/')  #формирование пути
                        process_element(child, dir_path)  #рекурсивный вызов для вложенных элементов
                    elif child.tag == 'file':  #если элемент - файл
                        #обработка файла
                        file_name = child.get('name', 'unnamed')  #получение имени файла
                        file_path = os.path.join(current_path, file_name).replace('\\', '/')  #формирование пути
                        content = child.text or ""  #содержимое файла (пустая строка если none)
                        if child.get('encoding') == 'base64':  #проверка кодировки base64
                            #декодирование base64 данных
                            try:
                                content = base64.b64decode(content).decode('utf-8')  #декодирование base64
                            except:  #обработка ошибок декодирования
                                content = f"[binary data - size: {len(content)} bytes]"  #сообщение об ошибке
                        self.files[file_path] = content  #сохраняем файл в памяти

            process_element(root, self.root)  #начинаем обработку с корневого элемента
            self.loaded = True  #устанавливаем флаг загрузки
            return True, f"vfs '{self.name}' успешно загружена"  #возврат успешного результата

        except Exception as e:  #обработка всех исключений
            return False, f"ошибка загрузки vfs: {str(e)}"  #возврат ошибки

    def list_directory(self, path):
        """список содержимого директории"""
        #Нормализуем путь
        if path != "/":
            path = path.rstrip('/')

        dirs = set()  #множество для директорий
        files = []  #список для файлов

        for file_path in self.files.keys():  #перебор всех путей файлов
            #Получаем директорию файла
            file_dir = os.path.dirname(file_path)
            if file_dir == "":
                file_dir = "/"

            #Если запрашивают корневую директорию
            if path == "/":
                if file_dir == "/":  #файл в корне
                    files.append(os.path.basename(file_path))
                else:  #файл во вложенной директории
                    #Берем первую часть пути после корня
                    first_dir = file_path.split('/')[1]
                    dirs.add(first_dir)
            else:
                #Если файл находится в запрашиваемой директории
                if file_dir == path:
                    files.append(os.path.basename(file_path))
                #Если файл находится во вложенной директории
                elif file_path.startswith(path + '/'):
                    remaining = file_path[len(path) + 1:]
                    next_part = remaining.split('/')[0]
                    dirs.add(next_part)

        result = []  #результирующий список
        for d in sorted(dirs):  #сортировка директорий по алфавиту
            result.append(f"[dir] {d}")  #форматируем директорию
        for f in sorted(files):  #сортировка файлов по алфавиту
            result.append(f"[file] {f}")  #форматируем файл

        return result  #возврат результата

    def directory_exists(self, path):
        """проверка существования директории"""
        if path == "/":
            return True  #корневая директория всегда существует

        #Проверяем, есть ли файлы в этой директории или ее поддиректориях
        for file_path in self.files.keys():
            file_dir = os.path.dirname(file_path)
            if file_dir == "":
                file_dir = "/"

            if file_dir == path or file_path.startswith(path + '/'):
                return True
        return False

    def file_exists(self, path):
        """проверка существования файла"""
        return path in self.files  #проверка наличия пути в словаре

    def read_file(self, path):
        """чтение содержимого файла"""
        return self.files.get(path, None)  #возвращаем содержимое файла или none

    def get_file_head(self, path, lines=10):
        """получение первых N строк файла"""
        content = self.read_file(path)  #чтение содержимого файла
        if content is None:  #если файл не найден
            return None  #возвращаем None

        file_lines = content.split('\n')  #разбиваем содержимое на строки
        return '\n'.join(file_lines[:lines])  #возвращаем первые N строк

    def get_info(self):
        """получение информации о vfs"""
        if not self.loaded:  #проверка загрузки vfs
            return "vfs не загружена"  #сообщение об ошибке

        file_count = len(self.files)  #количество файлов
        #количество директорий (уникальные пути без последнего элемента)
        dir_count = len(set('/'.join(path.split('/')[:-1]) for path in self.files.keys()))  #подсчет уникальных директорий

        return (f"имя vfs: {self.name}\n"  #форматированная информация о vfs
                f"хэш sha-256: {self.sha256_hash}\n"
                f"файлов: {file_count}\n"
                f"директорий: {dir_count}\n"
                f"статус: загружена")


class VFSEmulator:
    def __init__(self, root, vfs_path=None, script_path=None):
        self.root = root  #главное окно
        self.root.title("finikato.os(vfs)")  #заголовок окна
        self.root.configure(background="#7366bd")  #фон окна
        self.root.geometry("800x600")  #размер окна

        self.program_dir = os.path.dirname(os.path.abspath(__file__))  #директория программы
        os.chdir(self.program_dir)  #меняем текущую директорию

        self.vfs_path = os.path.abspath(vfs_path) if vfs_path else self.program_dir  #путь к vfs
        self.prompt = "vfs> "  #приглашение командной строки
        self.script_path = os.path.abspath(script_path) if script_path else None  #путь к скрипту
        self.is_running = False  #флаг работы эмулятора
        self.current_dir = "/"  #текущая директория в vfs

        #инициализация vfs
        self.vfs = VFS()  #создание экземпляра vfs

        self.create_gui()  #создание графического интерфейса

        self.write_output(f"программа запущена из: {self.program_dir}")  #информация о запуске
        self.write_output(f"текущая рабочая директория: {os.getcwd()}")  #текущая директория

        if self.script_path:  #если указан путь к скрипту
            exists = "найден" if os.path.exists(self.script_path) else "не найден"  #проверка существования
            self.write_output(f"путь к скрипту: {self.script_path} ({exists})")  #вывод информации о скрипте

        self.write_output("\nкоманды: set vfs_path|script_path <значение>, start, exit, vfs-info")  #список команд
        self.write_output("=" * 50)  #разделитель

        #автозагрузка vfs если указан путь
        if vfs_path and os.path.exists(vfs_path):  #проверка существования vfs
            success, message = self.vfs.load_from_xml(vfs_path)  #загрузка vfs
            self.write_output(message)  #вывод сообщения
            if success:  #если загрузка успешна
                self.write_output(self.vfs.get_info())  #вывод информации о vfs

        if self.script_path and os.path.exists(self.script_path):  #если скрипт существует
            self.root.after(100, self.start_emulator)  #автозапуск через 100мс

    def create_gui(self):
        """создание графического интерфейса"""
        create = tk.Label(self.root, text="меню пользователя:", background="#ffffff",  #метка заголовка
                          font=("comic sans ms", 16))  #шрифт заголовка
        create.grid(column=0, row=0, padx=10, pady=10, columnspan=2)  #размещение заголовка

        text_frame = tk.Frame(self.root)  #фрейм для текстового поля
        text_frame.grid(column=0, row=1, columnspan=2, padx=10, pady=10, sticky="nsew")  #размещение фрейма

        self.root.grid_rowconfigure(1, weight=1)  #настройка веса строки
        self.root.grid_columnconfigure(0, weight=1)  #настройка веса колонки

        scrollbar = tk.Scrollbar(text_frame)  #создание скроллбара
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)  #размещение скроллбара

        self.output_area = tk.Text(text_frame, width=70, height=20, background="white",  #текстовое поле вывода
                                   font=("consolas", 10), yscrollcommand=scrollbar.set)  #настройки текстового поля
        self.output_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)  #размещение текстового поля

        scrollbar.config(command=self.output_area.yview)  #связываем скроллбар с текстовым полем

        self.output_area.insert(tk.END, "добро пожаловать в finikato.os с vfs\nвведите команду\n")  #начальное сообщение
        self.output_area.configure(state='disabled')  #блокируем редактирование

        input_frame = tk.Frame(self.root, background="#7366bd")  #фрейм для ввода
        input_frame.grid(column=0, row=2, columnspan=2, padx=10, pady=10)  #размещение фрейма ввода

        self.entry = tk.Entry(input_frame, width=50, font=("arial", 12))  #поле ввода команд
        self.entry.pack(side=tk.LEFT, padx=5)  #размещение поля ввода
        self.entry.bind("<Return>", self.process_command)  #привязка клавиши enter
        self.entry.focus()  #установка фокуса на поле ввода

        self.btn = tk.Button(input_frame, text="ввод", command=self.process_command,  #кнопка ввода
                             font=("comic sans ms", 12), background="#4caf50")  #настройки кнопки
        self.btn.pack(side=tk.LEFT, padx=5)  #размещение кнопки

        button_frame = tk.Frame(self.root, background="#7366bd")  #фрейм для дополнительных кнопок
        button_frame.grid(column=0, row=3, columnspan=2, pady=5)  #размещение фрейма кнопок

        btn_clear = tk.Button(button_frame, text="очистить вывод", command=self.clear_output,  #кнопка очистки
                              font=("comic sans ms", 10), background="#ff5722")  #настройки кнопки очистки
        btn_clear.pack(side=tk.LEFT, padx=5)  #размещение кнопки очистки

    def write_output(self, text):
        """вывод текста в область вывода"""
        self.output_area.configure(state='normal')  #включаем редактирование
        self.output_area.insert(tk.END, text + "\n")  #добавляем текст
        self.output_area.see(tk.END)  #автопрокрутка к концу
        self.output_area.configure(state='disabled')  #отключаем редактирование

    def clear_output(self):
        """очистка текстового поля вывода"""
        self.output_area.configure(state='normal')  #включаем редактирование
        self.output_area.delete(1.0, tk.END)  #удаляем весь текст
        self.output_area.insert(tk.END, "введите команду\n")  #добавляем начальное сообщение
        self.output_area.see(tk.END)  #автопрокрутка к концу
        self.output_area.configure(state='disabled')  #отключаем редактирование

    def process_command(self, event=None):
        """обработка команд пользователя"""
        command = self.entry.get().strip()  #получение команды из поля ввода
        self.entry.delete(0, tk.END)  #очищаем поле ввода

        if not command:  #если команда пустая
            return  #выход из функции

        if self.is_running:  #если эмулятор запущен
            self.write_output(f"{self.prompt}{command}")  #вывод с приглашением vfs
        else:  #если эмулятор не запущен
            self.write_output(f"> {command}")  #вывод с приглашением настроек

        parts = command.split()  #разбиение команды на части

        if not parts:  #если нет частей команды
            return  #выход из функции

        cmd = parts[0].lower()  #команда в нижнем регистре
        args = parts[1:]  #аргументы команды

        if self.is_running:  #команды эмулятора vfs
            if cmd == "exit":  #команда выхода
                self.is_running = False  #сброс флага работы
                self.write_output("эмулятор остановлен.")  #сообщение об остановке
            elif cmd == "ls":  #команда списка файлов
                self.handle_ls(args)  #обработка команды ls
            elif cmd == "cd":  #команда смены директории
                self.handle_cd(args)  #обработка команды cd
            elif cmd == "cat":  #команда просмотра файла
                self.handle_cat(args)  #обработка команды cat
            elif cmd == "head":  #команда вывода начала файла
                self.handle_head(args)  #обработка команды head
            elif cmd == "vfs-info":  #команда информации о vfs
                if self.vfs.loaded:  #если vfs загружена
                    self.write_output(self.vfs.get_info())  #вывод информации
                else:  #если vfs не загружена
                    self.write_output("vfs не загружена")  #сообщение об ошибке
            else:  #неизвестная команда
                self.write_output(f"неизвестная команда: {cmd}")  #сообщение об ошибке
        else:  #команды настройки
            if cmd == "set":  #команда установки параметров
                self.process_set_command(args)  #обработка команды set
            elif cmd == "start":  #команда запуска эмулятора
                self.start_emulator()  #запуск эмулятора
            elif cmd == "vfs-info":  #команда информации о vfs
                if self.vfs.loaded:  #если vfs загружена
                    self.write_output(self.vfs.get_info())  #вывод информации
                else:  #если vfs не загружена
                    self.write_output("vfs не загружена")  #сообщение об ошибке
            elif cmd == "exit":  #команда выхода
                self.root.destroy()  #завершение программы
            else:  #неизвестная команда
                self.write_output(f"неизвестная команда: {cmd}")  #сообщение об ошибке

    def handle_ls(self, args):
        """обработка команды ls"""
        target = ' '.join(args) if args else self.current_dir  #целевая директория
        if self.vfs.loaded:  #если vfs загружена
            items = self.vfs.list_directory(target)  #получение списка файлов
            if items:  #если есть элементы
                for item in items:  #перебор элементов
                    self.write_output(item)  #вывод элемента
            else:  #если директория пуста
                self.write_output("директория пуста")  #сообщение о пустой директории
        else:  #если vfs не загружена
            self.write_output("vfs не загружена")  #сообщение об ошибке

    def handle_cd(self, args):
        """обработка команды cd"""
        if not args:  #если аргументов нет
            self.current_dir = "/"  #переход в корневую директорию
            self.write_output("переход в корневую директорию")  #сообщение
            return  #выход из функции

        target = ' '.join(args)  #целевая директория

        #обработка абсолютных и относительных путей
        if target.startswith('/'):  #абсолютный путь
            new_dir = target
        else:  #относительный путь
            if self.current_dir == '/':  #если текущая директория корневая
                new_dir = '/' + target
            else:  #если текущая директория не корневая
                new_dir = self.current_dir + '/' + target

        #нормализация пути (удаление двойных слешей и т.д.)
        new_dir = new_dir.replace('//', '/')  #удаление двойных слешей

        #проверка существования директории
        if self.vfs.loaded and self.vfs.directory_exists(new_dir):  #если vfs загружена и директория существует
            self.current_dir = new_dir  #установка новой директории
            self.write_output(f"текущая директория: {self.current_dir}")  #сообщение
        else:  #если директория не существует
            self.write_output(f"ошибка: директория не найдена: {target}")  #сообщение об ошибке

    def handle_cat(self, args):
        """обработка команды cat"""
        if not args:  #если нет аргументов
            self.write_output("ошибка: укажите имя файла")  #сообщение об ошибке
            return  #выход из функции

        file_path = ' '.join(args)  #путь к файлу

        #обработка относительных путей
        if not file_path.startswith('/'):  #если путь относительный
            if self.current_dir == '/':  #если текущая директория корневая
                file_path = '/' + file_path
            else:  #если текущая директория не корневая
                file_path = self.current_dir + '/' + file_path

        if self.vfs.loaded and self.vfs.file_exists(file_path):  #проверка существования файла
            content = self.vfs.read_file(file_path)  #чтение содержимого файла
            self.write_output(f"содержимое файла {file_path}:")  #заголовок
            self.write_output("-" * 40)  #разделитель
            self.write_output(content)  #вывод содержимого
            self.write_output("-" * 40)  #разделитель
        else:  #если файл не найден
            self.write_output(f"файл не найден: {file_path}") #сообщение об ошибке

    def handle_head(self, args):
        """обработка команды head"""
        if not args:  #если нет аргументов
            self.write_output("ошибка: укажите имя файла")  #сообщение об ошибке
            self.write_output("использование: head [-n число] <файл>")  #справка по использованию
            return  #выход из функции

        lines = 10  #количество строк по умолчанию
        file_args = []  #аргументы для имени файла

        #парсинг аргументов
        i = 0
        while i < len(args):
            if args[i] == '-n' and i + 1 < len(args):  #если найден параметр -n
                try:
                    lines = int(args[i + 1])  #преобразование в число
                    i += 2  #пропускаем два аргумента
                except ValueError:  #если преобразование не удалось
                    self.write_output(f"ошибка: неверное число строк: {args[i + 1]}")  #сообщение об ошибке
                    return  #выход из функции
            else:  #если это не параметр -n
                file_args.append(args[i])  #добавляем в аргументы файла
                i += 1  #переходим к следующему аргументу

        if not file_args:  #если не указано имя файла
            self.write_output("ошибка: укажите имя файла")  #сообщение об ошибке
            self.write_output("использование: head [-n число] <файл>")  #справка по использованию
            return  #выход из функции

        file_path = ' '.join(file_args)  #путь к файлу

        #обработка относительных путей
        if not file_path.startswith('/'):  #если путь относительный
            if self.current_dir == '/':  #если текущая директория корневая
                file_path = '/' + file_path
            else:  #если текущая директория не корневая
                file_path = self.current_dir + '/' + file_path

        if self.vfs.loaded and self.vfs.file_exists(file_path):  #проверка существования файла
            content = self.vfs.get_file_head(file_path, lines)  #получение первых строк
            self.write_output(f"первые {lines} строк файла {file_path}:")  #заголовок
            self.write_output("-" * 40)  #разделитель
            self.write_output(content)  #вывод содержимого
            self.write_output("-" * 40)  #разделитель
        else:  #если файл не найден
            self.write_output(f"файл не найден: {file_path}")  #сообщение об ошибке

    def process_set_command(self, args):
        """обработка команды set"""
        if len(args) < 2:  #проверка количества аргументов
            self.write_output("ошибка: команда set требует два аргумента")  #сообщение об ошибке
            return  #выход из функции

        param = args[0].lower()  #параметр в нижнем регистре
        value = ' '.join(args[1:]).strip('"\'')  #значение параметра
        abs_value = os.path.abspath(value)  #абсолютный путь

        if param == "vfs_path":  #установка пути vfs
            self.vfs_path = abs_value  #сохранение пути
            #пытаемся загрузить vfs
            success, message = self.vfs.load_from_xml(self.vfs_path)  #загрузка vfs
            self.write_output(message)  #вывод сообщения
            if success:  #если загрузка успешна
                self.write_output(self.vfs.get_info())  #вывод информации о vfs
        elif param == "script_path":  #установка пути скрипта
            self.script_path = abs_value  #сохранение пути
            exists = "найден" if os.path.exists(self.script_path) else "не найден"  #проверка существования
            self.write_output(f"путь к скрипту установлен: {self.script_path} ({exists})")  #вывод информации
        else:  #неизвестный параметр
            self.write_output(f"неизвестный параметр: {param}")  #сообщение об ошибке

    def start_emulator(self):
        """запуск эмулятора vfs"""
        self.write_output("=" * 50)  #разделитель
        self.write_output("запуск эмулятора vfs")  #заголовок
        self.write_output("=" * 50)  #разделитель

        self.is_running = True  #установка флага работы
        self.current_dir = "/"  #сброс текущей директории

        if self.script_path and os.path.exists(self.script_path):  #если скрипт существует
            self.execute_script()  #выполнение скрипта
        elif self.script_path:  #если скрипт указан но не существует
            self.write_output(f"ошибка: скрипт не найден: {self.script_path}")  #сообщение об ошибке

        self.write_output("эмулятор запущен. введите команды vfs или 'exit'.")  #сообщение о готовности
        self.write_output("доступные команды: ls, cd, cat, head, vfs-info, exit")  #список команд

    def execute_script(self):
        """выполнение скрипта команд"""
        self.write_output(f"выполнение скрипта: {self.script_path}")  #информация о скрипте

        try:  #обработка исключений
            #пробуем разные кодировки
            encodings = ['utf-8', 'cp1251', 'cp866', 'iso-8859-1']
            script_content = None

            for encoding in encodings:
                try:
                    with open(self.script_path, 'r', encoding=encoding) as f:
                        script_content = f.readlines()
                    break
                except UnicodeDecodeError:
                    continue

            if script_content is None:
                self.write_output(f"ошибка: не удалось прочитать скрипт с поддерживаемыми кодировками")
                return

            for line_num, line in enumerate(script_content, 1):
                line = line.strip()  #удаление пробелов

                if not line or line.startswith('#'):  #пропуск пустых строк и комментариев
                    continue  #переход к следующей строке

                self.write_output(f"{self.prompt}{line}")  #вывод команды

                parts = line.split()  #разбиение строки на части

                if not parts:  #если нет частей
                    continue  #переход к следующей строке

                cmd = parts[0].lower()  #команда в нижнем регистре
                args = parts[1:]  #аргументы команды

                if cmd == "exit":  #команда выхода
                    self.write_output("завершение работы...")  #сообщение
                    self.is_running = False  #сброс флага работы
                    break  #выход из цикла
                elif cmd == "ls":  #команда списка файлов
                    self.handle_ls(args)  #обработка команды ls
                elif cmd == "cd":  #команда смены директории
                    self.handle_cd(args)  #обработка команды cd
                elif cmd == "cat":  #команда просмотра файла
                    self.handle_cat(args)  #обработка команды cat
                elif cmd == "head":  #команда вывода начала файла
                    self.handle_head(args)  #обработка команды head
                elif cmd == "vfs-info":  #команда информации о vfs
                    if self.vfs.loaded:  #если vfs загружена
                        self.write_output(self.vfs.get_info())  #вывод информации
                    else:  #если vfs не загружена
                        self.write_output("vfs не загружена")  #сообщение об ошибке
                else:  #неизвестная команда
                    self.write_output(f"неизвестная команда: {cmd}")  #сообщение об ошибке

        except Exception as e:  #обработка исключений
            self.write_output(f"ошибка чтения скрипта: {e}")  #сообщение об ошибке

        self.write_output("выполнение скрипта завершено")  #сообщение о завершении


def main():
    vfs_path, script_path = None, None  #инициализация переменных путей

    i = 1  #начальный индекс аргументов
    while i < len(sys.argv):  #обработка аргументов командной строки
        if sys.argv[i] == "--vfs_path" and i + 1 < len(sys.argv):  #проверка аргумента vfs_path
            vfs_path = sys.argv[i + 1]  #сохранение пути vfs
            i += 2  #переход через два аргумента
        elif sys.argv[i] == "--script_path" and i + 1 < len(sys.argv):  #проверка аргумента script_path
            script_path = sys.argv[i + 1]  #сохранение пути скрипта
            i += 2  #переход через два аргумента
        else:  #неизвестный аргумент
            i += 1  #переход к следующему аргументу

    root = tk.Tk()  #создание главного окна
    app = VFSEmulator(root, vfs_path, script_path)  #создание экземпляра эмулятора
    root.mainloop()  #запуск главного цикла


if __name__ == "__main__":
    main()  #вызов главной функции