// Arkrishitech sensor node - USB serial JSON stream for the browser dashboard.
#include <OneWire.h>
#include <DallasTemperature.h>
// Wire only after checking your exact sensor-board pinout. UNO Q MCU pins are 3.3V logic; NEVER feed 5V into analog pins.

const int PIN_MOIST = A2;      // capacitive soil moisture analog output
const int PIN_PH    = A3;      // pH interface analog output; requires 2-point calibration
const int PIN_DS18  = 2;       // DS18B20 data, 4.7k pull-up to 3.3V
int RAW_DRY = 900, RAW_WET = 400; // calibrate in your own soil/air and saturated medium
float PH_SLOPE = -5.7, PH_OFFSET = 21.0; // placeholders: calibrate with pH 4 and 7 buffers
OneWire ow(PIN_DS18); DallasTemperature ds(&ow);
float avgRead(int pin) { long sum=0; for(int i=0;i<16;i++){sum+=analogRead(pin);delay(4);} return sum/16.0; }
void setup(){ Serial.begin(115200); ds.begin(); while(!Serial && millis()<3000){} }
void loop(){
  float raw=avgRead(PIN_MOIST);
  float moisture=constrain((RAW_DRY-raw)/(float)(RAW_DRY-RAW_WET)*100.0,0,100);
  ds.requestTemperatures(); float soilT=ds.getTempCByIndex(0);
  bool tempValid = soilT >= -20 && soilT <= 60;
  float volts=avgRead(PIN_PH)*3.3/1023.0; float ph=constrain(PH_SLOPE*volts+PH_OFFSET,0,14);
  Serial.print("{\"moisture\":");Serial.print(moisture,1);
  Serial.print(",\"soil_t\":"); if(tempValid) Serial.print(soilT,1); else Serial.print("null");
  Serial.print(",\"ph\":");Serial.print(ph,2);Serial.println("}");
  delay(2000);
}
