/*
 * ================================================================
 *  TEST 1 — HC-SR04 Ultrasonic Sensor only
 * ================================================================
 *  Wiring:
 *    HC-SR04 VCC  → Nucleo 5V  (CN7 pin 18  or  CN10 pin 8)
 *    HC-SR04 GND  → Nucleo GND (CN7 pin 20  or  CN10 pin 20)
 *    HC-SR04 Trig → PA0        (CN7 pin 28  or  CN10 pin 29)
 *    HC-SR04 Echo → PA1        (CN7 pin 30  or  CN10 pin 31)
 *
 *  How it works:
 *    1. We pulse Trig HIGH for 10 µs  → sensor fires ultrasound burst
 *    2. Echo pin goes HIGH for however long the sound takes to bounce back
 *    3. We measure that HIGH time in microseconds
 *    4. distance (cm) = pulse_µs / 58
 *
 *  Output: distance printed over UART2 → USB serial → PlatformIO monitor
 *    Open monitor with:  pio device monitor --baud 115200
 *    Or press the plug icon in VS Code bottom bar
 *
 *  How to verify:
 *    - Hold a flat object (book/hand) in front of sensor
 *    - Move it closer / farther — number should change smoothly
 *    - Valid range: ~2 cm to ~400 cm
 *    - If you see 0     → echo not received (wiring issue or too close)
 *    - If you see 999   → timeout (nothing in range or echo pin floating)
 *    - If numbers jump wildly → add a 1 kΩ resistor on Echo line (5V→3.3V)
 *
 *  Board: STM32 Nucleo-F401RE  |  84 MHz
 * ================================================================
 */

#include "stm32f4xx.h"
#include "max7219.h"
#include <stdint.h>
#include <stdio.h>      /* for sprintf */

/* ------------------------------------------------------------------ */
/*  System clock — 84 MHz (HSI → PLL)                                 */
/* ------------------------------------------------------------------ */
static void clock_init(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_PWREN;
    PWR->CR      |= PWR_CR_VOS;

    FLASH->ACR = FLASH_ACR_LATENCY_2WS | FLASH_ACR_PRFTEN
               | FLASH_ACR_ICEN | FLASH_ACR_DCEN;

    /* HSI → PLL: M=16, N=336, P=4  →  84 MHz */
    RCC->PLLCFGR = (16u  << RCC_PLLCFGR_PLLM_Pos)
                 | (336u << RCC_PLLCFGR_PLLN_Pos)
                 | (1u   << RCC_PLLCFGR_PLLP_Pos)   /* P=4 */
                 | (0u   << RCC_PLLCFGR_PLLSRC_Pos) /* HSI */
                 | (7u   << RCC_PLLCFGR_PLLQ_Pos);

    RCC->CFGR = RCC_CFGR_HPRE_DIV1 | RCC_CFGR_PPRE1_DIV2 | RCC_CFGR_PPRE2_DIV1;

    RCC->CR |= RCC_CR_PLLON;
    while (!(RCC->CR & RCC_CR_PLLRDY));

    RCC->CFGR |= RCC_CFGR_SW_PLL;
    while ((RCC->CFGR & RCC_CFGR_SWS) != RCC_CFGR_SWS_PLL);

    SystemCoreClockUpdate();
}

/* ------------------------------------------------------------------ */
/*  DWT — cycle-accurate microsecond delay + timestamp                 */
/*                                                                     */
/*  DWT = Data Watchpoint and Trace unit, built into every Cortex-M4. */
/*  CYCCNT counts CPU cycles (84 million per second at 84 MHz).       */
/* ------------------------------------------------------------------ */
static void dwt_init(void)
{
    CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk; /* enable trace */
    DWT->CYCCNT = 0;
    DWT->CTRL  |= DWT_CTRL_CYCCNTENA_Msk;           /* start counter */
}

/* Spin for exactly 'us' microseconds */
static void delay_us(uint32_t us)
{
    uint32_t start  = DWT->CYCCNT;
    uint32_t target = us * (SystemCoreClock / 1000000u);
    while ((DWT->CYCCNT - start) < target);
}

/* Return elapsed microseconds since a saved DWT snapshot */
static inline uint32_t elapsed_us(uint32_t since)
{
    return (DWT->CYCCNT - since) / (SystemCoreClock / 1000000u);
}

/* ------------------------------------------------------------------ */
/*  SysTick — simple 1 ms counter for pacing measurements             */
/* ------------------------------------------------------------------ */
static volatile uint32_t ms_tick = 0;
void SysTick_Handler(void) { ms_tick++; }

static void delay_ms(uint32_t ms)
{
    uint32_t t = ms_tick;
    while ((ms_tick - t) < ms);
}

