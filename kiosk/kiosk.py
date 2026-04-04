import sys
import webbrowser  # 👈 브라우저 여는 도구
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit,
    QGridLayout, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer
import requests

# ================= 키보드 =================
class NumberKeyboard(QWidget):
    def __init__(self, target: QLineEdit):
        super().__init__()
        self.target = target
        self.init_ui()

    def init_ui(self):
        grid = QGridLayout()
        grid.setSpacing(15)
        keys = ["1","2","3","4","5","6","7","8","9","0","←"]
        positions = [(i, j) for i in range(2) for j in range(6)]

        for pos, key in zip(positions, keys):
            btn = QPushButton(key)
            btn.setFixedSize(56, 48)

            if key == "←":
                btn.setStyleSheet("QPushButton { font-size: 20px; font-weight: bold; color: white; background-color: #EB5757; border-radius: 12px; border: none; } QPushButton:pressed { background-color: #C44545; }")
                btn.clicked.connect(lambda _, k=key: self.press(k))
            elif key == "":
                btn.setEnabled(False)
                btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
            else:
                btn.setStyleSheet("QPushButton { font-size: 18px; font-weight: bold; color: #212121; background-color: #E0E0E0; border-radius: 12px; border: 1px solid #BDBDBD; } QPushButton:pressed { background-color: #BDBDBD; }")
                btn.clicked.connect(lambda _, k=key: self.press(k))
            grid.addWidget(btn, *pos)
        self.setLayout(grid)

    def press(self, key):
        if not self.target: return
        if key == "←": self.target.backspace()
        else: self.target.insert(key)

class EnglishKeyboard(QWidget):
    def __init__(self, target: QLineEdit = None):
        super().__init__()
        self.target = target
        self.init_ui()

    def set_target(self, target):
        self.target = target

    def init_ui(self):
        grid = QGridLayout()
        grid.setSpacing(10)
        keys = ["Q","W","E","R","T","Y","U","I","O","P","A","S","D","F","G","H","J","K","L","","Z","X","C","V","B","N","M","","","←"]
        positions = [(i, j) for i in range(3) for j in range(10)]

        for pos, key in zip(positions, keys):
            btn = QPushButton(key)
            btn.setFixedSize(56, 48)

            if key == "←":
                btn.setStyleSheet("QPushButton { font-size: 20px; font-weight: bold; color: white; background-color: #EB5757; border-radius: 12px; border: none; } QPushButton:pressed { background-color: #C44545; }")
                btn.clicked.connect(lambda _, k=key: self.press(k))
            elif key == "":
                btn.setEnabled(False)
                btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
            else:
                btn.setStyleSheet("QPushButton { font-size: 18px; font-weight: bold; color: #212121; background-color: #E0E0E0; border-radius: 12px; border: 1px solid #BDBDBD; } QPushButton:pressed { background-color: #BDBDBD; }")
                btn.clicked.connect(lambda _, k=key: self.press(k))
            grid.addWidget(btn, *pos)
        self.setLayout(grid)

    def press(self, key):
        if not self.target: return
        if key == "←": self.target.backspace()
        else: self.target.insert(key)

