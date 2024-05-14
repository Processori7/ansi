import ctypes
import os
import pathlib
import shutil
import subprocess
import sys
import time
from freeGPT import AsyncClient
import asyncio
from datetime import datetime
from colorama import init, Fore
import winreg


init()  # Инициализация colorama

def add_to_path(path, root=winreg.HKEY_CURRENT_USER, key_path='Environment', access=winreg.KEY_ALL_ACCESS):
    root_key = winreg.ConnectRegistry(None, root)
    key = winreg.OpenKey(root_key, key_path, 0, access)
    value, value_type = winreg.QueryValueEx(key, 'path')
    value = value.rstrip(';') + ';' + path
    winreg.SetValueEx(key, 'path', 0, value_type, value)
    winreg.CloseKey(key)
    winreg.CloseKey(root_key)

def clear_terminal():
    """Очищает терминал."""
    try:
        subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)
    except Exception as e:
        print(f"Ошибка при очистке терминала: {e}")

def print_flush2(text, delay=0.003):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)  # Задержка в секундах
    time.sleep(0.005)  # Задержка перед очисткой терминала

def print_flush3(text):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
    print()
    time.sleep(0.00003)  # Задержка перед очисткой терминала

async def print_history():
    if os.path.exists("history.txt"):
        with open("history.txt", "r") as f:
            for line in f:
                print(line.strip())
        ans = input("\nДля возврата в меню введите 'да' или 'yes'\nДля очистки истории введите cls: ")
        if ans.lower() in ['да', 'yes']:
            await main()
        elif ans.lower() == 'cls':
            os.remove("history.txt")
            print("Готово")
            await main()
    else:
        print("Ой! История не найдена!\n")

async def communicate_with_model(message):
    """Взаимодействует с моделью для генерации ответа."""
    try:
        resp = await AsyncClient.create_completion("gpt3", message)
        return resp
    except Exception as e:
        return f"Ошибка при общении с моделью: {e}"

async def main():
    """Основная функция программы."""
    try:
        # Проверяем, запущен ли скрипт от имени администратора
        if ctypes.windll.shell32.IsUserAnAdmin():
            # Папка для копирования файла
            ansi_folder = "C:\\ansi\\"
            if not os.path.exists(ansi_folder):
                os.makedirs(ansi_folder)
                add_to_path(ansi_folder)

            # Проверяем наличие файла ansi.exe в папке C:\ansi
            ansi_exe_path = os.path.join(ansi_folder, "ansi.exe")
            if not os.path.exists(ansi_exe_path):
                # Если файл не найден, копируем его из папки Desktop
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                source_path = os.path.join(desktop_path, "ansi.exe")
                shutil.copy(source_path, ansi_folder)

        print_flush2(
"""
Ansi GPT3 готова к общению.
Основные команды: 
- Введите 'выход' или 'ex' или 'exit', чтобы завершить.
- Введите 'очистить' или 'cls' или 'clear', чтобы удалить переписку.
- Введите 'история' или 'hsitory', чтобы вывести истрию переписки на экран.\n
""")

        history = []

        while True:
            user_input = input(Fore.LIGHTGREEN_EX + "Вы: " + Fore.WHITE)
            print()

            if user_input.lower() in ['история', 'history']:
                await print_history()
            elif user_input.lower() in ['выход', 'ex', 'exit']:
                print("До свидания!")
                sys.exit()
            elif user_input.lower() in ['очистить', 'cls', 'clear']:
                clear_terminal()
                history = []
                continue
            else:
                response = await communicate_with_model(user_input)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                history.append((timestamp, user_input, response))

                print(Fore.YELLOW + "Ansi GPT3 LLM:" + Fore.WHITE, end=' ')
                print_flush3(response + "\n")

                # Сохранение истории в файл
                with open("history.txt", "a") as f:
                    for entry in history:
                        f.write(f"{entry[0]}\nВопрос пользователя: {entry[1]}\nОтвет Ansi: {entry[2]}\n\n")

    except KeyboardInterrupt:
        print("\nПрограмма завершена пользователем.")

if __name__ == "__main__":
    asyncio.run(main())