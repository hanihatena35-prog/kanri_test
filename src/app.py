from flask import Flask, render_template, request, redirect, session, flash
from datetime import datetime, timedelta
import re
import os

app = Flask(__name__)
app.secret_key = "secret_key"

PASSWORD_FILE = os.path.join(os.path.dirname(__file__), "Settings", "パスワード.txt")

def load_password_from_file():
    """パスワード.txtからパスワードを読み込む"""
    if os.path.exists(PASSWORD_FILE):
        try:
            with open(PASSWORD_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return "Testpass1"  # デフォルトパスワード
    return "Testpass1"  # デフォルトパスワード

def save_password_to_file(password):
    """パスワードをパスワード.txtに保存"""
    try:
        os.makedirs(os.path.dirname(PASSWORD_FILE), exist_ok=True)
        with open(PASSWORD_FILE, "w", encoding="utf-8") as f:
            f.write(password)
    except Exception as e:
        print(f"パスワード保存エラー: {e}")

# 仮のユーザーデータ（本来はDB）
user_data = {
    "username": "testuser",
    "password": load_password_from_file(),
    "password_updated": datetime.now() - timedelta(days=80)  # 80日前に更新 → 期限間近
}

PASSWORD_EXPIRE_DAYS = 90
PASSWORD_WARNING_DAYS = 7


def is_valid_password(pw):
    """パスワードのバリデーション"""
    if len(pw) < 8:
        return False
    # 英大文字、英小文字、数字を全て含む必要がある
    if not re.search(r"[A-Z]", pw):
        return False
    if not re.search(r"[a-z]", pw):
        return False
    if not re.search(r"[0-9]", pw):
        return False
    if not re.match(r"^[A-Za-z0-9]+$", pw):
        return False
    return True


def check_password_expiry():
    """パスワード期限チェック"""
    last_update = user_data["password_updated"]
    expire_date = last_update + timedelta(days=PASSWORD_EXPIRE_DAYS)
    warning_date = expire_date - timedelta(days=PASSWORD_WARNING_DAYS)

    return datetime.now(), warning_date, expire_date


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username != user_data["username"] or password != user_data["password"]:
            flash("ユーザー名またはパスワードが違います")
            return render_template("login.html")

        now, warn, expire = check_password_expiry()

        session["username"] = username

        # 有効期限切れ
        if now > expire:
            flash("パスワードの有効期限が切れています。変更してください。")
            return redirect("/change_password")

        # 期限1週間前
        if now >= warn:
            flash("パスワードの有効期限が1週間以内です。変更を推奨します。")
            return redirect("/home")

        return redirect("/home")

    return render_template("login.html")


@app.route("/home")
def home():
    if "username" not in session:
        return redirect("/")
    return render_template("index.html")


@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "username" not in session:
        return redirect("/")

    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")

        # 現在のパスワード検証
        if current_pw != user_data["password"]:
            flash("現在のパスワードが一致しません")
            return render_template("change_password.html")

        # 新しいパスワードと確認用パスワードの一致確認
        if new_pw != confirm_pw:
            flash("新しいパスワードと確認用パスワードが一致しません")
            return render_template("change_password.html")

        # 新旧パスワードが同じでないか確認
        if new_pw == current_pw:
            flash("新しいパスワードは現在のパスワードと異なるものを設定してください")
            return render_template("change_password.html")

        # パスワードバリデーション
        if not is_valid_password(new_pw):
            flash("パスワードは8文字以上で英大文字・英小文字・数字を含める必要があります")
            return render_template("change_password.html")

        user_data["password"] = new_pw
        user_data["password_updated"] = datetime.now()
        
        # パスワードをファイルに保存
        save_password_to_file(new_pw)

        flash("パスワードを変更しました")
        return redirect("/index")

    return render_template("change_password.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