/* ------------------------------------------------------------------ */
/*  GPIO init                                                          */
/*                                                                     */
/*  MODER bits: 00=input, 01=output, 10=alternate function, 11=analog */
/* ------------------------------------------------------------------ */
static void gpio_init(void)
{
    /* Enable clocks for GPIOA and GPIOB */
    RCC->AHB1ENR |= RCC_AHB1ENR_GPIOAEN | RCC_AHB1ENR_GPIOBEN;
    __DSB();

    /* PB0 = status LED → output push-pull, start LOW */
    GPIOB->MODER  = (GPIOB->MODER & ~(3u << 0)) | (1u << 0);
    GPIOB->OTYPER &= ~(1u << 0);
    GPIOB->BSRR    = (1u << (0 + 16));

    /* PA0 = Trig → output push-pull */
    GPIOA->MODER  = (GPIOA->MODER & ~(3u << 0)) | (1u << 0); /* MODER0 = 01 */
    GPIOA->OTYPER &= ~(1u << 0);                              /* push-pull   */
    GPIOA->BSRR    = (1u << (0 + 16));                        /* start LOW   */

    /* PA1 = Echo → input, no pull (HC-SR04 drives it) */
    GPIOA->MODER &= ~(3u << 2);  /* MODER1 = 00 (input) */
    GPIOA->PUPDR &= ~(3u << 2);  /* no pull              */

    /* PA4 = potentiometer → analog */
    GPIOA->MODER |= (3u << 8);   /* MODER4 = 11 (analog) */

    /* PA2 = USART2 TX → alternate function AF7 */
    GPIOA->MODER  = (GPIOA->MODER  & ~(3u << 4))  | (2u << 4);  /* AF mode */
    GPIOA->AFR[0] = (GPIOA->AFR[0] & ~(0xFu << 8)) | (7u << 8); /* AF7     */
    GPIOA->OTYPER &= ~(1u << 2);

    /* PA3 = relay → output push-pull, start LOW (relay off) */
    GPIOA->MODER  = (GPIOA->MODER & ~(3u << 6)) | (1u << 6);
    GPIOA->OTYPER &= ~(1u << 3);
    GPIOA->BSRR    = (1u << (3 + 16));  /* start LOW */

    /* PA5=CLK, PA6=CS, PA7=DIN → outputs for MAX7219 */
    GPIOA->MODER  |= (1u << 10) | (1u << 12) | (1u << 14); /* output mode */
    GPIOA->OTYPER &= ~((1u << 5) | (1u << 6) | (1u << 7)); /* push-pull   */
    GPIOA->BSRR    = (1u << 6) | (1u << (5+16)) | (1u << (7+16)); /* CS HIGH, CLK/DIN LOW */
}

/* ------------------------------------------------------------------ */
/*  USART2 init — 115200 baud, TX only (PA2)                          */
/*                                                                     */
/*  USART2 is wired to the Nucleo's ST-Link chip, which acts as a     */
/*  USB-to-serial bridge. Plug in USB → it appears as a COM port.     */
/*  PCLK1 = 42 MHz  →  BRR = 42000000 / 115200 ≈ 364.58             */
/*  BRR mantissa = 364, fraction = 0.58 * 16 ≈ 9  →  BRR = 0x16C9  */
/* ------------------------------------------------------------------ */
static void uart_init(void)
{
    RCC->APB1ENR |= RCC_APB1ENR_USART2EN;
    __DSB();

    uint32_t pclk1 = SystemCoreClock / 2;
    USART2->BRR = (pclk1 + 57600u) / 115200u; /* 115200 baud, auto-calculated */
    USART2->CR1 = USART_CR1_TE        /* TX enable                   */
                | USART_CR1_UE;       /* USART enable                */
}

/* ------------------------------------------------------------------ */
/*  ADC — potentiometer on PA4 (ADC1 channel 4)                       */
/* ------------------------------------------------------------------ */
static void adc_init(void)
{
    RCC->APB2ENR |= RCC_APB2ENR_ADC1EN;
    __DSB();
    ADC1->SQR3 = 4;           /* channel 4 = PA4 */
    ADC1->SMPR2 |= (7u << 12); /* max sample time for stability */
    ADC1->CR2   = ADC_CR2_ADON;
}

static uint32_t adc_read(void)
{
    ADC1->CR2 |= ADC_CR2_SWSTART;
    while (!(ADC1->SR & ADC_SR_EOC));
    return ADC1->DR;
}

/* map 12-bit ADC (0-4095) to 0-200 cm */
static uint32_t pot_read_cm(void)
{
    return adc_read() * 200u / 4095u;
}

/* Send one character — wait if TX buffer busy */
static void uart_putc(char c)
{
    while (!(USART2->SR & USART_SR_TXE));
    USART2->DR = (uint8_t)c;
}

/* Send a null-terminated string */
static void uart_puts(const char *s)
{
    while (*s) uart_putc(*s++);
}

