import sys
import json
import os
import datetime
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QComboBox, QDialog, QFormLayout, QMessageBox
)
import socket
from plyer import notification
from plyer.platforms.win.notification import WindowsNotification
import pygame
import os
import datetime
import webbrowser


weekday = datetime.datetime.now().weekday()

html_path = "https://www.github.com/Wakana-0/TeachConnect/releases"


def debug_log(message):
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def log_error(message):
    debug_log(f"记录错误: {message}")
    log_file = os.path.join(LOG_PATH, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))
    log_entry = f"[{datetime.datetime.now()}] ERROR: {message}\n"


if weekday == 6:
    webbrowser.open(html_path)
    notification.notify(
        title="升级提醒",
        message="请将 TeachConect 客户端更新到最新版本！",
        timeout=5  # 通知显示的时长
    )



# 初始化pygame的混音器
try:
    pygame.mixer.init()
except Exception as e:
    log_error(e)
    debug_log('初始化混音器失败',e)
    notification.notify(
        title="发生错误（非致命错误）",
        message=f"播放音频时发生错误: {e}，尝试连接音频设备以解决错误",
        timeout=5  # 通知显示的时长
    )


# 播放提示音
def play_notification_sound():
    try:
        sound = pygame.mixer.Sound('sound.mp3')
        sound.play()
    except Exception as e:
        log_error(e)
        print(f"播放音频时发生错误: {e}")

# 设置调试模式，True为启用调试，False为禁用
DEBUG_MODE = True

# 设置存储路径
APP_DATA_PATH = os.path.join(os.getenv("APPDATA"), "TConect")
USER_DATA_PATH = os.path.join(APP_DATA_PATH, "User")
LOG_PATH = os.path.join(APP_DATA_PATH, "log")
CACHE_PATH = os.path.join(APP_DATA_PATH, "cache")
IP_STORAGE_FILE = os.path.join(CACHE_PATH, "IPs.json")
NAME_STORAGE_FILE = os.path.join(CACHE_PATH, "Names.json")
USER_CREDENTIALS_FILE = os.path.join(USER_DATA_PATH, "UserIFMT.json")

# 确保目录存在
for path in [USER_DATA_PATH, LOG_PATH, CACHE_PATH]:
    os.makedirs(path, exist_ok=True)


def load_recent_data(filepath):
    debug_log(f"加载文件: {filepath}")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            debug_log(f"加载成功: {data}")
            return data
    debug_log("文件不存在，返回空字典")
    return {}


def save_recent_data(filepath, data):
    debug_log(f"保存数据到 {filepath}，数据: {data}")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def log_message(ip, name, message):
    log_file = os.path.join(LOG_PATH, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))
    log_entry = f"[{datetime.datetime.now()}] IP: {ip}, Name: {name}, Message: {message}\n"
    debug_log(f"记录日志: {log_entry}")
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(log_entry)



class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("登录")
        layout = QFormLayout()

        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.login_button = QPushButton("登录")
        self.login_button.clicked.connect(self.check_credentials)

        self.register_button = QPushButton("注册")
        self.register_button.clicked.connect(self.register_user)

        layout.addRow("用户名:", self.username_input)
        layout.addRow("密码:", self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)

        self.setLayout(layout)
        self.result = None

        # 检查是否已有用户数据
        self.check_if_registered()

    def check_if_registered(self):
        """检查是否已有用户数据"""
        if os.path.exists(USER_CREDENTIALS_FILE):
            users = load_recent_data(USER_CREDENTIALS_FILE)
            if users:  # 如果存在已注册的用户
                self.register_button.setEnabled(False)  # 禁用注册按钮
                self.register_button.setText("已注册")  # 显示“已注册”文字

    def check_credentials(self):
        users = load_recent_data(USER_CREDENTIALS_FILE)
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if username in users and users[username] == password:
            self.result = username
            self.accept()
        else:
            QMessageBox.warning(self, "错误", "用户名或密码错误！")
            self.username_input.clear()
            self.password_input.clear()

    def register_user(self):
        # 仅在未注册的情况下允许注册
        users = load_recent_data(USER_CREDENTIALS_FILE)
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "错误", "用户名和密码不能为空！")
            return

        if username in users:
            QMessageBox.warning(self, "错误", "用户名已存在！")
        else:
            users[username] = password
            save_recent_data(USER_CREDENTIALS_FILE, users)
            QMessageBox.information(self, "成功", "注册成功！")
            self.register_button.setEnabled(False)  # 禁用注册按钮
            self.register_button.setText("已注册")  # 显示“已注册”文字



