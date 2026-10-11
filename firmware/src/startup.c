#include <stdint.h>
#include "board.h"
extern uint32_t _estack, _sidata, _sdata, _edata, _sbss, _ebss;
int main(void);
void Reset_Handler(void);
void SysTick_Handler(void);
static void Fault_Handler(void) { board_panic(); }
__attribute__((section(".isr_vector"),used,aligned(512)))
const uintptr_t vectors[16 + FMAC_IRQn + 1] = {
    [0] = (uintptr_t)&_estack,
    [1] = (uintptr_t)Reset_Handler,
    [2 ... 14] = (uintptr_t)Fault_Handler,
    [15] = (uintptr_t)SysTick_Handler,
    [16 ... 16 + FMAC_IRQn] = (uintptr_t)Fault_Handler
};
void Reset_Handler(void) {
    __disable_irq();
    board_early_safe();
    uint32_t *src = &_sidata;
    for (uint32_t *dst = &_sdata; dst < &_edata;) *dst++ = *src++;
    for (uint32_t *dst = &_sbss; dst < &_ebss;) *dst++ = 0;
    SystemInit();
    SCB->VTOR = (uint32_t)vectors;
    (void)main();
    board_panic();
}
void SysTick_Handler(void) { HAL_IncTick(); }
