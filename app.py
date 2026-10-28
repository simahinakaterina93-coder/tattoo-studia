from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash


# ==========================================
# НАСТРОЙКИ
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "alywawes.db")

app = Flask(__name__)


# ==========================================
# ПОДКЛЮЧЕНИЕ К БАЗЕ
# ==========================================

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# ==========================================
# СОЗДАНИЕ БАЗЫ
# ==========================================

def create_database():

    connection = get_db()

    # ======================================
    # ПОЛЬЗОВАТЕЛИ
    # ======================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'client',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ======================================
    # МАСТЕРА
    # ======================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS masters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT,
            photo TEXT
        )
    """)

    # ======================================
    # ЗАПИСИ
    # ======================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,
            master_id INTEGER,

            service TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,

            phone TEXT,

            status TEXT DEFAULT 'new',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (master_id)
                REFERENCES masters(id)
                ON DELETE SET NULL
        )
    """)

    # ======================================
    # СООБЩЕНИЯ
    # ======================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            client_id INTEGER NOT NULL,
            master_id INTEGER NOT NULL,

            sender_role TEXT NOT NULL,

            message TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (client_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (master_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # ======================================
    # МАСТЕРА
    # ======================================

    masters = [
        (
            1,
            "Лина Лифонова",
            "Blackwork",
            "lina.jpg"
        ),
        (
            2,
            "Даниил Киров",
            "Realism",
            "danill.jpg"
        ),
        (
            3,
            "Лилия Белова",
            "Fine Line",
            "liliya.jpg"
        )
    ]

    for master in masters:

        existing = connection.execute("""
            SELECT id
            FROM masters
            WHERE id = ?
        """, (master[0],)).fetchone()

        if not existing:

            connection.execute("""
                INSERT INTO masters (
                    id,
                    name,
                    specialization,
                    photo
                )
                VALUES (?, ?, ?, ?)
            """, master)

    connection.commit()
    connection.close()

    # ======================================
    # ИСПРАВЛЯЕМ MASTER_SLOTS
    # ======================================

    connection = get_db()

    table_exists = connection.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'master_slots'
    """).fetchone()

    if table_exists:

        columns = connection.execute("""
            PRAGMA foreign_key_list(master_slots)
        """).fetchall()

        wrong_table = False

        for column in columns:

            if column["table"] != "masters":
                wrong_table = True

        if wrong_table:

            print(
                "Исправление таблицы master_slots..."
            )

            connection.execute("""
                DROP TABLE master_slots
            """)

            connection.commit()

    # ======================================
    # СОЗДАЁМ MASTER_SLOTS
    # ======================================

    connection.execute("""
        CREATE TABLE IF NOT EXISTS master_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            master_id INTEGER NOT NULL,

            slot_date TEXT NOT NULL,
            slot_time TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(master_id, slot_date, slot_time),

            FOREIGN KEY (master_id)
                REFERENCES masters(id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()


# ==========================================
# АККАУНТЫ МАСТЕРОВ
# ==========================================

def create_master_accounts():

    connection = get_db()

    masters = [
        (
            "Лина Лифонова",
            "lina",
            "lina123"
        ),
        (
            "Даниил Киров",
            "daniil",
            "daniil123"
        ),
        (
            "Лилия Белова",
            "liliya",
            "liliya123"
        )
    ]

    for name, username, password in masters:

        existing = connection.execute("""
            SELECT id
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

        if not existing:

            connection.execute("""
                INSERT INTO users (
                    name,
                    username,
                    password,
                    role
                )
                VALUES (?, ?, ?, 'master')
            """, (
                name,
                username,
                generate_password_hash(password)
            ))

    connection.commit()
    connection.close()


# ==========================================
# ГЛАВНАЯ
# ==========================================

@app.route("/")
def index():

    return send_from_directory(
        BASE_DIR,
        "index.html"
    )


# ==========================================
# ФАЙЛЫ САЙТА
# ==========================================

@app.route("/<path:filename>")
def files(filename):

    return send_from_directory(
        BASE_DIR,
        filename
    )


# ==========================================
# РЕГИСТРАЦИЯ
# ==========================================

@app.route(
    "/api/register",
    methods=["POST"]
)
def register():

    data = request.get_json() or {}

    name = str(
        data.get("name", "")
    ).strip()

    username = str(
        data.get("username", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    if not name:

        return jsonify({
            "success": False,
            "message": "Введите имя"
        }), 400

    if not username:

        return jsonify({
            "success": False,
            "message": "Введите логин"
        }), 400

    if not password:

        return jsonify({
            "success": False,
            "message": "Введите пароль"
        }), 400

    connection = get_db()

    existing = connection.execute("""
        SELECT id
        FROM users
        WHERE username = ?
    """, (username,)).fetchone()

    if existing:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Такой логин уже существует"
        }), 400

    cursor = connection.execute("""
        INSERT INTO users (
            name,
            username,
            password,
            role
        )
        VALUES (?, ?, ?, 'client')
    """, (
        name,
        username,
        generate_password_hash(password)
    ))

    user_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Регистрация выполнена",
        "id": user_id,
        "name": name,
        "username": username,
        "role": "client"
    })


# ==========================================
# ВХОД
# ==========================================

@app.route(
    "/api/login",
    methods=["POST"]
)
def login():

    data = request.get_json() or {}

    username = str(
        data.get("username", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )

    if not username or not password:

        return jsonify({
            "success": False,
            "message": "Введите логин и пароль"
        }), 400

    connection = get_db()

    user = connection.execute("""
        SELECT
            id,
            name,
            username,
            password,
            role
        FROM users
        WHERE username = ?
    """, (username,)).fetchone()

    connection.close()

    if not user:

        return jsonify({
            "success": False,
            "message": "Неверный логин или пароль"
        }), 401

    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify({
            "success": False,
            "message": "Неверный логин или пароль"
        }), 401

    return jsonify({
        "success": True,
        "id": user["id"],
        "name": user["name"],
        "username": user["username"],
        "role": user["role"]
    })


# ==========================================
# ПОЛЬЗОВАТЕЛЬ
# ==========================================

@app.route(
    "/api/user/<username>",
    methods=["GET"]
)
def get_user(username):

    connection = get_db()

    user = connection.execute("""
        SELECT
            id,
            name,
            username,
            role,
            created_at
        FROM users
        WHERE LOWER(username) = ?
    """, (
        username.lower(),
    )).fetchone()

    connection.close()

    if not user:

        return jsonify({
            "success": False,
            "message": "Пользователь не найден"
        }), 404

    return jsonify({
        "success": True,
        "user": {
            "id": user["id"],
            "name": user["name"],
            "username": user["username"],
            "role": user["role"],
            "created_at": user["created_at"]
        }
    })


# ==========================================
# СВОБОДНЫЕ ДАТЫ — ПОЛУЧЕНИЕ
# ==========================================

@app.route(
    "/api/master/<int:master_id>/slots",
    methods=["GET"]
)
def get_master_slots(master_id):

    connection = get_db()

    master = connection.execute("""
        SELECT
            id,
            name
        FROM masters
        WHERE id = ?
    """, (
        master_id,
    )).fetchone()

    if not master:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Мастер не найден"
        }), 404

    slots = connection.execute("""
        SELECT
            id,
            slot_date,
            slot_time
        FROM master_slots
        WHERE master_id = ?
        ORDER BY slot_date, slot_time
    """, (
        master_id,
    )).fetchall()

    connection.close()

    return jsonify({
        "success": True,

        "master": {
            "id": master["id"],
            "name": master["name"]
        },

        "slots": [
            {
                "id": slot["id"],
                "slot_date": slot["slot_date"],
                "slot_time": slot["slot_time"]
            }
            for slot in slots
        ]
    })


# ==========================================
# СВОБОДНЫЕ ДАТЫ — ДОБАВЛЕНИЕ
# ==========================================

@app.route(
    "/api/master/<int:master_id>/slots",
    methods=["POST"]
)
def add_master_slot(master_id):

    data = request.get_json() or {}

    slot_date = str(
        data.get("slot_date", "")
    ).strip()

    slot_time = str(
        data.get("slot_time", "")
    ).strip()

    if not slot_date:

        return jsonify({
            "success": False,
            "message": "Не указана дата."
        }), 400

    if not slot_time:

        return jsonify({
            "success": False,
            "message": "Не указано время."
        }), 400

    connection = get_db()

    # ИЩЕМ МАСТЕРА ИМЕННО В ТАБЛИЦЕ masters

    master = connection.execute("""
        SELECT
            id,
            name,
            specialization
        FROM masters
        WHERE id = ?
    """, (
        master_id,
    )).fetchone()

    if not master:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Мастер не найден."
        }), 404

    # Проверяем, нет ли такой даты

    existing = connection.execute("""
        SELECT id
        FROM master_slots
        WHERE master_id = ?
        AND slot_date = ?
        AND slot_time = ?
    """, (
        master_id,
        slot_date,
        slot_time
    )).fetchone()

    if existing:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Такая дата уже опубликована."
        }), 400

    # Добавляем

    cursor = connection.execute("""
        INSERT INTO master_slots (
            master_id,
            slot_date,
            slot_time
        )
        VALUES (?, ?, ?)
    """, (
        master_id,
        slot_date,
        slot_time
    ))

    connection.commit()

    slot_id = cursor.lastrowid

    connection.close()

    return jsonify({
        "success": True,
        "message": "Свободная дата добавлена.",

        "slot": {
            "id": slot_id,
            "slot_date": slot_date,
            "slot_time": slot_time
        }
    })


# ==========================================
# СВОБОДНЫЕ ДАТЫ — УДАЛЕНИЕ
# ==========================================

@app.route(
    "/api/master/slots/<int:slot_id>",
    methods=["DELETE"]
)
def delete_master_slot(slot_id):

    connection = get_db()

    slot = connection.execute("""
        SELECT
            id,
            master_id,
            slot_date,
            slot_time
        FROM master_slots
        WHERE id = ?
    """, (
        slot_id,
    )).fetchone()

    if not slot:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Свободная дата не найдена."
        }), 404

    connection.execute("""
        DELETE FROM master_slots
        WHERE id = ?
    """, (
        slot_id,
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Свободная дата удалена."
    })


# ==========================================
# СОЗДАНИЕ ЗАПИСИ КЛИЕНТА
# ==========================================

@app.route(
    "/api/appointments",
    methods=["POST"]
)
def create_appointment():

    data = request.get_json() or {}

    user_id = data.get("user_id")
    master_id = data.get("master_id")

    service = str(
        data.get("service", "")
    ).strip()

    appointment_date = str(
        data.get("appointment_date", "")
    ).strip()

    appointment_time = str(
        data.get("appointment_time", "")
    ).strip()

    phone = str(
        data.get("phone", "")
    ).strip()

    if not user_id:

        return jsonify({
            "success": False,
            "message": "Не указан пользователь"
        }), 400

    if not master_id:

        return jsonify({
            "success": False,
            "message": "Не указан мастер"
        }), 400

    if not service:

        return jsonify({
            "success": False,
            "message": "Не указана услуга"
        }), 400

    if not appointment_date:

        return jsonify({
            "success": False,
            "message": "Не указана дата"
        }), 400

    if not appointment_time:

        return jsonify({
            "success": False,
            "message": "Не указано время"
        }), 400

    connection = get_db()

    # КЛИЕНТ

    user = connection.execute("""
        SELECT id
        FROM users
        WHERE id = ?
        AND role = 'client'
    """, (
        user_id,
    )).fetchone()

    if not user:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Клиент не найден"
        }), 404

    # МАСТЕР

    master = connection.execute("""
        SELECT
            id,
            name
        FROM masters
        WHERE id = ?
    """, (
        master_id,
    )).fetchone()

    if not master:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Выбранный мастер не найден"
        }), 404

    # СЛОТ

    slot = connection.execute("""
        SELECT
            id
        FROM master_slots
        WHERE master_id = ?
        AND slot_date = ?
        AND slot_time = ?
    """, (
        master_id,
        appointment_date,
        appointment_time
    )).fetchone()

    if not slot:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Это время уже занято или мастер его не публиковал."
        }), 400

    # СОЗДАЁМ ЗАПИСЬ

    cursor = connection.execute("""
        INSERT INTO appointments (
            user_id,
            master_id,
            service,
            appointment_date,
            appointment_time,
            phone
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        master_id,
        service,
        appointment_date,
        appointment_time,
        phone
    ))

    appointment_id = cursor.lastrowid

    # УДАЛЯЕМ СЛОТ

    connection.execute("""
        DELETE FROM master_slots
        WHERE id = ?
    """, (
        slot["id"],
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Запись создана",
        "appointment_id": appointment_id,
        "master_id": master_id
    })


# ==========================================
# ЗАПИСИ КЛИЕНТА
# ==========================================

@app.route(
    "/api/appointments/<int:user_id>",
    methods=["GET"]
)
def get_appointments(user_id):

    connection = get_db()

    appointments = connection.execute("""
        SELECT
            appointments.id,
            appointments.service,
            appointments.appointment_date,
            appointments.appointment_time,
            appointments.phone,
            appointments.status,

            masters.name AS master_name,
            masters.specialization AS specialization

        FROM appointments

        LEFT JOIN masters
        ON appointments.master_id = masters.id

        WHERE appointments.user_id = ?

        ORDER BY
            appointments.appointment_date,
            appointments.appointment_time
    """, (
        user_id,
    )).fetchall()

    connection.close()

    return jsonify({
        "success": True,

        "appointments": [
            {
                "id": appointment["id"],
                "service": appointment["service"],
                "date": appointment["appointment_date"],
                "time": appointment["appointment_time"],
                "phone": appointment["phone"],
                "status": appointment["status"],
                "master": appointment["master_name"],
                "specialization": appointment["specialization"]
            }

            for appointment in appointments
        ]
    })


# ==========================================
# ЗАПИСИ МАСТЕРА
# ==========================================

@app.route(
    "/api/master/<int:master_id>/appointments",
    methods=["GET"]
)
def get_master_appointments(master_id):

    connection = get_db()

    master = connection.execute("""
        SELECT
            id,
            name,
            specialization
        FROM masters
        WHERE id = ?
    """, (
        master_id,
    )).fetchone()

    if not master:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Мастер не найден"
        }), 404

    appointments = connection.execute("""
        SELECT
            appointments.id,
            appointments.service,
            appointments.appointment_date,
            appointments.appointment_time,
            appointments.phone,
            appointments.status,

            users.id AS client_id,
            users.name AS client_name,
            users.username AS client_username

        FROM appointments

        JOIN users
        ON appointments.user_id = users.id

        WHERE appointments.master_id = ?

        ORDER BY
            appointments.appointment_date,
            appointments.appointment_time
    """, (
        master_id,
    )).fetchall()

    connection.close()

    return jsonify({
        "success": True,

        "master": {
            "id": master["id"],
            "name": master["name"],
            "specialization": master["specialization"]
        },

        "appointments": [
            {
                "id": appointment["id"],
                "client_id": appointment["client_id"],
                "client_name": appointment["client_name"],
                "client_username": appointment["client_username"],
                "service": appointment["service"],
                "date": appointment["appointment_date"],
                "time": appointment["appointment_time"],
                "phone": appointment["phone"],
                "status": appointment["status"]
            }

            for appointment in appointments
        ]
    })


# ==========================================
# УДАЛЕНИЕ ЗАПИСИ
# ==========================================

@app.route(
    "/api/appointments/<int:appointment_id>",
    methods=["DELETE"]
)
def delete_appointment(appointment_id):

    connection = get_db()

    appointment = connection.execute("""
        SELECT
            id,
            master_id,
            appointment_date,
            appointment_time
        FROM appointments
        WHERE id = ?
    """, (
        appointment_id,
    )).fetchone()

    if not appointment:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Запись не найдена"
        }), 404

    # Возвращаем слот

    if appointment["master_id"]:

        connection.execute("""
            INSERT OR IGNORE INTO master_slots (
                master_id,
                slot_date,
                slot_time
            )
            VALUES (?, ?, ?)
        """, (
            appointment["master_id"],
            appointment["appointment_date"],
            appointment["appointment_time"]
        ))

    connection.execute("""
        DELETE FROM appointments
        WHERE id = ?
    """, (
        appointment_id,
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Запись удалена"
    })


