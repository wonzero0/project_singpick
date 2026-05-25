#include <Arduino.h>

int white1 = 2;
int white2 = 3;
int white3 = 4;

int redLED = 8;
int greenLED = 9;
int blueLED = 10;
int yellowLED = 11;

bool musicPlaying = false;

void setup() {

  Serial.begin(9600);

  pinMode(white1, OUTPUT);
  pinMode(white2, OUTPUT);
  pinMode(white3, OUTPUT);

  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(blueLED, OUTPUT);
  pinMode(yellowLED, OUTPUT);

  // 🤍 기본 흰색
  whiteMode();
}

void loop() {

  // 🔥 시리얼 신호 수신
  if (Serial.available()) {

    String command = Serial.readStringUntil('\n');
    command.trim();

    // 🎵 노래 시작
    if (command == "PLAY") {

      musicPlaying = true;

      Serial.println("PLAY RECEIVED");
    }

    // ⏹ 노래 종료
    else if (command == "STOP") {

      musicPlaying = false;

      whiteMode();

      Serial.println("STOP RECEIVED");
    }
  }

  // 🎉 미러볼 모드
  if (musicPlaying) {

    partyMode();
  }
}

// =========================
// 🤍 흰 조명
// =========================
void whiteMode() {

  digitalWrite(white1, HIGH);
  digitalWrite(white2, HIGH);
  digitalWrite(white3, HIGH);

  digitalWrite(redLED, LOW);
  digitalWrite(greenLED, LOW);
  digitalWrite(blueLED, LOW);
  digitalWrite(yellowLED, LOW);
}

// =========================
// 🎉 미러볼
// =========================
void partyMode() {

  // 흰색 OFF
  digitalWrite(white1, LOW);
  digitalWrite(white2, LOW);
  digitalWrite(white3, LOW);

  // 컬러 랜덤
  digitalWrite(redLED, random(0, 2));
  digitalWrite(greenLED, random(0, 2));
  digitalWrite(blueLED, random(0, 2));
  digitalWrite(yellowLED, random(0, 2));

  delay(350);
}