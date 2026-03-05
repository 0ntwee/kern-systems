from flask import Flask, request
import subprocess

app = Flask(__name__)

@app.route('/say')
def say():
    phrase = request.args.get('phrase', '')
    subprocess.run(['spd-say', '-o', 'rhvoice', '-y', 'aleksandr', phrase])
    return f'Said: {phrase}'

@app.route('/system/check')
def system_check():
    # Возвращает JSON с состоянием системы: загрузка CPU, свободная RAM, температура
    import psutil
    status = {
        'cpu_percent': psutil.cpu_percent(),
        'ram_free': psutil.virtual_memory().available,
        'online': True
    }
    return status

@app.route('/task', methods=['POST'])
def handle_task():
    import subprocess, sys, json
    task_data = request.get_json()
    # Запускаем map_task.py как подпроцесс
    proc = subprocess.run(
        [sys.executable, './map_task.py'],
        input=json.dumps(task_data),
        text=True,
        capture_output=True
    )
    return proc.stdout if proc.returncode == 0 else '{"error": "fail"}'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
