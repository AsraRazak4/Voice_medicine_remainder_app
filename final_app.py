import sqlite3, json, threading, pyttsx3, os, re, webbrowser, random
import speech_recognition as sr
from datetime import datetime
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.animation import Animation
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.list import ThreeLineAvatarIconListItem, IconLeftWidget, IconRightWidget, IRightBodyTouch
from kivymd.uix.boxlayout import MDBoxLayout

# --- 1. SCREEN CLASSES ---
class HomeScreen(MDScreen): pass
class TodayScreen(MDScreen): pass
class HistoryScreen(MDScreen): pass
class EmergencyScreen(MDScreen): pass

# Helper for multiple buttons on list items
class RightButtons(IRightBodyTouch, MDBoxLayout):
    adaptive_width = True

# --- 2. CORE SERVICES ---
def speak(text):
    def run_speech():
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 145) 
            clean = re.sub(r'\[.*?\]', '', text).replace("\\n", ". ")
            engine.say(clean)
            engine.runAndWait()
            engine.stop()
        except: pass
    threading.Thread(target=run_speech, daemon=True).start()

def init_db():
    with sqlite3.connect("medicines.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS medicines 
            (id INTEGER PRIMARY KEY, name TEXT, time TEXT, status TEXT DEFAULT 'PENDING', 
             last_reset TEXT)''')

# --- 3. UI DESIGN (GLASSMORPHISM) ---
KV = '''
<HomeScreen>:
    on_enter: app.update_stats()
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.05, 0.05, 0.1, 1
        MDTopAppBar:
            title: "MED-ASSIST AI"
            md_bg_color: 0.1, 0.1, 0.2, 0.8
            elevation: 0
        MDBoxLayout:
            orientation: 'vertical'
            padding: dp(25)
            spacing: dp(25)
            MDCard:
                size_hint: (1, 0.2)
                radius: [25,]
                padding: dp(20)
                md_bg_color: 1, 1, 1, 0.08
                line_color: 1, 1, 1, 0.1
                MDBoxLayout:
                    orientation: "vertical"
                    MDLabel:
                        id: progress_label
                        text: "Syncing..."
                        halign: "center"
                        font_style: "H6"
                        bold: True
                        theme_text_color: "Custom"
                        text_color: 0.9, 0.9, 1, 1
                    MDLabel:
                        id: health_tip
                        text: "Tip: Stay hydrated!"
                        halign: "center"
                        font_style: "Subtitle1"
                        theme_text_color: "Hint"
            MDCard:
                size_hint: (1, 0.4)
                md_bg_color: 0.1, 0.4, 0.8, 0.15
                radius: [40,]
                ripple_behavior: True
                line_color: 0.1, 0.4, 0.8, 0.3
                on_release: app.listen_voice_command()
                MDBoxLayout:
                    orientation: "vertical"
                    spacing: dp(10)
                    MDIcon:
                        icon: "microphone"
                        font_size: "100sp"
                        pos_hint: {"center_x": .5}
                        theme_text_color: "Custom"
                        text_color: 0.2, 0.6, 1, 1
                    MDLabel:
                        text: "TAP TO SPEAK"
                        halign: "center"
                        font_style: "H5"
                        bold: True
            MDGridLayout:
                cols: 2
                spacing: dp(20)
                size_hint_y: 0.25
                MDRaisedButton:
                    text: "DAILY LIST"
                    font_size: "18sp"
                    size_hint: (1, 1)
                    md_bg_color: 0.1, 0.6, 0.3, 0.8
                    on_release: app.root.current = "today"
                MDRaisedButton:
                    text: "AI GUIDE"
                    font_size: "18sp"
                    size_hint: (1, 1)
                    md_bg_color: 0.6, 0.4, 0.1, 0.8
                    on_release: app.root.current = "history"
            MDFillRoundFlatButton:
                text: "🆘 EMERGENCY SOS"
                size_hint: (1, 0.15)
                md_bg_color: 0.8, 0.1, 0.1, 0.9
                font_size: "22sp"
                bold: True
                on_release: app.root.current = "emergency"

<TodayScreen>:
    on_pre_enter: app.refresh_today_list()
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.05, 0.05, 0.1, 1
        MDTopAppBar:
            title: "TODAY'S SCHEDULE"
            left_action_items: [["arrow-left", lambda x: app.go_home()]]
            md_bg_color: 0.1, 0.1, 0.2, 1
        MDScrollView:
            MDList:
                id: today_list
                padding: dp(15)
                spacing: dp(10)

<HistoryScreen>:
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.05, 0.05, 0.1, 1
        MDTopAppBar:
            title: "AI MEDICAL GUIDE"
            left_action_items: [["arrow-left", lambda x: app.go_home()]]
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(20)
            MDCard:
                size_hint_y: None
                height: dp(350)
                padding: dp(25)
                radius: [25,]
                md_bg_color: 1, 1, 1, 0.05
                MDLabel:
                    id: chat_output
                    text: "Ask me: 'What is Paracetamol?'"
                    halign: "center"
                    font_style: "H6"
                    theme_text_color: "Custom"
                    text_color: 1, 1, 1, 0.9
                    markup: True
            Widget:

<EmergencyScreen>:
    on_enter: app.start_sos_animation()
    on_leave: app.stop_sos_animation()
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(40)
        spacing: dp(30)
        md_bg_color: 0.6, 0, 0, 1
        MDIcon:
            icon: "alert-octagon"
            font_size: "120sp"
            pos_hint: {"center_x": .5}
        MDLabel:
            text: "HELP IS NEEDED"
            halign: "center"
            font_style: "H3"
            bold: True
        MDFillRoundFlatIconButton:
            icon: "phone"
            text: "CALL AMBULANCE"
            size_hint: (1, None)
            height: dp(90)
            font_size: "20sp"
            md_bg_color: 1, 1, 1, 0.2
            on_release: app.make_call("911")
        MDFillRoundFlatIconButton:
            icon: "account-group"
            text: "CALL FAMILY"
            size_hint: (1, None)
            height: dp(90)
            font_size: "20sp"
            md_bg_color: 1, 1, 1, 0.2
            on_release: app.make_call("123456789")
        MDRaisedButton:
            text: "CANCEL"
            pos_hint: {"center_x": .5}
            md_bg_color: 0, 0, 0, 0.5
            on_release: app.go_home()
'''

class MedicineApp(MDApp):
    def build(self):
        self.theme_cls.theme_style = "Dark"
        init_db()
        self.daily_reset()
        Builder.load_string(KV)
        self.sm = MDScreenManager()
        self.sm.add_widget(HomeScreen(name='home'))
        self.sm.add_widget(TodayScreen(name='today'))
        self.sm.add_widget(HistoryScreen(name='history'))
        self.sm.add_widget(EmergencyScreen(name='emergency'))
        Clock.schedule_interval(self.background_state_check, 2)
        return self.sm

    def go_home(self): self.root.current = "home"

    def make_call(self, num):
        webbrowser.open(f"tel:{num}")
        speak(f"Preparing call to {num}")

    # --- ⏰ PERSISTENT ALERTS ---
    def background_state_check(self, dt):
        now = datetime.now()
        try:
            with sqlite3.connect("medicines.db") as conn:
                cursor = conn.execute("SELECT id, name, time FROM medicines WHERE status='PENDING'")
                for mid, name, t_str in cursor.fetchall():
                    med_dt = datetime.strptime(t_str, "%I:%M %p").replace(year=now.year, month=now.month, day=now.day)
                    sec_late = (now - med_dt).total_seconds()
                    
                    if sec_late > 900: # 15 Mins
                        conn.execute("UPDATE medicines SET status='MISSED' WHERE id=?", (mid,))
                        speak(f"Medicine alert. {name} has been marked as missed.")
                        self.update_stats()
                        continue
                    
                    if sec_late >= 0:
                        mins_late = int(sec_late // 60)
                        if mins_late % 3 == 0: # Every 3 mins
                            if int(sec_late % 60) in [10, 20, 30]: # 3 bursts
                                speak(f"Time to take your {name}")
        except: pass

    def update_stats(self):
        if not self.root or not self.root.has_screen('home'): return
        tips = ["Tip: Walk for 5 mins.", "Tip: Drink a glass of water.", "Tip: Keep a healthy smile!"]
        try:
            home = self.root.get_screen('home')
            home.ids.health_tip.text = random.choice(tips)
            with sqlite3.connect("medicines.db") as conn:
                total = conn.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
                taken = conn.execute("SELECT COUNT(*) FROM medicines WHERE status='TAKEN'").fetchone()[0]
                home.ids.progress_label.text = f"{taken} of {total} Medicines Taken"
        except: pass

    def refresh_today_list(self):
        if not self.root: return
        container = self.root.get_screen('today').ids.today_list
        container.clear_widgets()
        with sqlite3.connect("medicines.db") as conn:
            for mid, name, time, status in conn.execute("SELECT id, name, time, status FROM medicines"):
                color = [1, 0.7, 0, 1] if status == "PENDING" else ([0, 1, 0.5, 1] if status == "TAKEN" else [1, 0.2, 0.2, 1])
                
                item = ThreeLineAvatarIconListItem(
                    text=f"[size=20sp][b]{name}[/b][/size]", 
                    secondary_text=f"Time: {time}",
                    tertiary_text=f"Status: {status}"
                )
                
                # Status Icon (Left)
                icon = IconLeftWidget(icon="check-circle" if status == "TAKEN" else "clock-alert")
                icon.theme_text_color = "Custom"; icon.text_color = color
                item.add_widget(icon)
                
                # Buttons (Right)
                r_btns = RightButtons()
                
                # Checkmark (Mark Taken)
                if status == "PENDING":
                    done_btn = IconRightWidget(icon="check-bold", theme_text_color="Custom", text_color=[0, 1, 0.5, 1])
                    done_btn.on_release = lambda x=mid: self.mark_as_taken(x)
                    r_btns.add_widget(done_btn)
                
                # Trash Can (Delete/Stop Med)
                del_btn = IconRightWidget(icon="delete-forever", theme_text_color="Custom", text_color=[1, 0.3, 0.3, 1])
                del_btn.on_release = lambda x=mid, n=name: self.delete_med(x, n)
                r_btns.add_widget(del_btn)
                
                item.add_widget(r_btns)
                container.add_widget(item)

    def mark_as_taken(self, mid):
        with sqlite3.connect("medicines.db") as conn:
            conn.execute("UPDATE medicines SET status = 'TAKEN' WHERE id = ?", (mid,))
        self.refresh_today_list()
        self.update_stats()
        speak("Excellent. I have marked that as taken.")

    def delete_med(self, mid, name):
        with sqlite3.connect("medicines.db") as conn:
            conn.execute("DELETE FROM medicines WHERE id = ?", (mid,))
        self.refresh_today_list()
        self.update_stats()
        speak(f"Medicine {name} has been removed from your list.")

    def listen_voice_command(self):
        def thread_listen():
            r = sr.Recognizer()
            with sr.Microphone() as source:
                speak("Listening")
                try:
                    audio = r.listen(source, timeout=4)
                    cmd = r.recognize_google(audio).lower()
                    Clock.schedule_once(lambda dt: self.process_command(cmd))
                except: speak("I didn't catch that.")
        threading.Thread(target=thread_listen, daemon=True).start()

    def process_command(self, cmd):
        add_match = re.search(r"add\s+(.+?)\s+at\s+(.+)", cmd)
        if add_match:
            med = add_match.group(1).strip().title()
            raw_t = add_match.group(2).strip().lower()
            period = "PM" if "p" in raw_t else "AM"
            digs = re.findall(r'\d+', raw_t)
            try:
                f_t = f"{int(digs[0]):02d}:{int(digs[1]):02d} {period}" if len(digs) >= 2 else f"{int(digs[0]):02d}:00 {period}"
                with sqlite3.connect("medicines.db") as conn:
                    conn.execute("INSERT INTO medicines (name, time, status, last_reset) VALUES (?, ?, 'PENDING', ?)", (med, f_t, datetime.now().strftime("%Y-%m-%d")))
                speak(f"Okay, I've added {med} for {f_t}")
                self.update_stats()
            except: speak("Sorry, I couldn't understand the time.")
        elif any(w in cmd for w in ["what", "tell", "info"]):
            self.root.current = "history"
            self.run_ai_chat(cmd)

    def run_ai_chat(self, query):
        try:
            with open("medicines.json", "r") as f: kb = json.load(f)
            q = query.lower()
            found = False
            for cat in kb:
                for med in kb[cat]:
                    if med['generic_name'].lower() in q or any(b.lower() in q for b in med.get('brand_names', [])):
                        res = f"[b]{med['generic_name'].upper()}[/b]\\n\\n{med['notes']}"
                        self.root.get_screen('history').ids.chat_output.text = res
                        speak(med['notes'])
                        found = True; break
            if not found: speak("I don't have information on that medication.")
        except: pass

    def daily_reset(self):
        today = datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect("medicines.db") as conn:
            conn.execute("UPDATE medicines SET status = 'PENDING' WHERE last_reset != ?", (today,))
            conn.execute("UPDATE medicines SET last_reset = ?", (today,))

    def start_sos_animation(self):
        s = self.root.get_screen('emergency')
        self.a = Animation(md_bg_color=(0.8, 0.1, 0.1, 1), duration=0.6) + Animation(md_bg_color=(0.4, 0, 0, 1), duration=0.6)
        self.a.repeat = True; self.a.start(s)

    def stop_sos_animation(self):
        if hasattr(self, 'a'): self.a.stop(self.root.get_screen('emergency'))

if __name__ == "__main__":
    MedicineApp().run()