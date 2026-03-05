#!/usr/bin/env python3
import os, time, json, threading, requests, itertools, sqlite3
from flask import Flask, request, render_template_string

app = Flask(__name__)

# === КОНФИГУРАЦИЯ ЧЕРЕЗ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ===
MAP_SERVICE = os.getenv('KERN_MAP_SERVICE', 'http://localhost:5002')
MISSION_DB = os.getenv('KERN_MISSIONS_DB', 'missions.db')

# === БАЗА ДАННЫХ ===
def init_db():
    conn = sqlite3.connect(MISSION_DB)
    conn.execute('''CREATE TABLE IF NOT EXISTS missions
                    (points TEXT, route TEXT, cost REAL, 
                     constraints TEXT, timestamp DATETIME)''')
    conn.commit()
    conn.close()

def save_mission(points, route, cost, constraints):
    conn = sqlite3.connect(MISSION_DB)
    conn.execute("INSERT INTO missions VALUES (?,?,?,?,datetime('now'))",
                 (str(points), str(route), cost, str(constraints)))
    conn.commit()
    conn.close()

@app.route('/missions/history')
def mission_history():
    conn = sqlite3.connect(MISSION_DB)
    rows = conn.execute("SELECT * FROM missions ORDER BY timestamp DESC LIMIT 10").fetchall()
    conn.close()
    return {'missions': [dict(zip(['points','route','cost','constraints','timestamp'], r)) for r in rows]}

# === ПРОКСИ ===
@app.route('/api/plan', methods=['POST'])
def proxy_plan():
    r = requests.post(f'{MAP_SERVICE}/plan', json=request.json, timeout=10)
    return r.json()

@app.route('/api/visualize', methods=['POST'])
def proxy_vis():
    r = requests.post(f'{MAP_SERVICE}/visualize', json=request.json, timeout=10)
    return r.json()

# === МИССИОННЫЙ ПЛАНИРОВЩИК ===
def plan_mission(points, home=(0, 0)):
    best_route, best_cost = None, float('inf')
    for order in itertools.permutations(points):
        current = home
        total_cost = 0
        valid = True
        for target in order:
            try:
                r = requests.post(f'{MAP_SERVICE}/plan',
                    json={'start': list(current), 'goal': list(target)}, timeout=5)
                if r.status_code != 200:
                    valid = False; break
                total_cost += r.json().get('cost', 999)
                current = tuple(target)
            except:
                valid = False; break
        if not valid: continue
        try:
            r = requests.post(f'{MAP_SERVICE}/plan',
                json={'start': list(current), 'goal': list(home)}, timeout=5)
            if r.status_code == 200:
                total_cost += r.json().get('cost', 999)
            else:
                continue
        except:
            continue
        if total_cost < best_cost:
            best_cost = total_cost
            best_route = order
    if best_route:
        save_mission(points, best_route, best_cost, {})
    return {'route': best_route, 'estimated_cost': round(best_cost, 2)} if best_route else {'error': 'no route'}

@app.route('/task/run', methods=['POST'])
def run_mission():
    data = request.json
    points = [tuple(p) for p in data['points']]
    home = tuple(data.get('home', [0, 0]))
    return plan_mission(points, home)

# === UI ===
@app.route('/')
def ui():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head><title>Керн: Личный ЦУП</title>
<style>
body{font-family:monospace;background:#000;color:#0f0;padding:1em;margin:0}
pre{background:#001100;padding:1em;overflow:auto;white-space:pre}
button{margin:5px;padding:8px;background:#0f0;color:#000;border:0;cursor:pointer}
</style>
</head>
<body>
<h2>Керн: Личный ЦУП</h2>
<button onclick="runMission()">Запустить миссию</button>
<button onclick="showMap()">Показать карту</button>
<button onclick="showHistory()">История миссий</button>
<pre id="out">Готов к работе.</pre>

<script>
async function runMission() {
    // Генерируем случайный seed для этой миссии
    const seed = Date.now() % 10000;

    const points = [[2,2],[5,3],[8,1]];
    const home = [0,0];

    // Функция для планирования одного сегмента с фиксированным seed
    async function planSegment(start, goal) {
        const resp = await fetch('/api/plan', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                start: start,
                goal: goal,
                width: 25,
                height: 25,
                seed: seed  // ← один seed на всю миссию!
            })
        });
        return await resp.json();
    }

    // Перебираем все маршруты (упрощённо — только один для демо)
    const route = [[2,2],[5,3],[8,1]]; // можно перебирать, но для демо фиксировано
    let totalCost = 0;
    let current = home;

    for (let target of route) {
        const data = await planSegment(current, target);
        totalCost += data.cost;
        current = target;
    }
    // Возврат домой
    const back = await planSegment(current, home);
    totalCost += back.cost;

    document.getElementById('out').textContent = 
        'Маршрут: ' + route.map(p => `[${p[0]},${p[1]}]`).join(' → ') +
        '\\nСтоимость: ' + totalCost.toFixed(2) +
        '\\nSeed: ' + seed;
}

async function showMap() {
    const plan = await fetch('/api/plan', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({start:[2,2], goal:[22,22], width:25, height:25, seed:42})
    }).then(r => r.json());

    const vis = await fetch('/api/visualize', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({grid: plan.grid, path: plan.path})
    }).then(r => r.json());

    document.getElementById('out').textContent = vis.ascii_map;
}

async function showHistory() {
    const hist = await fetch('/missions/history').then(r => r.json());
    let txt = 'Последние миссии:\\n';
    for (let m of hist.missions) {
        txt += `${m.route} | ${m.cost} | ${m.timestamp}\\n`;
    }
    document.getElementById('out').textContent = txt || 'Нет данных';
}
</script>
</body>
</html>
''')

if __name__ == '__main__':
    init_db()
    print(f"🚀 Оркестратор запущен")
    print(f"   MAP_SERVICE = {MAP_SERVICE}")
    print(f"   База: {MISSION_DB}")
    print(f"   UI: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
### Конец программы
