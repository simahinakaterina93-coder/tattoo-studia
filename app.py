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

            role TEXT NOT NULL DEFAULT 'client',

            created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP

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
    # МАСТЕР ЛИНА
    # ======================================

    connection.execute("""
        INSERT OR IGNORE INTO masters
        (
            id,
            name,
            specialization,
            photo
        )

        VALUES
        (
            1,
            'Лина Лифонова',
            'Blackwork',
            'lina.jpg'
        )
    """)


    # ======================================
    # МАСТЕР ДАНИИЛ
    # ======================================

    connection.execute("""
        INSERT OR IGNORE INTO masters
        (
            id,
            name,
            specialization,
            photo
        )

        VALUES
        (
            2,
            'Даниил Киров',
            'Realism',
            'danill.jpg'
        )
    """)


    # ======================================
    # МАСТЕР ЛИЛИЯ
    # ======================================

    connection.execute("""
        INSERT OR IGNORE INTO masters
        (
            id,
            name,
            specialization,
            photo
        )

        VALUES
        (
            3,
            'Лилия Белова',
            'Fine Line',
            'liliya.jpg'
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

            status TEXT NOT NULL
                DEFAULT 'Ожидает подтверждения',

            created_at
                TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id),

            FOREIGN KEY (master_id)
                REFERENCES masters(id)

        )
    """)


    connection.commit()

    connection.close()


# ==========================================
# ГЛАВНАЯ
# ==========================================

@app.route("/")
def home():

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

    data = request.get_json()


    if not data:

        return jsonify({
            "success": False,
            "message": "Нет данных"
        }), 400


    name = data.get(
        "name",
        ""
    ).strip()


    username = data.get(
        "username",
        ""
    ).strip()


    password = data.get(
        "password",
        ""
    )


    if not name or not username or not password:

        return jsonify({
            "success": False,
            "message": "Заполните все поля"
        }), 400


    if len(password) < 6:

        return jsonify({
            "success": False,
            "message":
                "Пароль должен содержать минимум 6 символов"
        }), 400


    connection = get_db()


    # Проверяем логин

    existing_user = connection.execute(
        """
        SELECT id
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()


    if existing_user:

        connection.close()

        return jsonify({
            "success": False,
            "message":
                "Такой логин уже существует"
        }), 409


    # Хешируем пароль

    password_hash = generate_password_hash(
        password
    )


    # Создаём пользователя

    cursor = connection.execute(
        """
        INSERT INTO users
        (
            name,
            username,
            password,
            role
        )

        VALUES (?, ?, ?, ?)
        """,

        (
            name,
            username,
            password_hash,
            "client"
        )
    )


    user_id = cursor.lastrowid


    connection.commit()

    connection.close()


    return jsonify({

        "success": True,

        "message":
            "Регистрация прошла успешно",

        "user": {

            "id": user_id,

            "name": name,

            "username": username,

            "role": "client"

        }

    })


# ==========================================
# ВХОД
# ==========================================

@app.route(
    "/api/login",
    methods=["POST"]
)
def login():

    data = request.get_json()


    if not data:

        return jsonify({
            "success": False,
            "message": "Нет данных"
        }), 400


    username = data.get(
        "username",
        ""
    ).strip()


    password = data.get(
        "password",
        ""
    )


    if not username or not password:

        return jsonify({
            "success": False,
            "message":
                "Введите логин и пароль"
        }), 400


    connection = get_db()


    user = connection.execute(
        """
        SELECT
            id,
            name,
            username,
            password,
            role

        FROM users

        WHERE username = ?
        """,

        (username,)
    ).fetchone()


    connection.close()


    if not user:

        return jsonify({
            "success": False,
            "message":
                "Неверный логин или пароль"
        }), 401


    if not check_password_hash(
        user["password"],
        password
    ):

        return jsonify({
            "success": False,
            "message":
                "Неверный логин или пароль"
        }), 401


    return jsonify({

        "success": True,

        "message":
            "Вход выполнен",

        "user": {

            "id":
                user["id"],

            "name":
                user["name"],

            "username":
                user["username"],

            "role":
                user["role"]

        }

    })


# ==========================================
# СОЗДАНИЕ ЗАПИСИ
# ==========================================

@app.route(
    "/api/appointments",
    methods=["POST"]
)
def create_appointment():

    data = request.get_json()


    if not data:

        return jsonify({
            "success": False,
            "message": "Нет данных"
        }), 400


    user_id = data.get(
        "user_id"
    )


    username = data.get(
        "username",
        ""
    ).strip()


    master_id = data.get(
        "master_id"
    )


    service = data.get(
        "service"
    )


    appointment_date = data.get(
        "appointment_date"
    )


    appointment_time = data.get(
        "appointment_time"
    )


    phone = data.get(
        "phone"
    )


    # ======================================
    # ПРОВЕРКИ
    # ======================================

    if not service:

        return jsonify({
            "success": False,
            "message":
                "Услуга не выбрана"
        }), 400


    if not appointment_date:

        return jsonify({
            "success": False,
            "message":
                "Дата не выбрана"
        }), 400


    if not appointment_time:

        return jsonify({
            "success": False,
            "message":
                "Время не выбрано"
        }), 400


    if not phone:

        return jsonify({
            "success": False,
            "message":
                "Введите телефон"
        }), 400


    connection = get_db()


    # ======================================
    # ИЩЕМ ПОЛЬЗОВАТЕЛЯ ПО ID
    # ======================================

    user = None


    if user_id:

        user = connection.execute(
            """
            SELECT
                id,
                name,
                username

            FROM users

            WHERE id = ?
            """,

            (user_id,)
        ).fetchone()


    # ======================================
    # ЕСЛИ ID СТАРЫЙ —
    # ИЩЕМ ПО ЛОГИНУ
    # ======================================

    if not user and username:

        user = connection.execute(
            """
            SELECT
                id,
                name,
                username

            FROM users

            WHERE username = ?
            """,

            (username,)
        ).fetchone()


    # ======================================
    # ПОЛЬЗОВАТЕЛЬ НЕ НАЙДЕН
    # ======================================

    if not user:

        connection.close()

        return jsonify({

            "success": False,

            "message":
                "Пользователь не найден. Войдите в аккаунт заново."

        }), 404


    # ======================================
    # ПРОВЕРЯЕМ МАСТЕРА
    # ======================================

    if master_id:

        master = connection.execute(
            """
            SELECT id

            FROM masters

            WHERE id = ?
            """,

            (master_id,)
        ).fetchone()


        if not master:

            connection.close()

            return jsonify({

                "success": False,

                "message":
                    "Мастер не найден"

            }), 404


    # ======================================
    # СОХРАНЯЕМ ЗАПИСЬ
    # ======================================

    connection.execute(
        """
        INSERT INTO appointments
        (
            user_id,
            master_id,
            service,
            appointment_date,
            appointment_time,
            phone,
            status
        )

        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,

        (
            user["id"],
            master_id,
            service,
            appointment_date,
            appointment_time,
            phone,
            "Ожидает подтверждения"
        )
    )


    connection.commit()

    connection.close()


    return jsonify({

        "success": True,

        "message":
            "Запись успешно создана"

    })


# ==========================================
# ЗАПУСК БАЗЫ
# ==========================================

create_database()


# ==========================================
# ЗАПУСК FLASK
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
