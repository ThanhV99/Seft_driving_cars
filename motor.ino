//dc A cham hon B 30 xung PWM
int enA = 5;
int in1 = 8;
int in2 = 7;

int enB = 11;
int in3 = 10;
int in4 = 9;

char c;
int count=0;
void setup() { 
  Serial.begin(9600);               
  pinMode(enA,OUTPUT);
  pinMode(in1,OUTPUT);
  pinMode(in2,OUTPUT);
  pinMode(enB,OUTPUT);
  pinMode(in3,OUTPUT);
  pinMode(in4,OUTPUT);  
  digitalWrite(in1,HIGH);
  digitalWrite(in2,LOW);
  digitalWrite(in4,HIGH);
  digitalWrite(in3,LOW);
}
 
void loop() {
  if(Serial.available()>0){
    c = Serial.read();
    count++;
    if(c=='0'){     
      analogWrite(enA,130);
      analogWrite(enB,70);
    }
    if(c=='2'){          
      analogWrite(enB,120);
      analogWrite(enA,90);
    }
    if(c=='1'){
      analogWrite(enA,110);
      analogWrite(enB,80);
    }
    if(c=='q'){
      analogWrite(enA,0);
      analogWrite(enB,0);
    }
    if(count==50){
      count = 0;
      analogWrite(enA,0);
      analogWrite(enB,0);
      delay(1);
    }
  }  
}
