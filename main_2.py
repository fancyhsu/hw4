#include "mbed.h"
#include "mbed_rpc.h"
#include "math.h"
#include "fsl_port.h"
#include "fsl_gpio.h"
#include "MQTTNetwork.h"
#include "MQTTmbed.h"
#include "MQTTClient.h"
WiFiInterface *wifi;
InterruptIn btn3(SW3);
volatile int message_num = 0;
volatile int arrivedcount = 0;
volatile bool closed = false;
const char* topic = "Mbed";
// RawSerial pc(USBTX, USBRX);
Serial pc(USBTX, USBRX);
RawSerial xbee(D12, D11);
EventQueue queue(32 * EVENTS_EVENT_SIZE);
EventQueue queue2(32 * EVENTS_EVENT_SIZE);
InterruptIn sw2(SW2);
Thread t;
Thread t2(osPriorityNormal,120*1024/*120K stack size*/);;


#define UINT14_MAX        16383
#define FXOS8700CQ_SLAVE_ADDR0 (0x1E<<1)
#define FXOS8700CQ_SLAVE_ADDR1 (0x1D<<1)
#define FXOS8700CQ_SLAVE_ADDR2 (0x1C<<1)
#define FXOS8700CQ_SLAVE_ADDR3 (0x1F<<1)
#define FXOS8700Q_STATUS 0x00
#define FXOS8700Q_OUT_X_MSB 0x01
#define FXOS8700Q_OUT_Y_MSB 0x03
#define FXOS8700Q_OUT_Z_MSB 0x05
#define FXOS8700Q_M_OUT_X_MSB 0x33
#define FXOS8700Q_M_OUT_Y_MSB 0x35
#define FXOS8700Q_M_OUT_Z_MSB 0x37
#define FXOS8700Q_WHOAMI 0x0D
#define FXOS8700Q_XYZ_DATA_CFG 0x0E
#define FXOS8700Q_CTRL_REG1 0x2A
#define FXOS8700Q_M_CTRL_REG1 0x5B
#define FXOS8700Q_M_CTRL_REG2 0x5C
#define FXOS8700Q_WHOAMI_VAL 0xC7
I2C i2c( PTD9,PTD8);
int m_addr = FXOS8700CQ_SLAVE_ADDR1;
void FXOS8700CQ_readRegs(int addr, uint8_t * data, int len);
void FXOS8700CQ_writeRegs(uint8_t * data, int len);

void xbee_rx_interrupt(void);
void xbee_rx(void);
void reply_messange(char *xbee_reply, char *messange);
void rpc_call(Arguments *in, Reply *out);
void rpc_call_alldata(Arguments *in, Reply *out);

void acce_value();
void messageArrived(MQTT::MessageData& md);
void close_mqtt();
void publish_message(MQTT::Client<MQTTNetwork, Countdown>* client);
RPCFunction rpc_acce(&rpc_call, "rpc_call");
RPCFunction rpc_acce_alldata(&rpc_call_alldata, "rpc_call_alldata");

Timer timer1;
float tt[3], origin[3];
int first_pos = 0, flag3 = 1, all_cnt = 0, cnt = 1, flag2 = 0, all_i = 0;
float all_x[50], all_y[50], all_z[50];

int main(){
  pc.baud(9600);
  char xbee_reply[4];
  printf("AAA");
  xbee.baud(9600);
  xbee.printf("+++");
  xbee_reply[0] = xbee.getc();
  xbee_reply[1] = xbee.getc();
  if(xbee_reply[0] == 'O' && xbee_reply[1] == 'K'){
    pc.printf("enter AT mode.\r\n");
    xbee_reply[0] = '\0';
    xbee_reply[1] = '\0';
  }
  xbee.printf("ATMY 0x240\r\n");
  reply_messange(xbee_reply, "setting MY : <REMOTE_MY>");
  xbee.printf("ATDL 0x241\r\n");
  reply_messange(xbee_reply, "setting DL : <REMOTE_DL>");
  xbee.printf("ATID 0x0\r\n");
  reply_messange(xbee_reply, "setting PAN ID : <PAN_ID>");
  xbee.printf("ATWR\r\n");
  reply_messange(xbee_reply, "write config");
  xbee.printf("ATCN\r\n");
  reply_messange(xbee_reply, "exit AT mode");
  xbee.getc();
  pc.printf("start\r\n");
  
  t.start(callback(&queue, &EventQueue::dispatch_forever));
  t2.start(callback(&queue2, &EventQueue::dispatch_forever));
  
  sw2.rise(queue2.event(acce_value));
  xbee.attach(xbee_rx_interrupt, Serial::RxIrq);
}
void xbee_rx_interrupt(void){
  xbee.attach(NULL, Serial::RxIrq); // detach interrupt
  queue.call(&xbee_rx);
}
void xbee_rx(void){
  char buf[100] = {0};
  char outbuf[100] = {0};
  while(xbee.readable()){
    memset(buf, 0, 100);
    for (int i=0; ; i++) {
      char recv = xbee.getc();
      if (recv == '\r') {
        break;
      }
      buf[i] = pc.putc(recv);
    }
    
    RPC::call(buf, outbuf);
    // wait(0.1);
  }
  xbee.attach(xbee_rx_interrupt, Serial::RxIrq); // reattach interrupt
}
void reply_messange(char *xbee_reply, char *messange){
  xbee_reply[0] = xbee.getc();
  xbee_reply[1] = xbee.getc();
  xbee_reply[2] = xbee.getc();
  if(xbee_reply[1] == 'O' && xbee_reply[2] == 'K'){
    pc.printf("%s\r\n", messange);
    xbee_reply[0] = '\0';
    xbee_reply[1] = '\0';
    xbee_reply[2] = '\0';
  }
}

