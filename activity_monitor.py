import tkinter as tk
from AppKit import NSWorkspace
from pynput import keyboard, mouse
from datetime import datetime
from pandas import DataFrame
import os
import subprocess


LOG_FILE_PATH = os.path.join(os.path.expanduser('~'), 'Desktop', 'activity_log')
# LOG_FILE_PATH = os.path.join('.', 'activity_log')

# TODO: add support for other browsers
BROWSERS = ['Google Chrome'] # 'Safari', 'Firefox']

class AppleScriptRunner:

    vscode_active_file_script = """
        tell application "Code"
            set activeEditor to window 1
            set activeFile to file of activeEditor
            set fileName to name of activeFile
        end tell
        return fileName
    """

    def _browser_tab_script(self, browser):
        return f"""
            tell application "{browser}"
                set activeWindow to front window
                set activeTab to active tab of activeWindow
                set tabTitle to title of activeTab
            end tell
            return tabTitle
        """

    def get_active_browser_tab(self, browser):
        try:
            return self._run_script(self._browser_tab_script(browser))
        except Exception as e:
            print('Error getting active browser tab: ', e)
            return None

    def get_active_vscode_file(self):
        try:
            return self._run_script(self.vscode_active_file_script)
        except Exception as e:
            print('Error getting active VS Code file: ', e)
            return None

    def _run_script(self, script):
        result = subprocess.check_output(['osascript', '-e', script], universal_newlines=True).strip()
        return result

class AppMonitor:
    def __init__(self):
        self.last_app = None
        self.current_app = None
        self.start_time = None
        self.workspace = NSWorkspace.sharedWorkspace()
        self.activity_log = []
        self.listeners = []
        self.monitoring = False
        self.script_runner = AppleScriptRunner()
        self.info = tk.StringVar()  # Add a StringVar to store the info variable
        self.info.set('press start to begin monitoring')


    def get_active_app(self):
        try:
            active_app = self.workspace.activeApplication()['NSApplicationName']
            if active_app in BROWSERS:
                active_app = self.get_active_browser_tab(active_app)
            # TODO: add VS Code support
            # if active_app == 'Code':
            #     active_app = self.get_active_vscode_file(active_app)
            return active_app
        except Exception as e:
            print(f'error getting getting app: {e}')
            self.info.set(f'error getting getting app: {e}' )
        return

    def get_active_browser_tab(self, active_app):
        try:
            if active_app in BROWSERS:
                tab = self.script_runner.get_active_browser_tab(active_app)
                return tab
            else:
                return None
        except Exception as e:
            print('Error getting active browser tab: ', e)
            self.info.set(f'Error getting active browser tab: {e}')
            return None

    def get_active_chrome_tab(self, active_app):
        try:
            if active_app == 'Google Chrome':
                tab = self.script_runner.get_active_chrome_tab()
                return tab
            else:
                return None
        except Exception as e:
            print('Error getting active Chrome tab: ', e)
            self.info.set(f'Error getting active Chrome tab: {e}')
            return None

    def get_active_vscode_file(self, active_app):
        try:
            if active_app == 'Code':
                file_name = self.script_runner.get_active_vscode_file()
                return file_name
            else:
                return None
        except Exception as e:
            print('Error getting active VS Code file: ', e)
            self.info.set(f'Error getting active VS Code file: {e}')
            return None

    def log_activity(self):
        app = self.get_active_app()
        print(app)
        self.info.set(f'current app: {app}')
        if app != self.last_app:
            if self.last_app is None:
                self.last_app = app
                self.start_time = datetime.now()
                return
            current_time = datetime.now()
            active_time = current_time - self.start_time
            self.activity_log.append({'app': self.last_app, 'time': self.format_duration(active_time.total_seconds())})
            self.last_app = app
            self.start_time = current_time

    def format_duration(self, total_seconds):
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{int(hours)}:{int(minutes):02d}:{int(seconds):02d}'

    def output_log(self):
        current_time = datetime.now()
        if self.last_app is not None and self.start_time is not None:
            active_time = current_time - self.start_time
            if len(self.activity_log) > 0:
                self.activity_log[-1]['time'] = self.format_duration(active_time.total_seconds())
            else:
                self.activity_log.append({'app': self.last_app, 'time': self.format_duration(active_time.total_seconds())})
        df = DataFrame(self.activity_log)
        path = LOG_FILE_PATH+'_'+current_time.strftime('%H-%M-%S')+'.csv'
        print('writing log to ', path)
        self.info.set(f'writing log to {path}')
        df.to_csv(path, index=False)

    def on_press(self, key):
        self.log_activity()

    def on_click(self, x, y, button, pressed):
        if pressed:
            self.log_activity()

    def on_scroll(self, x, y, dx, dy):
        self.log_activity()

    def key_listener(self):
        listener = keyboard.Listener(
        on_press=self.on_press,
        on_release=None)
        listener.start()
        listener.wait()
        return listener

    def mouse_listener(self):
        listener = mouse.Listener(
            on_click=self.on_click, on_scroll=self.on_scroll)
        listener.start()
        listener.wait()
        return listener

    def start(self):
        try:
            self._start_listeners()
            self.monitoring = True
        except KeyboardInterrupt:
            print("KeyboardInterrupt detected. Outputting log...")
            self.output_log()


    def _start_listeners(self):
        mouse_listener = self.mouse_listener()
        self.listeners.append(mouse_listener)
        # key_listener is causing an error - think it's a threading issue
        # mouse listener might be sufficient for now
        # key_listener = self.key_listener()
        # self.listeners.append(key_listener)

    def _stop_listeners(self):
        for listener in self.listeners:
            listener.stop()

    def stop(self):
        if self.last_app is not None and self.start_time is not None:
            current_time = datetime.now()
            active_time = current_time - self.start_time
            if len(self.activity_log) > 0:
                self.activity_log[-1]['time'] = self.format_duration(active_time.total_seconds())
            else:
                self.activity_log.append({'app': self.last_app, 'time': self.format_duration(active_time.total_seconds())})
        self.last_app = None
        self.start_time = None
        self._stop_listeners()
        self.monitoring = False

class AppMonitorUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Activity Monitor")
        self.master.geometry("250x250")  # Set the default size of the window
        self.app_monitor = AppMonitor()
        self.listeners_started = False

        self.info_label = tk.Label(master, textvariable=self.app_monitor.info)  # Display the info variable on the UI
        self.start_button = tk.Button(master, text="Start Monitoring", command=self.start_listeners)
        self.stop_button = tk.Button(master, text="Stop Monitoring", command=self.stop_listeners, state=tk.DISABLED)
        self.output_button = tk.Button(master, text="Output Log", command=self.app_monitor.output_log)

        self.start_button.pack(pady=10)
        self.stop_button.pack(pady=10)
        self.output_button.pack(pady=10)
        self.info_label.pack(pady=10)


    def start_listeners(self):
        if not self.listeners_started:
            self.app_monitor.start()
            self.listeners_started = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)

    def stop_listeners(self):
        if self.listeners_started:
            self.app_monitor.stop()
            self.listeners_started = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)

if __name__ == '__main__':
    root = tk.Tk()
    app_ui = AppMonitorUI(root)
    root.mainloop()
