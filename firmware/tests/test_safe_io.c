#include <assert.h>
#include "board.h"
GPIO_TypeDef mock_a,mock_b,mock_c,mock_d,mock_e,mock_f;
RCC_TypeDef mock_rcc;
PWR_TypeDef mock_pwr;
GPIO_TypeDef *checked_gpioa(void) {
    /* PA10 must not activate the PB4 dead-battery pull-down. */
    assert(mock_pwr.CR3 & (1U<<14));
    return &mock_a;
}
static void expect_outputs(GPIO_TypeDef *port,uint32_t pins) {
    for (unsigned pin=0;pin<16;++pin) if (pins & (1U<<pin)) {
        assert(((port->MODER>>(2*pin))&3U)==1U);
        assert((port->OTYPER & (1U<<pin))==0);
    }
}
int main(void) {
    mock_a.MODER=0xaaaaaaaaU;
    mock_c.MODER=0xaaaaaaaaU;
    board_early_safe();
    assert(mock_rcc.AHB2ENR==0x3fU);
    assert(mock_rcc.APB1ENR1 & (1U<<28));
    assert(mock_e.BSRR==(0x3f1fU<<16));
    assert(mock_c.BSRR==(1U<<(12+16)));
    assert(mock_f.BSRR==(1U<<(9+16)));
    assert(mock_d.BSRR==(1U<<(2+16)));
    assert(mock_a.BSRR==(1U<<10));
    assert(mock_b.BSRR==((1U<<12)|(1U<<7)));
    expect_outputs(&mock_e,0x3f1fU);
    expect_outputs(&mock_c,1U<<12);
    expect_outputs(&mock_f,1U<<9);
    expect_outputs(&mock_d,1U<<2);
    expect_outputs(&mock_a,1U<<10);
    expect_outputs(&mock_b,(1U<<12)|(1U<<7));
    assert(((mock_a.MODER>>26)&15U)==10U); /* SWD pins untouched. */
    assert(((mock_c.MODER>>20)&15U)==10U); /* UART pins untouched. */
    return 0;
}
