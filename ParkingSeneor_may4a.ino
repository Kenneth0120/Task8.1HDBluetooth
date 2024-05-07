#include <ArduinoBLE.h>

#define trigPin 6 
#define echoPin 5 
#define force A1

int data = 0;
float new_delay;
bool shouldAdvertise = true; // Control variable to handle advertising

BLEService parkingService("12345678-1234-5678-1234-56789abcdef0"); // create a BLE service
BLEStringCharacteristic distanceCharacteristic("abcdef12-3456-7890-1234-567890abcdef", BLENotify, 20);  // Max 20 bytes

void setup() {
  Serial.begin (9600); 
  while (!Serial);
  pinMode(force, INPUT);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT); 

  // Initialize BLE
  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");
    while (1);
  }

  Serial.println("Bluetooth initialized successfully");
  
  BLE.setLocalName("ParkingSensor");
  BLE.setAdvertisedServiceUuid(parkingService.uuid());
  parkingService.addCharacteristic(distanceCharacteristic);
  BLE.addService(parkingService);
  BLE.advertise();

  Serial.println("Bluetooth device active, waiting for connections...");
}

void loop() {
  int forceRead = analogRead(force);
  long distance = measureDistance();
  
  // Convert distance and forceRead into a comma-separated string
  String dataToSend = String(distance) + "," + String(forceRead);
  distanceCharacteristic.writeValue(dataToSend.c_str());

  Serial.print("Sending data: ");
  Serial.println(dataToSend);
  
  // Handle re-advertising
  if (!BLE.connected() && shouldAdvertise) {
    BLE.advertise();
    Serial.println("Restarted advertising");
  }

  delay(2500); // Delay for stability
}

long measureDistance() {
  digitalWrite(trigPin, LOW); 
  delayMicroseconds(2); 
  digitalWrite(trigPin, HIGH); 
  delayMicroseconds(10); 
  digitalWrite(trigPin, LOW); 
  long duration = pulseIn(echoPin, HIGH);
  delay(10);
  return duration * 0.034 * 2;
}