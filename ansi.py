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
from packaging import version

init()  # Инициализация colorama

# Функция для удаления эмодзи (Unicode > 0xFFFF)
def remove_emojis(text):
    return re.sub(r'[\U00010000-\U0010ffff]', '', text)

def remove_sponsor_block(text):
    # Удаляет всё между **Sponsor и ---
    return re.sub(r'\*\*Sponsor.*?---', '', text, flags=re.DOTALL).strip()

CURRENT_VERSION = "1.3.4"
config_file = "config.ini"
ansi_folder = "C:\\ansi\\"
ansi_config_file_path = os.path.join(ansi_folder, config_file)

def update_app(update_url):
   webbrowser.open(update_url)

def check_for_updates():
    try:
        response = requests.get("https://api.github.com/repos/Processori7/ansi/releases/latest")
        response.raise_for_status()
        latest_release = response.json()

        assets = latest_release["assets"]
        for asset in assets:
            if asset["name"].endswith(".exe"):
                download_url = asset["browser_download_url"]
                break
        else:
            print("Не удалось найти файл exe для последней версии.")
            return

        latest_version_str = latest_release["tag_name"]
        match = re.search(r'\d+\.\d+', latest_version_str)
        latest_version = match.group() if match else latest_version_str

        if version.parse(latest_version) > version.parse(CURRENT_VERSION):
            ans = input(f"Доступна новая версия {latest_version}. Хотите обновить?\nВведите да - для обновления.\n>>> ").lower()
            if ans == 'да':
                update_app(download_url)
    except requests.exceptions.RequestException as e:
        print("Ошибка при проверке обновлений:", e)

async def read_config_from_drive_c():
    config = configparser.ConfigParser()
    try:
        config.read(ansi_config_file_path)
        if 'model' in config and 'name' in config['model']:
            return config.get('model', 'name').strip()
        else:
            return 'o3-mini'
    except Exception as e:
        print(f"Ошибка при чтении C:\\ansi\\config.ini: {e}")
        return 'o3-mini'

async def read_model_config():
    config = configparser.ConfigParser()
    try:
        if os.path.exists(ansi_config_file_path):
            config.read(ansi_config_file_path)
        else:
            config.read('config.ini')

        if 'model' in config and 'name' in config['model']:
            return config.get('model', 'name').strip()
        else:
            return 'o3-mini'
    except Exception as e:
        print(f"Ошибка при чтении config.ini: {e}")
        return 'o3-mini'

async def write_model_config(model_name):
    config = configparser.ConfigParser()
    config.add_section('model')
    config.set('model', 'name', str(model_name))
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

async def write_model_config_to_drive_c(model_name):
    config = configparser.ConfigParser()
    config.add_section('model')
    config.set('model', 'name', str(model_name))
    with open(ansi_config_file_path, 'w') as configfile:
        config.write(configfile)

async def show_model():
    use_model = await read_config_from_drive_c() if os.path.exists(ansi_config_file_path) else await read_model_config()
    print(f"Сейчас используется: {use_model}.\nДоступные модели:")
    model_names = await get_Polinations_chat_models()
    ans = input("Введите название выбранной модели: ").strip()
    if ans in model_names:
        if os.path.exists(ansi_config_file_path):
            await write_model_config_to_drive_c(ans)
        else:
            await write_model_config(ans)
        await print_flush2("Готово, модель добавлена в Config.ini\n")
        await main()
        return ans
    else:
        print("Ошибка! Пожалуйста, введите правильное имя модели.")
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
    try:
        subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)
    except Exception as e:
        print(f"Ошибка при очистке терминала: {e}")

async def print_flush2(text):
    cleaned_text = remove_emojis(text)
    for char in cleaned_text:
        sys.stdout.write(char)
        sys.stdout.flush()
    time.sleep(0.005)

async def print_flush3(text):
    cleaned_text = remove_emojis(text)
    cleaned_text = remove_sponsor_block(cleaned_text)
    for char in cleaned_text:
        sys.stdout.write(char)
        sys.stdout.flush()
    print()

