import os

from dotenv import load_dotenv

load_dotenv()

if os.environ.get("RUN_MAIN_SCRIPT"):
    # Запуск основного скрипта
    import main
else:
    # Запуск другого скрипта
    # import other_script
