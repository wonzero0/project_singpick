// RGB 1번 LED 핀 설정 (예: 내부용)
const int redPin1 = 3;
const int greenPin1 = 5;
const int bluePin1 = 6;

// RGB 2번 LED 핀 설정 (예: 외부용)
const int redPin2 = 9;
const int greenPin2 = 10;
const int bluePin2 = 11;

enum BoothState {
  STATE_OFF,
  STATE_RESERVATION,
  STATE_AVAILABLE,
  STATE_UNAVAILABLE
};

BoothState currentState = STATE_OFF;

void setup() {
  // 1번 LED 핀 출력 설정
  pinMode(redPin1, OUTPUT);
  pinMode(greenPin1, OUTPUT);
  pinMode(bluePin1, OUTPUT);

  // 2번 LED 핀 출력 설정
  pinMode(redPin2, OUTPUT);
  pinMode(greenPin2, OUTPUT);
  pinMode(bluePin2, OUTPUT);

  // 초기화 시 모든 LED 끄기 (Anode 방식이므로 HIGH가 OFF)
  digitalWrite(redPin1, HIGH);
  digitalWrite(greenPin1, HIGH);
  digitalWrite(bluePin1, HIGH);

  digitalWrite(redPin2, HIGH);
  digitalWrite(greenPin2, HIGH);
  digitalWrite(bluePin2, HIGH);

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

void updateStateByCommand(const String &command) {
  if (command.equalsIgnoreCase("RESERVATION") || command.equalsIgnoreCase("RED") || command.equalsIgnoreCase("SONG_SELECT")) {
    setBoothState(STATE_RESERVATION);
    Serial.println("State: RESERVATION (All Red LEDs ON)");
  } else if (command.equalsIgnoreCase("AVAILABLE") || command.equalsIgnoreCase("GREEN") || command.equalsIgnoreCase("HOME") || command.equalsIgnoreCase("RESET")) {
    setBoothState(STATE_AVAILABLE);
    Serial.println("State: AVAILABLE (All Green LEDs ON)");
  } else if (command.equalsIgnoreCase("UNAVAILABLE") || command.equalsIgnoreCase("BLUE")) {
    setBoothState(STATE_UNAVAILABLE);
    Serial.println("State: UNAVAILABLE (All Blue LEDs ON)");
  } else if (command.equalsIgnoreCase("OFF")) {
    setBoothState(STATE_OFF);
    Serial.println("State: OFF (All LEDs OFF)");
  } else {
    Serial.print("Unknown command: ");
    Serial.println(command);
  }
}