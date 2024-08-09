
import os
import re
import sys
import shutil
import subprocess
import ctypes
import time
import asyncio
import winreg
import configparser
import webbrowser
import requests
from datetime import datetime
from colorama import init, Fore
from webscout import KOBOLDAI, BLACKBOXAI, ThinkAnyAI, PhindSearch, DeepInfra, WEBS as w
from packaging import version


CURRENT_VERSION = "1.3.2"

init()  # Инициализация colorama

def update_app(update_url):
   webbrowser.open(update_url)

def check_for_updates():
    try:
        # Получение информации о последнем релизе на GitHub
        response = requests.get("https://api.github.com/repos/Processori7/ansi/releases/latest")
        response.raise_for_status()
        latest_release = response.json()

        # Получение ссылки на файл exe последней версии
        assets = latest_release["assets"]
        for asset in assets:
            if asset["name"].endswith(".exe"):
                download_url = asset["browser_download_url"]
                break
        else:
            print("Не удалось найти файл exe для последней версии.")
            return

        # Сравнение текущей версии с последней версией
        latest_version_str = latest_release["tag_name"]
        match = re.search(r'\d+\.\d+', latest_version_str)
        if match:
            latest_version = match.group()
        else:
            latest_version = latest_version_str

        if version.parse(latest_version) > version.parse(CURRENT_VERSION):
            # Предложение пользователю обновление
            ans = input(f"Доступна новая версия {latest_version}. Хотите обновить?\nВведите да - для обновления.\n>>>").lower()
            if ans == 'да':
                update_app(download_url)
    except requests.exceptions.RequestException as e:
            print("Ошибка при проверке обновлений:", e)

# Функция для чтения настроек модели из INI-файла
async def read_config_from_drive_c():
    config = configparser.ConfigParser()
    config.read(r'C:\ansi\config.ini')
    if 'model' in config:
        return config.get('model', 'name')
    else:
        return 'claude-3-haiku'

async def read_model_config():
    config = configparser.ConfigParser()
    if os.path.exists(r'C:\ansi\config.ini'):
        config.read(r'C:\ansi\config.ini')
    else:
        config.read('config.ini')
    if 'model' in config:
        return config.get('model', 'name')
    else:
        return 'claude-3-haiku'

# Функция для записи настроек модели в INI-файл
async def write_model_config(model_name):
    config = configparser.ConfigParser()
    config.add_section('model')
    config.set('model', 'name', model_name)
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

async def write_model_config_to_drive_c(model_name):
    config = configparser.ConfigParser()
    config.add_section('model')
    config.set('model', 'name', model_name)
    with open(r'C:\ansi\config.ini', 'w') as configfile:
        config.write(configfile)

async def show_model():
    await print_flush2("По умолчанию используется: claude-3-haiku.\nДоступные провайдеры и модели:\n1.KoboldAI - any LLM\n2.Blackbox - Blackbox LLM\n3.ThinkAnyAI - Claude-3-haiku\n4.Phind - Phind LLM\n5.Deepinfra - Meta-Llama-3-70B-Instruct\n6.Claude-3-haiku(DuckDuckGo)\n")
    ans = input("Введите номер выбранной модели, например 5: ")
    if ans.isdigit() and int(ans) < 7:
        model_name = ['KoboldAI', 'Blackbox', 'ThinkAnyAI', 'Phind', 'Deepinfra', 'claude-3-haiku'][int(ans) -1]
        if os.path.exists(r'C:\ansi\config.ini'):
            await write_model_config_to_drive_c(model_name)
        else:
            await write_model_config(model_name)
        await print_flush2("Готово, модель добавлена в Config.ini\n")
        await main()
        return model_name
    else:
        print("Ошибка! Пожалуйста, введите правильное число.")
        await show_model()

async def add_to_path(path, root=winreg.HKEY_CURRENT_USER, key_path='Environment', access=winreg.KEY_ALL_ACCESS):
    root_key = winreg.ConnectRegistry(None, root)
    key = winreg.OpenKey(root_key, key_path, 0, access)
    value, value_type = winreg.QueryValueEx(key, 'path')
    value = value.rstrip(';') + ';' + path
    winreg.SetValueEx(key, 'path', 0, value_type, value)
    winreg.CloseKey(key)
    winreg.CloseKey(root_key)

async def clear_terminal():
    """Очищает терминал."""
    try:
        subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)
    except Exception as e:
        print(f"Ошибка при очистке терминала: {e}")

async def print_flush2(text):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
    time.sleep(0.005)  # Задержка перед очисткой терминала

async def print_flush3(text):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
    print()

async def print_history():
    ansi_folder = "C:\\ansi\\"
    history_file = os.path.join(ansi_folder, "history.txt")
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            for line in f:
                print(line.strip())
        ans = input("\nДля возврата в меню введите 'да' или 'yes'\nДля очистки истории введите cls: ")
        if ans.lower() in ['да', 'yes']:
            await main()
        elif ans.lower() == 'cls':
            os.remove(history_file)
            print("Готово")
            await main()
    else:
        print("Ой! История не найдена!\n")

async def communicate_with_model(message):
    """Взаимодействует с моделью для генерации ответа."""
    try:
        ans = w().chat(message, model='gpt-4o-mini')  # gpt-4o-mini, mixtral-8x7b, llama-3-70b, claude-3-haiku
        return ans
    except Exception as e:
        return f"Ошибка при общении с моделью: {e}"

