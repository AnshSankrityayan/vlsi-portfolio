#include "max7219.h"
#include "stm32f4xx.h"

static void spi_delay(void) {
    for (volatile int i = 0; i < 100; i++);
}

#define M_CLK_LO()  (GPIOA->BSRR = (1u << (5 + 16)))
#define M_CLK_HI()  (GPIOA->BSRR = (1u << 5))
#define M_CS_LO()   (GPIOA->BSRR = (1u << (6 + 16)))
#define M_CS_HI()   (GPIOA->BSRR = (1u << 6))
#define M_DIN_LO()  (GPIOA->BSRR = (1u << (7 + 16)))
#define M_DIN_HI()  (GPIOA->BSRR = (1u << 7))

void max7219_write_reg(uint8_t reg, uint8_t data)
{
    uint16_t word = ((uint16_t)reg << 8) | data;
    M_CS_LO();
    for (int i = 15; i >= 0; i--) {
        M_CLK_LO();
        spi_delay();
        if (word & (1u << i)) M_DIN_HI(); else M_DIN_LO();
        M_CLK_HI();
        spi_delay();
    }
    M_CS_HI();
}

void max7219_init(void)
{
    max7219_write_reg(MAX_REG_DISPLAYTEST, 0x00); /* test mode off    */
    max7219_write_reg(MAX_REG_SCANLIMIT,   0x07); /* all 8 rows       */
    max7219_write_reg(MAX_REG_DECODEMODE,  0x00); /* raw matrix data  */
    max7219_write_reg(MAX_REG_INTENSITY,   0x08); /* mid brightness   */
    max7219_write_reg(MAX_REG_SHUTDOWN,    0x01); /* normal operation */
    for (uint8_t r = 1; r <= 8; r++)
        max7219_write_reg(r, 0x00);               /* clear display    */
}

/*
 * Bar graph: cm=0 means all columns lit; cm>=80 means clear display.
 * Each column represents about 10 cm.
 */
void max7219_display_bargraph(uint32_t cm)
{
    /* 0-80cm range, each column = 10cm, closer = more columns lit */
    uint8_t cols;
    if (cm >= 80) cols = 0;
    else          cols = 8 - (uint8_t)(cm / 10);

    for (uint8_t c = 1; c <= 8; c++)
        max7219_write_reg(c, (c <= cols) ? 0xFF : 0x00);
}

void max7219_clear(void)
{
    for (uint8_t r = 1; r <= 8; r++)
        max7219_write_reg(r, 0x00);
}