# ================= 홈 =================
class HomePage(QWidget):
    def __init__(self, go_signup, go_login, go_guest):
        super().__init__()
        self.go_signup = go_signup
        self.go_login = go_login
        self.go_guest = go_guest
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        self.notice = QLabel("")
        self.notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.notice.setStyleSheet("font-size:20px; color:green;")

        logo = QLabel("SINGPICK")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size:40px; font-weight:bold; color:black")

        btn_signup = QPushButton("회원가입")
        btn_login = QPushButton("회원")
        btn_guest = QPushButton("비회원")

        btn_signup.setStyleSheet("QPushButton { font-size: 20px; font-weight: bold; color: white; background-color: #2F80ED; border-radius: 14px; border: none; } QPushButton:pressed { background-color: #1C5DB6; }")
        btn_login.setStyleSheet("QPushButton { font-size: 18px; font-weight: bold; color: white; background-color: #27AE60; border-radius: 14px; border: none; } QPushButton:pressed { background-color: #1E874B; }")
        btn_guest.setStyleSheet("QPushButton { font-size: 18px; font-weight: bold; color: white; background-color: #828282; border-radius: 14px; border: none; } QPushButton:pressed { background-color: #5F5F5F; }")

        btn_signup.setFixedSize(300, 55)
        btn_login.setFixedSize(140, 55)
        btn_guest.setFixedSize(140, 55)

        btn_signup.clicked.connect(self.go_signup)
        btn_login.clicked.connect(self.go_login)
        # 비회원은 아이디 Guest, 토큰 없음으로 바로 곡 선택으로!
        btn_guest.clicked.connect(lambda: self.go_guest(user_id="Guest", token=""))

        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(btn_login)
        h.addWidget(btn_guest)
        h.addStretch()

        layout.addWidget(self.notice)
        layout.addStretch()
        layout.addWidget(logo)
        layout.addWidget(btn_signup, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(h)
        layout.addStretch()
        self.setLayout(layout)

    def show_notice(self):
        self.notice.setText("결제가 완료되었습니다. 부스로 입장해주세요!")
        QTimer.singleShot(4000, lambda: self.notice.setText(""))

# ================= 회원가입 =================
class SignUpPage(QWidget):
    def __init__(self, go_home):
        super().__init__()
        self.go_home = go_home
        self.init_ui()
        self.reset()

    def reset(self):
        self.user_id_input.clear()
        self.phone_input.clear()
        self.password_input.clear()
        while self.kb_box.count():
            item = self.kb_box.takeAt(0)
            if item.widget(): item.widget().setParent(None)

    def init_ui(self):
        main = QVBoxLayout()
        title = QLabel("회원가입")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:28px; font-weight: bold; color: black;")

        self.user_id_input = QLineEdit()
        self.user_id_input.setPlaceholderText("    아이디")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("    전화번호 (숫자 11자리)")
        self.phone_input.setMaxLength(11)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("    비밀번호 (숫자 6자리)")
        self.password_input.setMaxLength(6)

        for i in (self.user_id_input, self.phone_input, self.password_input):
            i.setFixedHeight(25)
            i.setStyleSheet("QLineEdit { font-size: 15px; padding-left: 10px; background-color: #F2F2F2; border: 2px solid #BDBDBD; border-radius: 8px; color: #212121; } QLineEdit::placeholder { color: black;} QLineEdit:focus { background-color: #FFFFFF; border: 2px solid #2F80ED; }")

        self.num_kb = NumberKeyboard(None)
        self.eng_kb = EnglishKeyboard()
        self.kb_box = QVBoxLayout()

        self.user_id_input.mousePressEvent = lambda e: self.show_eng(self.user_id_input)
        self.phone_input.mousePressEvent = lambda e: self.show_num(self.phone_input)
        self.password_input.mousePressEvent = lambda e: self.show_num(self.password_input)

        btn_submit = QPushButton("등록")
        btn_home = QPushButton("홈")
        for btn in (btn_submit, btn_home):
            btn.setFixedSize(140, 45)
            btn.setStyleSheet("QPushButton { font-size: 18px; font-weight: bold; color: white; background-color: #213555; border-radius: 12px; border: none; } QPushButton:pressed { background-color: #068FFF; }")
        
        btn_submit.clicked.connect(self.submit)
        btn_home.clicked.connect(lambda: [self.reset(), self.go_home()])

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_submit)
        btn_row.addWidget(btn_home)

        main.addWidget(title)
        main.addWidget(self.user_id_input)
        main.addWidget(self.phone_input)
        main.addWidget(self.password_input)
        main.addLayout(self.kb_box)
        main.addLayout(btn_row)
        self.setLayout(main)

    def clear_kb(self):
        while self.kb_box.count():
            self.kb_box.takeAt(0).widget().setParent(None)

    def show_eng(self, target):
        self.clear_kb()
        self.eng_kb.set_target(target)
        self.kb_box.addWidget(self.eng_kb)

    def show_num(self, target):
        self.clear_kb()
        self.num_kb.target = target
        self.kb_box.addWidget(self.num_kb)

    def submit(self):
        user_id = self.user_id_input.text().strip()
        phone = self.phone_input.text().strip()
        password = self.password_input.text().strip()

        if not (user_id.isalpha() and 4 <= len(user_id) <= 20): return print("오류: 아이디 양식 틀림")
        if len(phone) != 11 or not phone.isdigit(): return print("오류: 전화번호 양식 틀림")
        if len(password) != 6 or not password.isdigit(): return print("오류: 비밀번호 양식 틀림")

        payload = {"user_id": user_id, "phone": phone, "password": password}
        try:
            res = requests.post("http://127.0.0.1:8000/users/signup", json=payload)
            if res.status_code == 200:
                print("✅ 회원가입 성공!")
                self.reset()
                self.go_home()
            else:
                print(f"❌ 가입 실패: {res.json()}")
        except Exception as e:
            print(f"📡 서버 연결 실패: {e}")

