#1.1
import tkinter as tk # импортируем tkinter

def clicked():#функция для ввода и обработки комманд
    input_text = txt.get()#считывание текста из поля ввода
    btn.configure(text="Далее")

    # Выводим введенную команду в текстовое поле
    output_text.insert(tk.END, f"> {input_text}\n")

    # Обрабатываем команды
    comm = input_text.split()[0]#получаем команду
    args = input_text.split()[1:]#получаем аргументы
    #print(comm)
    #print(args)

    #обработка команд
    if comm == "ls":
        output_text.insert(tk.END, "Выполнена команда ls\n")
        output_text.insert(tk.END, "аргумент " +f"{args}")
    elif comm == "cd":
        output_text.insert(tk.END, "Выполнена команда cd\n")
        output_text.insert(tk.END, "аргумент " +f"{args}")
    elif comm == "exit":
        exit(0)
    else:
        output_text.insert(tk.END, f"Неизвестная команда\n")

    # Прокручиваем к концу текста
    output_text.see(tk.END)#прокрутка текстового поля
    txt.delete(0, tk.END)#очистка поля ввода

def clear_output():
    # Очищаем текстовое поле вывода
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, "Введите команду\n")#предлагаем пользователю ввести новую команду
    output_text.see(tk.END)#сдвиг вниз

window = tk.Tk() # создаём главное окно
window.configure(background="#7366BD")#задаём цвет
window.title("finikato.OS(VFS)") # устанавливаем заголовок окна
window.geometry("800x600") # задаём размер окна


#табличка с текстом
create = tk.Label(window, text="Меню Пользователя:", background="#FFFFFF", font=("Comic Sans MS", 16))
create.grid(column=0, row=0, padx=10, pady=10, columnspan=2)#устанавливаем расположение таблички

#текстовое поле для вывода информации с прокруткой
#позиционирование текстового поля
text_frame = tk.Frame(window)
text_frame.grid(column=0, row=1, columnspan=2, padx=10, pady=10, sticky="nsew")


window.grid_rowconfigure(1, weight=1)
window.grid_columnconfigure(0, weight=1)

#прокрутка
scrollbar = tk.Scrollbar(text_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

#текстовое поле
output_text = tk.Text(text_frame, width=70, height=20, background="white",
                      font=("Consolas", 10), yscrollcommand=scrollbar.set)
output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

#связываем скроллбар с текстовым полем
scrollbar.config(command=output_text.yview)

#начальное сообщение
output_text.insert(tk.END, "Добро пожаловать в finikato.OS\nВведите команду\n")

#поле ввода и кнопка
input_frame = tk.Frame(window, background="#7366BD")#контейнер
input_frame.grid(column=0, row=2, columnspan=2, padx=10, pady=10)

#поле ввода
txt = tk.Entry(input_frame, width=50, font=("Arial", 12))#
txt.pack(side=tk.LEFT, padx=5)

#кнопка
btn = tk.Button(input_frame, text="Ввод", command=clicked, font=("Comic Sans MS", 12), background="#4CAF50")
btn.pack(side=tk.LEFT, padx=5)

#кнопки для быстрого доступа
button_frame = tk.Frame(window, background="#7366BD")
button_frame.grid(column=0, row=3, columnspan=2, pady=5)


btn_clear = tk.Button(button_frame, text="Очистить вывод", command=clear_output,
                      font=("Comic Sans MS", 10), background="#FF5722")
btn_clear.pack(side=tk.LEFT, padx=5)


txt.focus()#устанавливаем фокус на поле ввода при запуске программы

#привязываем Enter к кнопке
def on_enter(event):
    clicked()

txt.bind('<Return>', on_enter)#привязываем событие нажатия Enter к функции on_enter

window.mainloop()#запускаем главный цикл, чтобы окно не закрывалось