void acce_value(){
  int tilt = 0, tilt_pre = 0, flag = 0;
  float thres = sqrt(2)/2;
  int oneseccnt = 0;
  while(flag3){
      uint8_t who_am_i, data[2], res[6];
      int16_t acc16;
      FXOS8700CQ_readRegs( FXOS8700Q_CTRL_REG1, &data[1], 1);
      data[1] |= 0x01;
      data[0] = FXOS8700Q_CTRL_REG1;
      FXOS8700CQ_writeRegs(data, 2);
      FXOS8700CQ_readRegs(FXOS8700Q_WHOAMI, &who_am_i, 1);
      FXOS8700CQ_readRegs(FXOS8700Q_OUT_X_MSB, res, 6);
      acc16 = (res[0] << 6) | (res[1] >> 2);
      if (acc16 > UINT14_MAX/2)
          acc16 -= UINT14_MAX;
      tt[0] = ((float)acc16) / 4096.0f;
      acc16 = (res[2] << 6) | (res[3] >> 2);
      if (acc16 > UINT14_MAX/2)
          acc16 -= UINT14_MAX;
      tt[1] = ((float)acc16) / 4096.0f;
      acc16 = (res[4] << 6) | (res[5] >> 2);
      if (acc16 > UINT14_MAX/2)
          acc16 -= UINT14_MAX;
      tt[2] = ((float)acc16) / 4096.0f;

      if(first_pos == 0){
          origin[0] = tt[0];
          origin[1] = tt[1];
          origin[2] = tt[2];
          first_pos = 1;
      }
      float ori_len = sqrt(pow(abs(origin[0]),2)+pow(abs(origin[1]),2)+pow(abs(origin[2]),2));
      float angle = origin[0]*tt[0] + origin[1]*tt[1] + origin[2]*tt[2];
      float angle2 = angle/(ori_len*(sqrt(pow(abs(tt[0]),2)+pow(abs(tt[1]),2)+pow(abs(tt[2]),2))));
      if(angle2 < thres)   tilt = 0;
      else  tilt = 1;
      if(tilt == 1 && tilt_pre == 0) flag = 1;
      if(flag == 1){
        wait(0.1);
        oneseccnt++;
        if(oneseccnt >= 10){
          oneseccnt = 0;
          flag = 0;
        }
      }  
      else{
        wait(0.5);
      }
      if(flag2 == 1){
        xbee.printf("%d\n", cnt-1);
        flag2 = 0;
        cnt = 0;
      }
      tilt_pre = tilt;
      cnt = cnt + 1;
      if(all_cnt<100){
        all_x[all_cnt] = tt[0];
        all_y[all_cnt] = tt[1];
        all_z[all_cnt] = tt[2];
        all_cnt ++;
      }
  }
}

void rpc_call(Arguments *in, Reply *out){
  flag2 = 1;
}

void rpc_call_alldata(Arguments *in, Reply *out){
  flag3 = 0;
  xbee.printf("%.4f %.4f %.4f\n",all_x[all_i],all_y[all_i],all_z[all_i]);
  all_i++;
}

void FXOS8700CQ_readRegs(int addr, uint8_t * data, int len) {
   char t = addr;
   i2c.write(m_addr, &t, 1, true);
   i2c.read(m_addr, (char *)data, len);
}
void FXOS8700CQ_writeRegs(uint8_t * data, int len) {
   i2c.write(m_addr, (char *)data, len);
}
