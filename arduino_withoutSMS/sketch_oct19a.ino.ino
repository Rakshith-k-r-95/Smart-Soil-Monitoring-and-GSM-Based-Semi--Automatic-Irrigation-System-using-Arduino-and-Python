#include <SoftwareSerial.h>
#include <DHT.h>

#define DHTPIN 2
#define DHTTYPE DHT11   // change to DHT22 if using DHT22
#define RELAY_PIN 7
#define SOIL_PIN A0
#define GSM_TX 9
#define GSM_RX 10

SoftwareSerial gsm(GSM_RX, GSM_TX);
DHT dht(DHTPIN, DHTTYPE);

bool pumpState = false; // false = OFF, true = ON
unsigned long lastSend = 0;
const unsigned long sendInterval = 5000; // 5 seconds

void setup() {
  Serial.begin(9600);        // Serial to PC
  gsm.begin(9600);          // SoftwareSerial to GSM
  dht.begin();
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); // relay off (active LOW)
  Serial.println("System start");

  // Check GSM without blocking
  gsm.println("AT");
  delay(200);
  if (gsm.available()) {
    String r = gsm.readString();
    if (r.indexOf("OK") != -1) Serial.println("GSM Module Connected ✅");
    else Serial.println("GSM Module Not Responding ❌");
  } else {
    Serial.println("GSM Module Not Connected ❌");
  }
}

void loop() {
  // Read sensors
  int soilValue = analogRead(SOIL_PIN);     // raw analog (0-1023)
  float humidity = dht.readHumidity();
  float temperature = dht.readTemperature();

  // Protect against failed DHT reads
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("DHT read failed");
    humidity = -1;
    temperature = -100;
  }

  // Non-blocking: check GSM input (SMS)
  if (gsm.available()) {
    String msg = gsm.readString();
    msg.toUpperCase();
    Serial.print("GSM RX: ");
    Serial.println(msg);
    if (msg.indexOf("ON") != -1) {
      pumpState = true;
      Serial.println("Pump -> ON (via SMS)");
    } else if (msg.indexOf("OFF") != -1) {
      pumpState = false;
      Serial.println("Pump -> OFF (via SMS)");
    }
  }

  // Apply pump state to relay (active LOW)
  if (pumpState) digitalWrite(RELAY_PIN, LOW);
  else digitalWrite(RELAY_PIN, HIGH);

  // Send CSV line to USB Serial every 5s
  unsigned long now = millis();
  if (now - lastSend >= sendInterval) {
    lastSend = now;
    // format: soil,temperature,humidity
    Serial.print(soilValue);
    Serial.print(",");
    Serial.print(temperature);
    Serial.print(",");
    Serial.println(humidity);
  }

  // short delay for stable loop
  delay(200);
}
