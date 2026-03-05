#!/usr/bin/env python3
import time
import subprocess
from datetime import datetime, time as dtime

while True:
    now = datetime.now().time()
    target = dtime(22, 10)
    if now.hour == target.hour and now.minute == target.minute:
        subprocess.run(['spd-say', '-o', 'rhvoice', '-y', 'aleksandr',
                        'Завершаю дневной цикл. Перехожу в режим ожидания'])
        time.sleep(60)  # чтобы не повторялось каждую секунду в течение минуты
    time.sleep(30)

### Конец программы
