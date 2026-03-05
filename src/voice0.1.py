#!/usr/bin/env python3
import os, random

phrases = ["Системы в норме", "Запускаю протокол", "Warning", "Пожалуйста, отойдите"]

os.system(f"espeak-ng -v ru -p 20 -s 130 -a 200 '{random.choice(phrases)}'")
### Конец программы
