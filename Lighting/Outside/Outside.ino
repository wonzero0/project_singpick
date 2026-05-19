// RGB pin settings
const int redPin = 9;
const int greenPin = 10;
const int bluePin = 11;

enum BoothState {
  STATE_OFF,
  STATE_RESERVATION,
  STATE_AVAILABLE,
  STATE_UNAVAILABLE
};

BoothState currentState = STATE_OFF;

void setup() {
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);

  // 초기화 시 모든 LED 끄기 (Anode 방식이므로 HIGH가 OFF)
  digitalWrite(redPin, HIGH);
  digitalWrite(greenPin, HIGH);
  digitalWrite(bluePin, HIGH);

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

// Anode LED 특성 반영 (true일 때 LOW를 줘서 점등)
void setLedColor(bool redOn, bool greenOn, bool blueOn) {
  digitalWrite(redPin, redOn ? LOW : HIGH);
  digitalWrite(greenPin, greenOn ? LOW : HIGH);
  digitalWrite(bluePin, blueOn ? LOW : HIGH);
}

void updateStateByCommand(const String &command) {
  if (command.equalsIgnoreCase("RESERVATION") || command.equalsIgnoreCase("RED") || command.equalsIgnoreCase("SONG_SELECT")) {
    setBoothState(STATE_RESERVATION);
    Serial.println("State: RESERVATION (Red LED ON)");
  } else if (command.equalsIgnoreCase("AVAILABLE") || command.equalsIgnoreCase("GREEN") || command.equalsIgnoreCase("HOME") || command.equalsIgnoreCase("RESET")) {
    setBoothState(STATE_AVAILABLE);
    Serial.println("State: AVAILABLE (Green LED ON)");
  } else if (command.equalsIgnoreCase("UNAVAILABLE") || command.equalsIgnoreCase("BLUE")) {
    setBoothState(STATE_UNAVAILABLE);
    Serial.println("State: UNAVAILABLE (Blue LED ON)");
  } else if (command.equalsIgnoreCase("OFF")) {
    setBoothState(STATE_OFF);
    Serial.println("State: OFF (All LEDs OFF)");
  } else {
    Serial.print("Unknown command: ");
    Serial.println(command);
  }
}