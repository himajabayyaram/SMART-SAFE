#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <Servo.h>

LiquidCrystal_I2C lcd(0x27, 16, 2);

Servo myServo;

String command = "";

int greenLED = 7;
int redLED = 6;
int buzzer = 8;

void setup() {

  Serial.begin(9600);

  myServo.attach(9);

  pinMode(greenLED, OUTPUT);
  pinMode(redLED, OUTPUT);
  pinMode(buzzer, OUTPUT);
  digitalWrite(buzzer,LOW);
  myServo.write(0);

  lcd.init();
  lcd.backlight();

  // Startup Message
  lcd.setCursor(0,0);
  lcd.print("SMART SAFE");

  lcd.setCursor(0,1);
  lcd.print("System Ready");

  delay(2000);

  lcd.clear();
}

void loop() {

  if (Serial.available()) {

    command = Serial.readStringUntil('\n');

    command.trim();

    // Reset outputs
    digitalWrite(greenLED, LOW);
    digitalWrite(redLED, LOW);
    digitalWrite(buzzer, LOW);

    lcd.clear();

    // ---------------- SCAN ----------------
    Serial.println(command);
    if (command == "SCAN") {

      lcd.setCursor(0,0);
      lcd.print("Scanning Face");

      lcd.setCursor(0,1);
      lcd.print("Please Wait");
    }
    
    else if (command == "EXPRESSION") {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Face OK");

      lcd.setCursor(0, 1);
      lcd.print("Do Expression");
}


    // ---------------- OPEN ----------------

    else if (command == "OPEN") {

      lcd.setCursor(0,0);
      lcd.print("Access Granted");

      lcd.setCursor(0,1);
      lcd.print("Door Unlocked");

      digitalWrite(greenLED, HIGH);

      myServo.write(90);

      delay(3000);

      myServo.write(0);

      digitalWrite(greenLED, LOW);
    }

    else if (command=="CHALLENGE")
    {
      lcd.clear();
      digitalWrite(buzzer,LOW);
    }
    
    else if (command == "VERIFYING") {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Verifying...");
}
    // ---------------- DENIED ----------------

    else if (command == "DENIED") {

      lcd.setCursor(0,0);
      lcd.print("Access Denied");

      lcd.setCursor(0,1);
      lcd.print("Try Again");

      digitalWrite(redLED, HIGH);
      for (int i=0;i<3;i++)
      {
        digitalWrite(buzzer, HIGH);
        delay(300);
        digitalWrite(buzzer, LOW);
        delay(300);
      }
      digitalWrite(redLED, LOW);
  
    }
    
    else if (command == "READY") {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("SMART SAFE");
  lcd.setCursor(0, 1);
  lcd.print("System Ready");
}
    // ---------------- REGISTER ----------------

    else if (command == "REGISTER") {

      lcd.setCursor(0,0);
      lcd.print("Registering");

      lcd.setCursor(0,1);
      lcd.print("New Face");
    }

    // ---------------- SAVED ----------------

    else if (command == "SAVED") {

      lcd.setCursor(0,0);
      lcd.print("Face Saved");

      lcd.setCursor(0,1);
      lcd.print("Successfully");

      delay(2000);
    }
  }
}