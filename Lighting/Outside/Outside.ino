// =========================
// RGB 1번 LED 핀 설정
const int redPin1 = 3;
const int greenPin1 = 5;
const int bluePin1 = 6;

// =========================
// RGB 2번 LED 핀 설정
const int redPin2 = 9;
const int greenPin2 = 10;
const int bluePin2 = 11;

// =========================
// 부스 상태 enum
// =========================
enum BoothState {
  STATE_OFF,
  STATE_RESERVATION,
  STATE_AVAILABLE,
  STATE_UNAVAILABLE
};

BoothState currentState = STATE_OFF;

// =========================
// 초기 설정
// =========================
void setup() {
  Serial.begin(9600);
  Serial.setTimeout(1500);

void setup() {
  // 1번 LED 핀 출력 설정
  pinMode(redPin1, OUTPUT);
  pinMode(greenPin1, OUTPUT);
  pinMode(bluePin1, OUTPUT);

  // 2번 LED 핀 출력 설정
  pinMode(redPin2, OUTPUT);
  pinMode(greenPin2, OUTPUT);
  pinMode(bluePin2, OUTPUT);

  allLedOff();
  delay(1000);

  setBoothState(STATE_AVAILABLE);
  Serial.println("Arduino Ready");
}

// =========================
// 메인 루프
// =========================
void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    Serial.print("[Serial] received='");
    Serial.print(command);
    Serial.println("'");

    if (command.length() > 0) {
      updateStateByCommand(command);
    }
  }
}

// =========================
// 상태 변경
// =========================
void setBoothState(BoothState state) {
  if (currentState == state) {
    Serial.print("Already in state: ");
    Serial.println(getStateName(state));
    return;
  }

  currentState = state;
  Serial.print("Changing state -> ");
  Serial.println(getStateName(state));

  switch (currentState) {
    case STATE_RESERVATION:
      setLedColor(true, false, false);
      Serial.println("STATE_RESERVATION");
      Serial.println("RED LED ON");
      break;

    case STATE_AVAILABLE:
      setLedColor(false, true, false);
      Serial.println("STATE_AVAILABLE");
      Serial.println("GREEN LED ON");
      break;

    case STATE_UNAVAILABLE:
      setLedColor(false, false, true);
      Serial.println("STATE_UNAVAILABLE");
      Serial.println("BLUE LED ON");
      break;

    case STATE_OFF:
    default:
      setLedColor(false, false, false);
      Serial.println("STATE_OFF");
      Serial.println("ALL LED OFF");
      break;
  }
}

// =========================
// LED 전체 OFF
// =========================
void allLedOff() {
  digitalWrite(redPin1, HIGH);
  digitalWrite(greenPin1, HIGH);
  digitalWrite(bluePin1, HIGH);

  digitalWrite(redPin2, HIGH);
  digitalWrite(greenPin2, HIGH);
  digitalWrite(bluePin2, HIGH);
}

// =========================
// RGB LED 제어
// 공통 애노드 방식
// LOW = ON
// HIGH = OFF
// =========================
void setLedColor(bool redOn, bool greenOn, bool blueOn) {

  Serial.begin(9600);
  
  // 처음 구동 시 기본 상태를 '초록색(사용 가능)'으로 시작합니다!
  setBoothState(STATE_AVAILABLE);
}

void loop() {
  // FastAPI로부터 시리얼 명령어가 들어왔는지 확인
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); // 공백 및 개행문자 제거
    updateStateByCommand(command);
  }
}

void setBoothState(BoothState state) {
  currentState = state;

  switch (currentState) {
    case STATE_RESERVATION:
      setLedColor(true, false, false); // 빨간색 ON
      break;

    case STATE_AVAILABLE:
      setLedColor(false, true, false); // 초록색 ON
      break;

    case STATE_UNAVAILABLE:
      setLedColor(false, false, true); // 파란색 ON
      break;

    case STATE_OFF:
    default:
      setLedColor(false, false, false); // 모두 OFF
      break;
  }
}

// [핵심 수정 부분] Anode LED 특성 반영 (true일 때 LOW를 줘서 1번, 2번 LED 동시 점등)
void setLedColor(bool redOn, bool greenOn, bool blueOn) {
  // 1번 LED 제어
  digitalWrite(redPin1, redOn ? LOW : HIGH);
  digitalWrite(greenPin1, greenOn ? LOW : HIGH);
  digitalWrite(bluePin1, blueOn ? LOW : HIGH);

  // 2번 LED 제어 (똑같은 상태값을 2번 핀들에도 그대로 쏴줍니다!)
  digitalWrite(redPin2, redOn ? LOW : HIGH);
  digitalWrite(greenPin2, greenOn ? LOW : HIGH);
  digitalWrite(bluePin2, blueOn ? LOW : HIGH);
}

// =========================
// 상태 이름 반환
// =========================
const char* getStateName(BoothState state) {
  switch (state) {
    case STATE_RESERVATION:
      return "RESERVATION";
    case STATE_AVAILABLE:
      return "AVAILABLE";
    case STATE_UNAVAILABLE:
      return "UNAVAILABLE";
    case STATE_OFF:
    default:
      return "OFF";
  }
}

// =========================
// 시리얼 명령 처리
// =========================
void updateStateByCommand(const String &command) {
  String cmd = command;
  cmd.trim();
  cmd.toUpperCase();

  if (
    cmd == "RESERVATION" ||
    cmd == "RED" ||
    cmd == "SONG_SELECT"
  ) {
    setBoothState(STATE_RESERVATION);
    Serial.println("-> RED LED ON");
    return;
  }

  if (cmd == "RESET") {
    setBoothState(STATE_AVAILABLE);
    Serial.println("RESET -> GREEN LED ON");
    return;
  }

  if (
    cmd == "AVAILABLE" ||
    cmd == "GREEN" ||
    cmd == "HOME"
  ) {
    if (currentState == STATE_RESERVATION) {
      Serial.println("IGNORED: GREEN/HOME/AVAILABLE while RESERVATION active");
      return;
    }
    setBoothState(STATE_AVAILABLE);
    Serial.println("-> GREEN LED ON");
    return;
  }

  if (
    cmd == "UNAVAILABLE" ||
    cmd == "BLUE"
  ) {
    setBoothState(STATE_UNAVAILABLE);
    Serial.println("-> BLUE LED ON");
    return;
  }

  if (cmd == "OFF") {
    setBoothState(STATE_OFF);
    Serial.println("-> ALL LED OFF");
    return;
  }

  Serial.print("Unknown command: ");
  Serial.println(command);
}