# ==========================================
# ЧАТ — ПОЛУЧЕНИЕ
# ==========================================

@app.route(
    "/api/chat/<master_username>",
    methods=["GET"]
)
def get_chat(master_username):

    client_id = request.args.get("client_id")

    if not client_id:

        return jsonify({
            "success": False,
            "message": "Не указан ID клиента"
        }), 400

    connection = get_db()

    master = connection.execute("""
        SELECT
            id,
            name,
            username
        FROM users
        WHERE LOWER(username) = ?
        AND role = 'master'
    """, (
        master_username.lower(),
    )).fetchone()

    if not master:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Мастер не найден"
        }), 404

    client = connection.execute("""
        SELECT
            id,
            name,
            username
        FROM users
        WHERE id = ?
        AND role = 'client'
    """, (
        client_id,
    )).fetchone()

    if not client:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Клиент не найден"
        }), 404

    messages = connection.execute("""
        SELECT
            id,
            client_id,
            master_id,
            sender_role,
            message,
            created_at

        FROM messages

        WHERE client_id = ?
        AND master_id = ?

        ORDER BY id ASC
    """, (
        client["id"],
        master["id"]
    )).fetchall()

    connection.close()

    return jsonify({
        "success": True,

        "master": {
            "id": master["id"],
            "name": master["name"],
            "username": master["username"]
        },

        "client": {
            "id": client["id"],
            "name": client["name"],
            "username": client["username"]
        },

        "messages": [
            {
                "id": message["id"],
                "from": message["sender_role"],
                "text": message["message"],
                "time": message["created_at"]
            }

            for message in messages
        ]
    })