# ================= 회원 로그인 (비밀번호 모자이크 & 에러 메시지 추가) =================
class LoginPage(QWidget):
    def __init__(self, go_home, go_song):
        super().__init__()
        self.go_home = go_home
        self.go_song = go_song
        self.fail_count = 0
        self.init_ui()
        self.reset()

    def reset(self):
        self.phone.clear()
        self.password.clear()
        self.error_label.setText("") # 🚨 화면 켜질 때 에러 메시지 초기화
        self.fail_count = 0
        while self.kb_box.count():
            item = self.kb_box.takeAt(0)
            if item.widget(): item.widget().setParent(None)

    def init_ui(self):
        layout = QVBoxLayout()
        title = QLabel("회원 로그인")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:28px; color: black; font-weight: bold;")

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("    전화번호 (숫자 11자리)")
        self.phone.setMaxLength(11)
        
        self.password = QLineEdit()
        self.password.setPlaceholderText("    비밀번호 (숫자 6자리)")
        self.password.setMaxLength(6)
        # 🚨 3번 요청: 비밀번호 입력 시 모자이크 처리!
        self.password.setEchoMode(QLineEdit.EchoMode.Password)

        for w in (self.phone, self.password):
            w.setFixedHeight(40)
            w.setStyleSheet("QLineEdit { font-size: 15px; padding-left: 10px; background-color: #F2F2F2; border: 2px solid #BDBDBD; border-radius: 8px; color: #212121; } QLineEdit::placeholder { color: black; } QLineEdit:focus { background-color: #FFFFFF; border: 2px solid #2F80ED; }")
        
        # 🚨 2번 요청: 비밀번호 틀렸을 때 띄워줄 빨간색 경고 문구 자리 만들기
        self.error_label = QLabel("")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setStyleSheet("color: #EB5757; font-size: 15px; font-weight: bold;")

        self.num_kb = NumberKeyboard(None)
        self.kb_box = QVBoxLayout()

        self.phone.mousePressEvent = lambda e: self.show_num(self.phone)
        self.password.mousePressEvent = lambda e: self.show_num(self.password)

        btn_ok = QPushButton("확인")
        btn_home = QPushButton("홈")
        for btn in (btn_ok, btn_home):
            btn.setFixedSize(140, 45)
            btn.setStyleSheet("QPushButton { background-color: #213555; color: white; font-size: 18px; font-weight: bold; border-radius: 12px; } QPushButton:pressed { background-color: #068FFF; }")
        
        btn_ok.clicked.connect(self.check)
        btn_home.clicked.connect(lambda: [self.reset(), self.go_home()])

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_home)

        layout.addWidget(title)
        layout.addWidget(self.phone)
        layout.addWidget(self.password)
        layout.addWidget(self.error_label) # 🚨 입력창 아래에 경고 문구 배치
        layout.addLayout(self.kb_box)
        layout.addLayout(btn_row)
        self.setLayout(layout)

    def clear_kb(self):
        while self.kb_box.count():
            item = self.kb_box.takeAt(0)
            if item.widget(): item.widget().setParent(None)

    def show_num(self, target):
        self.clear_kb()
        self.num_kb.target = target
        self.kb_box.addWidget(self.num_kb)

    def check(self):
        phone = self.phone.text().strip()
        password = self.password.text().strip()
        
        if not phone or not password:
            self.error_label.setText("전화번호와 비밀번호를 모두 입력해주세요.")
            return

        payload = {"phone": phone, "password": password}

        try:
            url = "http://127.0.0.1:8000/users/login"
            response = requests.post(url, json=payload)

            if response.status_code == 200:
                print("✅ 로그인 성공!")
                self.error_label.setText("") 
                data = response.json()
                
                user_id = data.get("user_id", "Guest")
                token = data.get("access_token", "")
                
                self.fail_count = 0
                self.go_song(user_id=user_id, token=token)
                
            else:
                # 🚨 터미널(검은 창)에 서버가 보낸 진짜 응답을 찍어봅니다!
                print(f"🚨 서버 원본 에러 응답: {response.text}")
                
                try:
                    error_data = response.json()
                    # 백엔드의 'detail' 메시지를 쏙 뽑아옵니다.
                    error_msg = error_data.get("detail", f"알 수 없는 오류 ({response.status_code})")
                except:
                    # JSON 형태가 아니면 그냥 생짜 텍스트라도 화면에 던집니다.
                    error_msg = response.text 
                
                self.error_label.setText(str(error_msg))

        except Exception as e:
            self.error_label.setText("백엔드 서버에 연결할 수 없습니다.")
            print(f"📡 백엔드 연결 실패: {e}")

