#include <ESP32_Servo.h>
#include "esp_camera.h"
#include <WiFi.h>
#include <ArduinoWebsockets.h>
#define CAMERA_MODEL_AI_THINKER
#include "camera_pins.h"
#include <ArduinoJson.h>



const char* ssid = "Frontier2976";
const char* password = "0550337623";
const char* websocket_server_host = "192.168.68.125";
const uint16_t websocket_server_port = 8089;
const int center = 90;
int x_angle = center;
int y_angle = center;

using namespace websockets;
WebsocketsClient client;
Servo x_servo;
Servo y_servo;

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  x_servo.attach(32,500,2500);
  y_servo.attach(33,500,2500);
  pinMode(4, OUTPUT); //laser  
  pinMode(2, OUTPUT); //pump  

  
  x_servo.write(x_angle);   
  y_servo.write(y_angle);
  delay(10);  

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = -1;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 10000000;
  config.pixel_format = PIXFORMAT_JPEG;
  //init with high specs to pre-allocate larger buffers
  if(psramFound()){
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 4;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");

  while(!client.connect(websocket_server_host, websocket_server_port, "/")){
    delay(500);
    Serial.print(".");
  }

  client.onMessage([](WebsocketsMessage msg){        
    //MOVE ALL OF THIS TO A FUNCTION YO
    // Serial.println("Got Message: " + msg.data());
    // Deserialize the JSON document
    DynamicJsonDocument command(1024);
    deserializeJson(command, msg.data());                       
    const int laser = command["laser"];
    const int aim_x_degrees = command["aim_x_degrees"];
    const int aim_y_degrees = command["aim_y_degrees"];    

    if(laser == 1){digitalWrite(4, HIGH);}
    if(laser == 0){digitalWrite(4, LOW);}
    
    y_angle = y_angle + aim_y_degrees;
    if(y_angle > 180){y_angle = 180;}
    if(y_angle <0){y_angle = 0;}
    y_servo.write(y_angle);
    delay(15)
    
    x_angle = x_angle + aim_x_degrees;    
    if(x_angle > 180){x_angle = 180;}
    if(x_angle <0){x_angle = 0;}
    x_servo.write(x_angle);
    delay(15)
    
  });
  Serial.println("Websocket Connected!");
}

void loop() {
  camera_fb_t *fb = esp_camera_fb_get();
  if(!fb){
    Serial.println("Camera capture failed");
    esp_camera_fb_return(fb);
    return;
  }

  if(fb->format != PIXFORMAT_JPEG){
    Serial.println("Non-JPEG data not implemented");
    return;
  }

  client.sendBinary((const char*) fb->buf, fb->len);
  client.poll();
  esp_camera_fb_return(fb);
}
