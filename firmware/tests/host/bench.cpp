#include <stdio.h>
#include <time.h>
extern "C" {
#include "comel_board.h"
}
#include "comel_c64.h"
#include "Teensy64.h"
#include "reSID.h"
extern AudioPlaySID playSID;
uint32_t host_gpio_low_mask;
static double now(){ timespec t; clock_gettime(CLOCK_MONOTONIC,&t); return t.tv_sec+t.tv_nsec*1e-9; }
int main(){
  roms_load(false); c64_init(false);
  double t0=now(); for(int i=0;i<312*500;i++) c64_step(); double t1=now();
  printf("C64: 500 quadros em %.3f s no PC (%.1f x tempo real)\n", t1-t0, 10.0/(t1-t0));
  const uint8_t regs[][2] = {{24,15},{5,9},{6,240},{1,30},{4,17},{8,40},{11,33},{13,240},{15,10},{18,65},{20,240}};
  for (auto &r: regs) playSID.setreg(r[0], r[1]);
  static int16_t s[AUDIO_BLOCK]; t0=now(); for(int i=0;i<62*10;i++) c64_audio_render(s,AUDIO_BLOCK); t1=now();
  printf("SID: 10 s de áudio em %.3f s no PC (%.0f x tempo real)\n", t1-t0, 10.0/(t1-t0));
}