# ================= 곡 수 선택 =================
class SongSelectPage(QWidget):
    def __init__(self, go_home):
        super().__init__()
        self.go_home = go_home # 이거 호출하면 KioskApp의 finish가 실행됨
        self.count = 0
        self.init_ui()

    def reset(self):
        self.count = 0
        self.update_label()
        self.notice.hide()

    def init_ui(self):
        layout = QVBoxLayout()
        title = QLabel("곡 수 선택")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: black;")

        self.notice = QLabel("최대 3곡까지 선택 가능합니다.")
        self.notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.notice.setStyleSheet("font-size: 16px; color: #D32F2F; font-weight: bold;")
        self.notice.hide()

        self.notice_timer = QTimer()
        self.notice_timer.setSingleShot(True)
        self.notice_timer.timeout.connect(self.notice.hide)

        self.label = QLabel("0 곡")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-size:32px; color:#394867;")

        btn_plus = QPushButton("+")
        btn_minus = QPushButton("-")
        for btn in (btn_plus, btn_minus):
            btn.setFixedSize(90, 90)
            btn.setStyleSheet("QPushButton { font-size: 42px; font-weight: bold; color: white; background-color: #2F80ED; border-radius: 45px; } QPushButton:pressed { background-color: #1C5DB6; }")
        
        btn_plus.clicked.connect(self.plus)
        btn_minus.clicked.connect(self.minus)

        count_row = QHBoxLayout()
        count_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_row.addWidget(btn_minus)
        count_row.addWidget(self.label)
        count_row.addWidget(btn_plus)

        btn_select = QPushButton("선택 (입장)")
        btn_home = QPushButton("취소 (홈)")
        for btn in (btn_select, btn_home):
            btn.setFixedSize(140, 45)
            btn.setStyleSheet("QPushButton { background-color: #213555; color: white; font-size: 18px; font-weight: bold; border-radius: 12px; } QPushButton:pressed { background-color: #068FFF; }")

        btn_select.clicked.connect(self.select)
        btn_home.clicked.connect(lambda: self.go_home(count=0))

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_select)
        btn_row.addWidget(btn_home)

        layout.addWidget(title)
        layout.addWidget(self.notice)
        layout.addLayout(count_row)
        layout.addLayout(btn_row)
        self.setLayout(layout)

    def show_notice(self):
        self.notice.show()
        self.notice_timer.start(3000)

    def update_label(self):
        self.label.setText(f"{self.count} 곡")

    def plus(self):
        if self.count < 3:
            self.count += 1
            self.update_label()
            if self.count == 3: self.show_notice()

    def minus(self):
        if self.count > 0:
            self.count -= 1
            self.update_label()

    def select(self):
        if self.count > 0:
            self.go_home(count=self.count)
        else:
            print("1곡 이상 선택해주세요!")


# ================= 메인 앱 제어 =================
class KioskApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SingPick Kiosk")
        self.setFixedSize(800, 480)
        
        # 로그인한 사용자의 정보를 기억하는 금고!
        self.current_user_id = "Guest"
        self.current_token = ""

        self.stack = QStackedWidget()
        self.init_pages()

        layout = QVBoxLayout()
        layout.addWidget(self.stack)
        self.setLayout(layout)
        self.setStyleSheet("background-color:#DDE6ED;")

    def init_pages(self):
        # 각 페이지 생성하면서 화면 이동 함수 연결
        self.home = HomePage(self.show_signup, self.show_login, self.show_song)
        self.signup = SignUpPage(self.show_home)
        self.login = LoginPage(self.show_home, self.show_song)
        self.song = SongSelectPage(self.finish)

        for p in (self.home, self.signup, self.login, self.song):
            self.stack.addWidget(p)

    def show_home(self):
        self.stack.setCurrentWidget(self.home)

    def show_signup(self):
        self.signup.reset() 
        self.stack.setCurrentWidget(self.signup)

    def show_login(self):
        self.login.reset() 
        self.stack.setCurrentWidget(self.login)

    # 🚨 로그인/비회원 클릭 시, 아이디와 토큰을 받아서 보관하고 곡 선택으로 넘어갑니다.
    def show_song(self, user_id="Guest", token=""):
        self.current_user_id = user_id
        self.current_token = token
        
        self.song.reset()
        self.stack.setCurrentWidget(self.song)

    # 🚨 곡 선택 후 '선택(입장)'을 누르면 실행됩니다.
    def finish(self, count):
        if count > 0:
            print(f"{self.current_user_id}님, {count}곡 결제 완료. 부스 입장!")
        
            url = f"http://127.0.0.1:8000/kiosk_static/index.html?user_id={self.current_user_id}&token={self.current_token}&songs={count}"
            webbrowser.open(url)
            
            # 다음 사람을 위해 키오스크 내부 데이터 초기화
            self.current_user_id = "Guest"
            self.current_token = ""
            
            # 화면은 다시 홈으로! (성공 메시지 띄우기)
            self.stack.setCurrentWidget(self.home)
            self.home.show_notice()
        else:
            # 취소(홈) 버튼 누른 경우
            self.current_user_id = "Guest"
            self.current_token = ""
            self.stack.setCurrentWidget(self.home)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = KioskApp()
    win.show()
    sys.exit(app.exec())