# ==========================================
# ЧАТ — СООБЩЕНИЕ КЛИЕНТА
# ==========================================

@app.route(
    "/api/chat/<master_username>",
    methods=["POST"]
)
def send_client_message(master_username):

    data = request.get_json() or {}

    client_id = data.get("client_id")

    message = str(
        data.get("message", "")
    ).strip()

    if not client_id:

        return jsonify({
            "success": False,
            "message": "Не указан ID клиента"
        }), 400

    if not message:

        return jsonify({
            "success": False,
            "message": "Сообщение не может быть пустым"
        }), 400

    connection = get_db()

    client = connection.execute("""
        SELECT
            id,
            name,
            username
        FROM users
        WHERE id = ?
        AND role = 'client'
    """, (
        client_id,
    )).fetchone()

    if not client:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Клиент не найден"
        }), 404

    master = connection.execute("""
        SELECT
            id,
            name,
            username
        FROM users
        WHERE LOWER(username) = ?
        AND role = 'master'
    """, (
        master_username.lower(),
    )).fetchone()

    if not master:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Мастер не найден"
        }), 404

    connection.execute("""
        INSERT INTO messages (
            client_id,
            master_id,
            sender_role,
            message
        )
        VALUES (?, ?, 'client', ?)
    """, (
        client["id"],
        master["id"],
        message
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Сообщение отправлено"
    })