/* ------------------------------------------------------------------ */
/*  HC-SR04 measurement                                                */
/*                                                                     */
/*  Sequence:                                                          */
/*   1. Pull Trig HIGH for 10 µs                                      */
/*   2. Wait for Echo to go HIGH (sensor starts sending)              */
/*   3. Measure how long Echo stays HIGH                              */
/*   4. distance = pulse_µs / 58   (speed of sound round-trip)       */
/*                                                                     */
/*  Returns 0   if echo never arrived  (too close / bad wiring)       */
/*  Returns 999 if echo too long       (nothing in range, >4 m)       */
/* ------------------------------------------------------------------ */
#define ECHO_WAIT_TIMEOUT_US  30000u  /* 30 ms — if echo not seen, abort */
#define ECHO_MAX_US           23200u  /* ~4 m round trip                 */

static uint32_t hcsr04_measure_cm(void)
{
    /* --- Fire trigger pulse --- */
    GPIOA->BSRR = (1u << 0);    /* PA0 HIGH */
    delay_us(10);
    GPIOA->BSRR = (1u << 16);   /* PA0 LOW  */

    /* --- Wait for Echo to go HIGH --- */
    uint32_t t0 = DWT->CYCCNT;
    while (!(GPIOA->IDR & (1u << 1))) {          /* PA1 still LOW? */
        if (elapsed_us(t0) > ECHO_WAIT_TIMEOUT_US)
            return 0;   /* echo never came — wiring problem or too close */
    }

    /* --- Measure how long Echo stays HIGH --- */
    uint32_t rise = DWT->CYCCNT;
    while (GPIOA->IDR & (1u << 1)) {             /* PA1 still HIGH? */
        if (elapsed_us(rise) > ECHO_MAX_US)
            return 999; /* nothing in range */
    }

    uint32_t pulse_us = elapsed_us(rise);
    return pulse_us / 58u;   /* convert to cm */
}

/* ------------------------------------------------------------------ */
/*  Main                                                               */
/* ------------------------------------------------------------------ */
int main(void)
{
    clock_init();
    dwt_init();
    SysTick_Config(SystemCoreClock / 1000u);  /* 1 ms tick */

    gpio_init();
    uart_init();
    adc_init();
    delay_ms(10);
    max7219_init();

    /* PA3 test blink — 3 quick flashes on startup */
    for (int i = 0; i < 3; i++) {
        GPIOA->BSRR = (1u << 3);        delay_ms(200);
        GPIOA->BSRR = (1u << (3 + 16)); delay_ms(200);
    }

    uart_puts("\r\n=== Fluid Controller ===\r\n\r\n");

    #define MARGIN 5u  /* hysteresis band in cm */

    char     buf[96];
    uint32_t history[5] = {0};
    uint8_t  hist_idx   = 0;
    uint8_t  hist_count = 0;
    int32_t  prev_cm    = -1;
    uint8_t  blink      = 0;

    while (1) {
        /* --- smooth distance --- */
        uint32_t raw = hcsr04_measure_cm();
        if (raw == 999) raw = 200;
        history[hist_idx++ % 5] = raw;
        if (hist_count < 5) hist_count++;
        uint32_t cm = 0;
        for (uint8_t j = 0; j < hist_count; j++) cm += history[j];
        cm /= hist_count;

        /* --- potentiometer threshold --- */
        uint32_t limit = pot_read_cm();

        /* --- 3-zone state machine --- */
        const char *status;
        int32_t delta = (int32_t)cm - (int32_t)limit;
        if      (delta < -(int32_t)MARGIN) status = "CRITICAL";
        else if (delta <  (int32_t)MARGIN) status = "WARNING";
        else                               status = "SAFE";

        /* --- trend + rate --- */
        int32_t rate = (prev_cm >= 0) ? ((int32_t)cm - prev_cm) : 0;
        const char *trend = (rate >  2) ? "RISING"
                          : (rate < -2) ? "FALLING"
                          :               "STABLE";
        prev_cm = (int32_t)cm;

        /* --- JSON output (ESP32-ready) --- */
        sprintf(buf, "{\"dist\":%lu,\"limit\":%lu,\"status\":\"%s\",\"trend\":\"%s\",\"rate\":%ld}\r\n",
                (unsigned long)cm, (unsigned long)limit,
                status, trend, (long)rate);
        uart_puts(buf);

        /* --- relay --- */
        if (status[0] == 'C')  /* CRITICAL */
            GPIOA->BSRR = (1u << 3);        /* PA3 HIGH → relay ON  */
        else
            GPIOA->BSRR = (1u << (3 + 16)); /* PA3 LOW  → relay OFF */

        /* --- status LED on PB0 --- */
        blink ^= 1;
        if (status[0] == 'S')      /* SAFE → off */
            GPIOB->BSRR = (1u << (0 + 16));
        else if (status[0] == 'W') /* WARNING → solid on */
            GPIOB->BSRR = (1u << 0);
        else                       /* CRITICAL -> blink once per loop */
            GPIOB->BSRR = blink ? (1u << 0) : (1u << (0 + 16));

        /* --- display --- */
        if (cm < 80) max7219_display_bargraph(cm);
        else         max7219_clear();

        delay_ms(1000);
    }
}