async def communicate_with_KoboldAI(user_input):
    try:
        koboldai = KOBOLDAI()
        response = koboldai.chat(user_input)
        return response
    except Exception as e:
        return f"Ошибка при общении с KoboldAI: {e}"

async def communicate_with_BlackboxAI(user_input):
    try:
        ai = BLACKBOXAI(
            is_conversation=True,
            max_tokens=800,
            timeout=30,
            intro=None,
            filepath=None,
            update_file=True,
            proxies={},
            history_offset=10250,
            act=None,
            model=None
        )

        responce = ai.chat(user_input)
        return responce
    except Exception as e:
        return f"Ошибка при общении с BLACKBOXAI: {e}"

async def communicate_with_ThinkAnyAI(user_input):
    try:
        opengpt = ThinkAnyAI()
        response = opengpt.chat(user_input)
        return response
    except Exception as e:
        return f"Ошибка при общении с ThinkAnyAI: {e}"

async def communicate_with_Phind(user_input):
    try:
        ph = PhindSearch()
        response = ph.chat(user_input)
        return response
    except Exception as e:
        return f"Ошибка при общении с PhindAI: {e}"

async def communicate_with_DeepInfra(user_input):
    try:
        ai = DeepInfra(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct",  # DeepInfra models
            is_conversation=True,
            max_tokens=800,
            timeout=30,
            intro=None,
            filepath=None,
            update_file=True,
            proxies={},
            history_offset=10250,
            act=None,
        )
        message = ai.ask(user_input)
        responce = ai.get_message(message)
        return responce
    except Exception as e:
        return f"Ошибка при общении с DeepInfraAI: {e}"

async def save_histoy(user_input, response):
    ansi_folder = "C:\\ansi\\"
    history_file = os.path.join(ansi_folder, "history.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Сохранение истории в файл
    if not os.path.exists(ansi_folder):
        os.makedirs(ansi_folder)
    with open(history_file, "a") as f:
        f.write(f"Дата и время: {timestamp}\nВопрос пользователя: {user_input}\nОтвет Ansi: {response}\n\n")

async def main():
    """Основная функция программы."""
    try:
        config_file = "config.ini"
        ansi_folder = "C:\\ansi\\"
        # Проверяем, запущен ли скрипт от имени администратора
        if ctypes.windll.shell32.IsUserAnAdmin():
            # Папка для копирования файла
            if not os.path.exists(ansi_folder):
                os.makedirs(ansi_folder)
                await add_to_path(ansi_folder)

            # Проверяем наличие файла ansi.exe в папке C:\ansi
            ansi_exe_path = os.path.join(ansi_folder, "ansi.exe")
            if not os.path.exists(ansi_exe_path):
                # Если файл не найден, копируем его из папки Desktop
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                source_path = os.path.join(desktop_path, "ansi.exe")
                shutil.copy(source_path, ansi_folder)

        # Проверяем, существует ли файл config.ini в папке C:\ansi
        ansi_config_file_path = os.path.join(ansi_folder, config_file)
        if os.path.exists(ansi_config_file_path):
            model_name = await read_config_from_drive_c()
        else:
            model_name = await read_model_config()
            if not os.path.exists(ansi_config_file_path):
                await write_model_config_to_drive_c(model_name)

        await print_flush2(
"""
Ansi GPT3 готова к общению.
Основные команды: 
- Введите 'выход' или 'ex' или 'exit', чтобы завершить.
- Введите 'очистить' или 'cls' или 'clear', чтобы удалить переписку.
- Введите 'история' или 'hsitory', чтобы вывести истрию переписки на экран.
- Введите 'model' или 'модель', чтобы выбрать LLM из доступных.\n
""")

        while True:
            user_input = input(Fore.LIGHTGREEN_EX + "Вы: " + Fore.WHITE)
            print()
            if user_input.lower() in ['история', 'history']:
                await print_history()
            elif user_input.lower() in ['выход', 'ex', 'exit']:
                print("До свидания!")
                sys.exit()
            elif user_input.lower() in ['очистить', 'cls', 'clear']:
                await clear_terminal()
                continue
            elif user_input.lower() in ['модель', 'model']:
                await show_model()
                continue
            else:
                print(Fore.YELLOW + f"Ansi {model_name} LLM:" + Fore.WHITE, end=' ')
                if model_name == 'gpt-4o-mini' or not os.path.exists('config.ini'):
                    response = await communicate_with_model(user_input)
                elif model_name == 'KoboldAI':
                    response = await communicate_with_KoboldAI(user_input)
                elif model_name == 'Blackbox':
                    response = await communicate_with_BlackboxAI(user_input)
                elif model_name == 'ThinkAnyAI':
                    response = await communicate_with_ThinkAnyAI(user_input)
                elif model_name == 'Phind':
                    response = await communicate_with_Phind(user_input)
                elif model_name == 'Deepinfra':
                    response = await communicate_with_DeepInfra(user_input)
                else:
                    response = await communicate_with_model(user_input)

                await save_histoy(user_input, response)
                await print_flush3(response + "\n")

    except KeyboardInterrupt:
        print("\nПрограмма завершена пользователем.")

    except Exception as e:
        print(f"Внимание! Произошла ошибка: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())