# ==========================================
# ЧАТ — СООБЩЕНИЕ МАСТЕРА
# ==========================================

@app.route(
    "/api/master/chat/<master_username>",
    methods=["POST"]
)
def send_master_message(master_username):

    data = request.get_json() or {}

    client_id = data.get("client_id")

    message = str(
        data.get("message", "")
    ).strip()

    if not client_id:

        return jsonify({
            "success": False,
            "message": "Не указан клиент"
        }), 400

    if not message:

        return jsonify({
            "success": False,
            "message": "Сообщение не может быть пустым"
        }), 400

    connection = get_db()

    master = connection.execute("""
        SELECT
            id,
            name,
            username
        FROM users
        WHERE LOWER(username) = ?
        AND role = 'master'
    """, (
        master_username.lower(),
    )).fetchone()

    if not master:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Мастер не найден"
        }), 404

    client = connection.execute("""
        SELECT
            id,
            name,
            username
        FROM users
        WHERE id = ?
        AND role = 'client'
    """, (
        client_id,
    )).fetchone()

    if not client:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Клиент не найден"
        }), 404

    connection.execute("""
        INSERT INTO messages (
            client_id,
            master_id,
            sender_role,
            message
        )
        VALUES (?, ?, 'master', ?)
    """, (
        client["id"],
        master["id"],
        message
    ))

    connection.commit()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Ответ отправлен"
    })


