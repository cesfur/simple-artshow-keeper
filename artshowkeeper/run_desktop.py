import os
import winreg
import ctypes
import threading
import subprocess
import time
from urllib import request, error
from artshowkeeper import main

LOCK_FILE = 'artshowkeeper.lock'

def run_client(browser_executable=None):
    if browser_executable is None:
        return

    url = 'http://127.0.0.1:5000'
    while True:
        try:
            request.urlopen(url)
            break
        except error.HTTPError as e:
            print('Error: {0}'.format(e))
            break
        except error.URLError as e:
            time.sleep(1.0)
    subprocess.Popen([browser_executable, '-new-window', url])

def run_desktop():
    # get client browser
    browser_executable = None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\firefox.exe') as browser_key:
            browser_executable = winreg.QueryValueEx(browser_key, '')
            browser_executable = browser_executable[0]
    except WindowsError:
        pass
    if browser_executable is None or not os.path.isfile(browser_executable):
        ctypes.windll.user32.MessageBoxW(0, 'Prohlížeč Firefox nenalezen. Nelze pokračovat.', 'Artshow Keeper', 0x00 + 0x30)
        return

    # run client thread
    client_thread = threading.Thread(target=run_client, kwargs={'browser_executable': browser_executable})
    client_thread.start()

    # run server
    lock_file_path = os.path.join(main.config.DATA_FOLDER, LOCK_FILE)
    if os.path.isfile(lock_file_path):
        print('Server is already running.')
        client_thread.join()
    else:
        print('Starting server.')
        open(lock_file_path, 'w').close()
        main.run()
        os.remove(lock_file_path)

run_desktop()