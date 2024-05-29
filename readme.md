# Описание
Это продвинутая версия pipboy: https://github.com/Processori7/pipboy  
Отличия: 
1. Ведение истории запросов и ответов.
2. При запуске файла с рабочего стола (не из папки) от имени администратора копирует файл в C:\ansi и добавлет его в пользовательскую переменную Path, поэтому просто в любой момент остается ввести в CMD: ansi и можно приступать к работе.
3. Эта версия никак не связана с Fallout, это просто дополнительный помощник при работе с командной строкой.
# Использование
1. Клонировать репозиторий:  
```git clone https://github.com/Processori7/ansi.git```
2. Перейти в папку:  
```cd /d ansi```
3. Создать виртуальное окружение:  
```python -m venv venv```
4. Активировать виртуальное окружение:  
```venv\Scripts\activate```
5. Установить зависимости:  
```pip install -r requirements.txt```
6. Запустить файл:  
```python ansi.py```