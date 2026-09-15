import sqlite3

DB = 'traffic.db'

def conn():
    c = sqlite3.connect(DB)
    c.execute("PRAGMA foreign_keys = ON")
    return c

def init():
    c = conn().cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS cars(
            id INTEGER PRIMARY KEY AUTOINCREMENT, model TEXT NOT NULL,
            year INTEGER, color TEXT, speed REAL DEFAULT 0, driver TEXT);
        CREATE TABLE IF NOT EXISTS lights(
            id INTEGER PRIMARY KEY AUTOINCREMENT, location TEXT NOT NULL,
            state TEXT DEFAULT 'красный', last_switch DATETIME DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS signs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, sign_type TEXT NOT NULL,
            location TEXT, value REAL);
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT, car_id INTEGER, light_id INTEGER,
            sign_id INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_type TEXT NOT NULL, details TEXT,
            FOREIGN KEY(car_id) REFERENCES cars(id),
            FOREIGN KEY(light_id) REFERENCES lights(id),
            FOREIGN KEY(sign_id) REFERENCES signs(id));
    ''')
    c.connection.commit()
    c.connection.close()

# ---------- Красивый вывод таблицы ----------
def print_table(headers, rows):
    if not rows:
        print("Пусто")
        return
    str_rows = [[str(cell) if cell is not None else '' for cell in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    head = "|" + "|".join(f" {h:<{w}} " for h, w in zip(headers, widths)) + "|"
    print(sep); print(head); print(sep)
    for row in str_rows:
        print("|" + "|".join(f" {cell:<{w}} " for cell, w in zip(row, widths)) + "|")
    print(sep)

def add_car():
    try:
        m = input("Модель: ").strip()
        y = int(input("Год выпуска: "))
        col = input("Цвет: ").strip()
        d = input("Водитель: ").strip()
        c = conn(); cur = c.cursor()
        cur.execute("INSERT INTO cars(model,year,color,driver)VALUES(?,?,?,?)", (m, y, col, d))
        c.commit(); print(f"✓ Автомобиль '{m}' добавлен (ID: {cur.lastrowid})"); c.close()
    except Exception as e: print("Ошибка:", e)

def add_light():
    loc = input("Местоположение: ").strip()
    st = input("Состояние (красный/жёлтый/зелёный) [красный]: ").strip() or "красный"
    c = conn(); c.execute("INSERT INTO lights(location,state)VALUES(?,?)", (loc, st))
    c.commit(); c.close(); print("✓ Светофор добавлен")

def add_sign():
    t = input("Тип знака (STOP/SPEED_LIMIT/PEDESTRIAN/NO_ENTRY): ").strip()
    loc = input("Местоположение: ").strip()
    v = input("Значение (Enter — нет): ").strip()
    c = conn(); c.execute("INSERT INTO signs(sign_type,location,value)VALUES(?,?,?)",
                          (t, loc, float(v) if v else None))
    c.commit(); c.close(); print("✓ Дорожный знак добавлен")

def add_event():
    try:
        cid = int(input("ID автомобиля: "))
        et = input("Тип события (проезд/остановка/нарушение/переключение/авария): ").strip()
        det = input("Описание: ").strip()
        c = conn(); cur = c.cursor()
        cur.execute("SELECT id FROM cars WHERE id=?", (cid,))
        if not cur.fetchone(): print("Нет такого авто"); c.close(); return
        cur.execute("INSERT INTO events(car_id,event_type,details)VALUES(?,?,?)", (cid, et, det))
        c.commit(); print(f"✓ Событие добавлено (ID: {cur.lastrowid})"); c.close()
    except Exception as e: print("Ошибка:", e)

def show_cars():
    c = conn(); rows = c.execute("SELECT id,model,year,color,speed,driver FROM cars").fetchall(); c.close()
    print("\nВСЕ АВТОМОБИЛИ")
    print_table(["ID", "Модель", "Год", "Цвет", "Скорость", "Водитель"], rows)

def show_events():
    c = conn()
    rows = c.execute('''SELECT e.id,e.timestamp,e.event_type,c.model,e.details
                        FROM events e LEFT JOIN cars c ON e.car_id=c.id
                        ORDER BY e.timestamp DESC''').fetchall()
    c.close(); print("\nПОЛНЫЙ ЛОГ СОБЫТИЙ")
    print_table(["ID", "Время", "Тип", "Авто", "Описание"], rows)

def show_accidents():
    c = conn()
    rows = c.execute('''SELECT e.id,e.timestamp,c.model,e.details
                        FROM events e LEFT JOIN cars c ON e.car_id=c.id
                        WHERE e.event_type='авария'
                        ORDER BY e.timestamp DESC''').fetchall()
    c.close(); print("\nВСЕ АВАРИИ")
    print_table(["ID", "Время", "Авто", "Описание"], rows)

def stats():
    c = conn()
    g = lambda q: c.execute(q).fetchone()[0]
    cars = g("SELECT COUNT(*) FROM cars"); lights = g("SELECT COUNT(*) FROM lights")
    signs = g("SELECT COUNT(*) FROM signs"); ev = g("SELECT COUNT(*) FROM events")
    viol = g("SELECT COUNT(*) FROM events WHERE event_type='нарушение'")
    pas = g("SELECT COUNT(*) FROM events WHERE event_type='проезд'")
    acc = g("SELECT COUNT(*) FROM events WHERE event_type='авария'")
    avg = c.execute("SELECT AVG(speed) FROM cars").fetchone()[0] or 0
    viol_cars = c.execute('''SELECT DISTINCT c.model FROM cars c
                             JOIN events e ON e.car_id=c.id
                             WHERE e.event_type='нарушение' ''').fetchall()
    acc_cars = c.execute('''SELECT DISTINCT c.model FROM cars c
                            JOIN events e ON e.car_id=c.id
                            WHERE e.event_type='авария' ''').fetchall()
    c.close()
    print("\nСТАТИСТИКА БАЗЫ ДАННЫХ")
    print("-" * 45)
    print(f"Автомобилей:      {cars}")
    print(f"Светофоров:       {lights}")
    print(f"Дорожных знаков:  {signs}")
    print(f"Событий:          {ev}")
    print(f"  — Нарушений:    {viol}")
    print(f"  — Проездов:     {pas}")
    print(f"  — Аварий:       {acc}")
    print(f"Средняя скорость: {avg:.1f} км/ч")
    vc = ", ".join([x[0] for x in viol_cars]) if viol_cars else "нет"
    ac = ", ".join([x[0] for x in acc_cars]) if acc_cars else "нет"
    print(f"Авто с нарушениями: {len(viol_cars)} ({vc})")
    print(f"Авто в авариях:     {len(acc_cars)} ({ac})")
    print("-" * 45)

def update_speed():
    try:
        cid = int(input("ID автомобиля: ")); sp = float(input("Новая скорость (км/ч): "))
        c = conn(); c.execute("UPDATE cars SET speed=? WHERE id=?", (sp, cid))
        if c.total_changes == 0: print("Нет такого авто")
        else: print(f"✓ Скорость авто ID={cid} обновлена на {sp} км/ч")
        c.commit(); c.close()
    except Exception as e: print("Ошибка:", e)

def search_model():
    p = input("Часть модели: ").strip()
    c = conn(); rows = c.execute("SELECT id,model,year,color,driver FROM cars WHERE model LIKE ?",
                                 (f"%{p}%",)).fetchall(); c.close()
    print("\nРЕЗУЛЬТАТЫ ПОИСКА")
    print_table(["ID", "Модель", "Год", "Цвет", "Водитель"], rows)

def search_type():
    t = input("Тип события (проезд/остановка/нарушение/переключение/авария): ").strip()
    c = conn(); rows = c.execute('''SELECT e.id,e.timestamp,c.model,e.details FROM events e
                                    LEFT JOIN cars c ON e.car_id=c.id
                                    WHERE e.event_type=? ORDER BY e.timestamp DESC''', (t,)).fetchall()
    c.close(); print("\nРЕЗУЛЬТАТЫ ПОИСКА")
    print_table(["ID", "Время", "Авто", "Описание"], rows)

def search_date():
    d = input("Дата (YYYY-MM-DD): ").strip()
    c = conn(); rows = c.execute('''SELECT e.id,e.timestamp,e.event_type,c.model FROM events e
                                    LEFT JOIN cars c ON e.car_id=c.id
                                    WHERE DATE(e.timestamp)=? ORDER BY e.timestamp DESC''', (d,)).fetchall()
    c.close(); print("\nРЕЗУЛЬТАТЫ ПОИСКА")
    print_table(["ID", "Время", "Тип", "Авто"], rows)

def search_by_car():
    try:
        cid = int(input("ID автомобиля: "))
        c = conn(); rows = c.execute('''SELECT e.id,e.timestamp,e.event_type,e.details
                                        FROM events e WHERE e.car_id=?
                                        ORDER BY e.timestamp DESC''', (cid,)).fetchall(); c.close()
        print("\nРЕЗУЛЬТАТЫ ПОИСКА")
        print_table(["ID", "Время", "Тип", "Описание"], rows)
    except Exception as e: print("Ошибка:", e)

def search_violators():
    c = conn()
    rows = c.execute('''SELECT DISTINCT c.id,c.model,c.driver FROM cars c
                        JOIN events e ON e.car_id=c.id WHERE e.event_type='нарушение' ''').fetchall()
    c.close(); print("\nАВТОМОБИЛИ С НАРУШЕНИЯМИ")
    print_table(["ID", "Модель", "Водитель"], rows)

def menu():
    print("\n" + "=" * 60)
    print("СИСТЕМА УПРАВЛЕНИЯ ДОРОЖНЫМ ДВИЖЕНИЕМ")
    print("=" * 60)
    print("ОСНОВНЫЕ ОПЕРАЦИИ:")
    print("  1. Добавить автомобиль")
    print("  2. Добавить светофор")
    print("  3. Добавить дорожный знак")
    print("  4. Добавить событие")
    print("  5. Показать все автомобили")
    print("  6. Показать статистику")
    print("  7. Показать полный лог событий")
    print("  8. Обновить скорость автомобиля")
    print("\nПОИСК:")
    print("  9. Поиск автомобиля по модели")
    print(" 10. Поиск событий по типу")
    print(" 11. Поиск событий по дате")
    print(" 12. Поиск нарушений по автомобилю")
    print(" 13. Поиск автомобилей с нарушениями")
    print(" 14. Показать все аварии")
    print("\n  0. Выход")
    print("=" * 60)

def main():
    init()
    actions = {'1':add_car, '2':add_light, '3':add_sign, '4':add_event,
               '5':show_cars, '6':stats, '7':show_events, '8':update_speed,
               '9':search_model, '10':search_type, '11':search_date,
               '12':search_by_car, '13':search_violators, '14':show_accidents}
    while True:
        menu()
        ch = input("Выберите действие: ").strip()
        if ch == '0': print("Выход."); break
        if ch in actions: actions[ch]()
        else: print("Неверный ввод.")

if __name__ == "__main__":
    main()