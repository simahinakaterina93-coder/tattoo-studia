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
    return connection


# ==========================================
# СОЗДАНИЕ БАЗЫ
# ==========================================

def create_database():

    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'client',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


# ==========================================
# ГЛАВНАЯ СТРАНИЦА
# ==========================================

@app.route("/")
def home():

    return send_from_directory(
        BASE_DIR,
        "index.html"
    )


# ==========================================
# ОТКРЫТИЕ HTML / CSS / JS / IMAGES
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

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "Нет данных"
        }), 400


    name = data.get("name", "").strip()
    username = data.get("username", "").strip()
    password = data.get("password", "")


    if not name or not username or not password:

        return jsonify({
            "success": False,
            "message": "Заполните все поля"
        }), 400


    if len(password) < 6:

        return jsonify({
            "success": False,
            "message": "Пароль должен содержать минимум 6 символов"
        }), 400


    connection = get_db()


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
            "message": "Такой логин уже существует"
        }), 409


    password_hash = generate_password_hash(password)


    connection.execute(
        """
        INSERT INTO users
        (name, username, password, role)
        VALUES (?, ?, ?, ?)
        """,
        (
            name,
            username,
            password_hash,
            "client"
        )
    )


    connection.commit()
    connection.close()


    return jsonify({
        "success": True,
        "message": "Регистрация прошла успешно"
    })


# ==========================================
# ВХОД
# ==========================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "Нет данных"
        }), 400


    username = data.get("username", "").strip()
    password = data.get("password", "")


    if not username or not password:

        return jsonify({
            "success": False,
            "message": "Введите логин и пароль"
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

        "message": "Вход выполнен",

        "user": {

            "id": user["id"],

            "name": user["name"],

            "username": user["username"],

            "role": user["role"]

        }

    })


# ==========================================
# ЗАПУСК
# ==========================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
    