# ==========================================
# СПИСОК ЧАТОВ МАСТЕРА
# ==========================================

@app.route(
    "/api/master/<master_username>/chats",
    methods=["GET"]
)
def get_master_chats(master_username):

    connection = get_db()

    master = connection.execute("""
        SELECT
            id,
            name,
            username
        FROM users
        WHERE LOWER(username) = ?
        AND role = 'master'
    """, (
        master_username.lower(),
    )).fetchone()

    if not master:

        connection.close()

        return jsonify({
            "success": False,
            "message": "Мастер не найден"
        }), 404

    clients = connection.execute("""
        SELECT DISTINCT
            users.id,
            users.name,
            users.username

        FROM messages

        JOIN users
        ON messages.client_id = users.id

        WHERE messages.master_id = ?

        AND users.role = 'client'

        ORDER BY users.name
    """, (
        master["id"],
    )).fetchall()

    result = []

    for client in clients:

        last_message = connection.execute("""
            SELECT
                message,
                sender_role,
                created_at

            FROM messages

            WHERE client_id = ?
            AND master_id = ?

            ORDER BY id DESC

            LIMIT 1
        """, (
            client["id"],
            master["id"]
        )).fetchone()

        result.append({

            "id": client["id"],

            "name": client["name"],

            "username": client["username"],

            "last_message": (
                last_message["message"]
                if last_message
                else ""
            ),

            "last_sender": (
                last_message["sender_role"]
                if last_message
                else ""
            ),

            "last_time": (
                last_message["created_at"]
                if last_message
                else ""
            )
        })

    connection.close()

    return jsonify({

        "success": True,

        "master": {
            "id": master["id"],
            "name": master["name"],
            "username": master["username"]
        },

        "clients": result
    })


# ==========================================
# ЗАПУСК
# ==========================================

create_database()
create_master_accounts()


if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