async def print_history():
    history_file = os.path.join(ansi_folder, "history.txt")
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                for line in f:
                    cleaned_line = remove_emojis(line.strip())
                    cleaned_line = remove_sponsor_block(cleaned_line)
                    print(cleaned_line)
        except UnicodeDecodeError:
            print("Файл истории повреждён или записан в другой кодировке.")
            print("Попытка перечитать с автоматическим определением кодировки...")
            try:
                with open(history_file, "r", encoding="utf-8-sig") as f:
                    for line in f:
                        cleaned_line = remove_emojis(line.strip())
                        cleaned_line = remove_sponsor_block(cleaned_line)
                        print(cleaned_line)
            except Exception as e:
                print(f"Не удалось прочитать файл: {e}")
                print("Рекомендуется очистить историю командой 'cls'")
        ans = input("\nДля возврата в меню введите 'да' или 'yes'\nДля очистки истории введите cls: ")
        if ans.lower() in ['да', 'yes']:
            await main()
        elif ans.lower() == 'cls':
            os.remove(history_file)
            print("Готово")
            await main()
    else:
        print("Ой! История не найдена!\n")

async def save_histoy(user_input, response):
    history_file = os.path.join(ansi_folder, "history.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not os.path.exists(ansi_folder):
        os.makedirs(ansi_folder)
    cleaned_response = remove_sponsor_block(response)
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(f"Дата и время: {timestamp}\n"
                f"Вопрос пользователя: {user_input}\n"
                f"Ответ Ansi: {cleaned_response}\n\n")

async def communicate_with_Pollinations_chat(user_input, model):
    try:
        url = f"https://text.pollinations.ai/'{user_input}'?model={model}"
        resp = requests.get(url)

        if resp.ok:
            # Пытаемся распарсить JSON
            try:
                data = resp.json()  # Может быть JSON
                # Если это JSON и есть 'reasoning_content', возвращаем его без эмодзи
                return remove_emojis(data.get('reasoning_content', str(data)))  # fallback: выводим JSON как строку
            except requests.exceptions.JSONDecodeError:
                # Если не JSON, возвращаем обычный текст
                return remove_emojis(resp.text)
        else:
            return f"Ошибка сервера: {resp.status_code}"
    except Exception as e:
        return str(e)

async def get_Polinations_chat_models():
    names = []
    try:
        url = "https://text.pollinations.ai/models"
        resp = requests.get(url)
        if resp.ok:
            models = resp.json()
            for model in models:
                if isinstance(model, dict) and "name" in model:
                    model_name = model["name"]
                    model_description = model.get("description", "Без описания")
                    print(f"Название модели: {model_name} Описание: {model_description}")
                    names.append(str(model_name))
            return names
        else:
            print(f"Ошибка получения списка моделей: {resp.status_code}")
            return ["o3-mini"]
    except Exception as e:
        print(f"Ошибка при получении списка моделей: {e}")
        return ["o3-mini"]

async def main():
    """Основная функция программы."""
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            if not os.path.exists(ansi_folder):
                os.makedirs(ansi_folder)
                await add_to_path(ansi_folder)
            ansi_exe_path = os.path.join(ansi_folder, "ansi.exe")
            if not os.path.exists(ansi_exe_path):
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                source_path = os.path.join(desktop_path, "ansi.exe")
                shutil.copy(source_path, ansi_folder)

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
- Введите 'model' или 'модель', чтобы выбрать LLM из доступных.
""")

        while True:
            user_input = input(Fore.LIGHTGREEN_EX + "\nВы: " + Fore.WHITE)
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
                if model_name == 'o3-mini' and not os.path.exists('config.ini'):
                    response = await communicate_with_Pollinations_chat(user_input, 'o3-mini')
                else:
                    response = await communicate_with_Pollinations_chat(user_input, model_name)
                await save_histoy(user_input, response)
                await print_flush3(response + "\n")

    except KeyboardInterrupt:
        print("\nПрограмма завершена пользователем.")
    except Exception as e:
        print(f"Внимание! Произошла ошибка: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())