class MessagingApp(QWidget):
    def __init__(self, username):
        super().__init__()
        self.setWindowTitle("消息发送")
        self.setGeometry(100, 100, 300, 200)
        self.username = username

        # 加载最近使用的 IP 和名称
        self.recent_ips = load_recent_data(IP_STORAGE_FILE)
        self.recent_names = load_recent_data(NAME_STORAGE_FILE)

        layout = QVBoxLayout()

        self.label_name = QLabel("名称:")
        self.name_input = QComboBox()
        self.name_input.setEditable(True)
        self.name_input.addItems(self.recent_names.keys())

        self.label_ip = QLabel("服务器 IP:")
        self.ip_input = QComboBox()
        self.ip_input.setEditable(True)
        self.update_ip_input()  # 初次加载 IP

        self.label_message = QLabel("消息:")
        self.message_input = QLineEdit()

        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_message)


        layout.addWidget(self.label_name)
        layout.addWidget(self.name_input)
        layout.addWidget(self.label_ip)
        layout.addWidget(self.ip_input)
        layout.addWidget(self.label_message)
        layout.addWidget(self.message_input)
        layout.addWidget(self.send_button)

        self.setLayout(layout)

        # 保存当前选中的 IP
        self.selected_ip = None


    def send_message(self):
        name = self.name_input.currentText().strip()
        ip_with_note = self.ip_input.currentText().strip()
        message = self.message_input.text().strip()

        # 检查必要字段是否填写
        if not name or not ip_with_note or not message:
            return

        # 从 "备注 - IP" 格式中分离出备注和 IP
        try:
            note, ip = ip_with_note.split(" - ", 1)
        except ValueError as e:
            log_error(e)
            try:
                note, ip = ip_with_note.split("-", 1)
            except ValueError:
                QMessageBox.warning(self, "错误", "IP 格式无效！")
                return

        # 保存当前选中的 IP
        self.selected_ip = ip_with_note

        # 保存最近使用的名称
        if name not in self.recent_names:
            self.recent_names[name] = True
            save_recent_data(NAME_STORAGE_FILE, self.recent_names)

        # 更新备注，并保存
        self.recent_ips[ip] = note  # 更新 IP 的备注
        save_recent_data(IP_STORAGE_FILE, self.recent_ips)

        # 记录日志
        log_message(ip, name, message)




        # 发送数据
        data = json.dumps({"name": name, "message": message})
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, 11223))
                s.sendall(data.encode("utf-8"))
                play_notification_sound()
                self.cooling_time = 10
                QMessageBox.information(self, "发送成功", "消息已成功发送")
        except Exception as e:
            log_error(e)
            QMessageBox.critical(self, "发送失败", f"发送失败：请检查网络连接或目标教室未启动程序\n错误信息: {e}")

        # 重新加载 IP 并保持之前选中的 IP
        self.recent_ips = load_recent_data(IP_STORAGE_FILE)
        self.update_ip_input()

        # 恢复之前选中的 IP
        if self.selected_ip:
            index = self.ip_input.findText(self.selected_ip)
            if index != -1:
                self.ip_input.setCurrentIndex(index)




    def update_ip_input(self):
        self.ip_input.clear()  # 清空当前的 IP 输入项
        for ip, note in self.recent_ips.items():
            self.ip_input.addItem(f"{note} - {ip}", ip)





if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginDialog()
    if login.exec() == QDialog.DialogCode.Accepted:
        window = MessagingApp(login.result)
        window.show()
        sys.exit(app.exec())
