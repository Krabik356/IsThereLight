#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

String WIFI_NAME = "Fenix";
String WIFI_PASSWORD = "0508026187";

String ID = "j8dsj8d198wjd981qwjnd";
String SECRET = "kdsajdj19jwd!7hd1h288hqH*!H*(";
String HTTP_PATH = "http://192.168.0.104:8000";

void wifi_begin(){
  Serial.println("WiFi connecting");
  WiFi.begin(WIFI_NAME, WIFI_PASSWORD);
  while(WiFi.status() != WL_CONNECTED){
    Serial.print(".");
    delay(1000);
  }
  Serial.println("WiFi connected");
  Serial.println(HTTP_PATH + "/remind/" + ID);
}

bool send_remind_http(){
  HTTPClient client;
  client.begin(HTTP_PATH+"/remind/"+ID);

  JsonDocument doc;
  doc["secret"] = SECRET;
  String toSend;
  serializeJson(doc, toSend);

  int code = client.POST(toSend);
  client.end();
  if (code != 200){
    return false;
  }
  return true;
}

void setup() {
  Serial.begin(115200);

  wifi_begin();
}

void loop() {
  bool is_ok = send_remind_http();
  if(!is_ok){
    Serial.println("error...");
  }
  delay(1000);
}



































