import socket
import json
import os
from plyer import notification
from plyer.platforms.win.notification import WindowsNotification
import pygame
import datetime
import time

# 设置存储路径
APP_DATA_PATH = os.path.join(os.getenv("APPDATA"), "TConect")
LOG_PATH = os.path.join(APP_DATA_PATH, "log")
CACHE_PATH = os.path.join(APP_DATA_PATH, "cache")

running_path = os.path.dirname(os.path.abspath(__file__))

DEBUG_MODE = True

def debug_log(message):
    if DEBUG_MODE:
        print(f"[DEBUG] {message}")

def log_message(ip, name, message):
    log_file = os.path.join(LOG_PATH, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))
    log_entry = f"[{datetime.datetime.now()}] IP: {ip}, Name: {name}, Message: {message}\n"
    debug_log(f"记录日志: {log_entry}")
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(log_entry)


def log_error(message):
    debug_log(f"记录错误: {message}")
    log_file = os.path.join(LOG_PATH, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S.log"))
    log_entry = f"[{datetime.datetime.now()}] ERROR: {message}\n"

# 初始化pygame的混音器
pygame.mixer.init()

# 播放提示音
def play_notification_sound():
    try:
        sound = pygame.mixer.Sound(f'{running_path}\\sound\\sound.mp3')
        sound.play()
    except Exception as e:
        log_error(e)
        notification.notify(
            title="错误! | Error!",
            message=f"播放音频时发生错误: {e}",
            timeout=4  # 通知显示的时长
        )


def save_to_system_log(name, message):
    log_file = os.path.join(os.getenv("APPDATA"), "MessagingApp", "message_log.txt")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{name}: {message}\n")


def start_server():
    ipdrss = socket.gethostbyname(socket.gethostname())

    print(f"服务器已启动，IP地址为 {ipdrss}")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("0.0.0.0", 11224))  # 允许所有IP访问
        server.listen()
        print("开始接收消息")

        while True:
            try:
                # 等待客户端连接
                conn, addr = server.accept()
                print(f"客户端 {addr} 已连接")
                with conn:
                    # 接收消息
                    data = conn.recv(1024)
                    if not data:
                        continue

                    try:
                        sd = False
                        # 尝试解析收到的JSON数据
                        msg = json.loads(data.decode("utf-8"))
                        name = msg.get("name", "未知")
                        message = msg.get("message", "无内容")
                        print(f"接收到消息: {addr}")
                        data = json.dumps({"name": name, "message": message})

                        # 尝试连接CW插件
                        try:
                            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                                s.connect(('127.0.0.1', 11223)) #CW插件端口
                                s.sendall(data.encode("utf-8"))
                                sd = True
                        except Exception as e:
                            log_error(e)
                            print(f"连接CW插件时发生错误: {e}")

                        # 使用 plyer 弹出通知
                        notification.notify(
                            title=name,
                            message=message,
                            timeout=15  # 通知显示的时长
                        )
                        print(f"接收到消息: {message}")

                        # 播放通知声音
                        if sd != True:
                            play_notification_sound()

                        # 保存到系统消息日志
                        save_to_system_log(name, message)

                    except json.JSONDecodeError as e:
                        log_error(e)
                        print("接收到无法解析的消息")
                    except Exception as e:
                        log_error(e)
                        print(f"处理消息时发生错误: {e}")

            except Exception as e:
                log_error(e)
                print(f"服务器发生错误: {e}")
                # 在发生异常时，服务器仍然继续运行


if __name__ == "__main__":
    start_server()
