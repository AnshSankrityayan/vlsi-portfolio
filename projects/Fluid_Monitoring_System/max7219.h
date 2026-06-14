#ifndef MAX7219_H
#define MAX7219_H

/*
 * MAX7219 bit-bang driver
 * DIN = PA7, CLK = PA5, CS = PA6
 * 8x8 LED matrix bargraph display, no-decode mode
 */

#include "stm32f4xx.h"
#include <stdint.h>

/* Register addresses */
#define MAX_REG_NOOP        0x00
#define MAX_REG_DIGIT0      0x01
#define MAX_REG_DIGIT1      0x02
#define MAX_REG_DIGIT2      0x03
#define MAX_REG_DIGIT3      0x04
#define MAX_REG_DIGIT4      0x05
#define MAX_REG_DIGIT5      0x06
#define MAX_REG_DIGIT6      0x07
#define MAX_REG_DIGIT7      0x08
#define MAX_REG_DECODEMODE  0x09
#define MAX_REG_INTENSITY   0x0A
#define MAX_REG_SCANLIMIT   0x0B
#define MAX_REG_SHUTDOWN    0x0C
#define MAX_REG_DISPLAYTEST 0x0F

/* Segment patterns (dp=D7, a=D6, b=D5, c=D4, d=D3, e=D2, f=D1, g=D0) */
#define SEG_E   0x4F  /* a,d,e,f,g */
#define SEG_r   0x05  /* e,g        */
#define SEG_OFF 0x00

/* GPIO bit positions */
#define MAX_DIN_PIN  7  /* PA7 */
#define MAX_CLK_PIN  5  /* PA5 */
#define MAX_CS_PIN   6  /* PA6 */

void max7219_init(void);
void max7219_write_reg(uint8_t reg, uint8_t data);
void max7219_display_bargraph(uint32_t cm);
void max7219_clear(void);

#endif /* MAX7219_H */
