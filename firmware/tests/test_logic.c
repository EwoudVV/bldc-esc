#include <assert.h>
#include <stdint.h>
#include "commands.h"
#include "measurements.h"
int main(void) {
    assert(command_parse("help") == CMD_HELP);
    assert(command_parse("status") == CMD_STATUS);
    assert(command_parse("adc") == CMD_ADC);
    assert(command_parse("driver") == CMD_DRIVER);
    assert(command_parse("driver on") == CMD_WAKE_ON);
    assert(command_parse("driver off") == CMD_WAKE_OFF);
    assert(command_parse("") == CMD_EMPTY);
    assert(command_parse(0) == CMD_EMPTY);
    const char *rejected[] = {"arm", "run", "pwm 100", "driver on garbage", "driver on;arm", "driver onn", "driver o", "DRIVER ON"};
    for (unsigned i=0;i<sizeof rejected/sizeof rejected[0];++i) assert(command_parse(rejected[i]) == CMD_UNKNOWN);
    assert(adc_pin_mv(0)==0 && adc_pin_mv(4095)==2500);
    assert(adc_pin_mv(2048)==1250);
    assert(bus_mv(0)==0 && bus_mv(4095)==52500);
    assert(bus_mv(2048)>=26250 && bus_mv(2048)<=26260);
    assert(phase_current_ma(2048,2048)==0);
    assert(phase_current_ma(2081,2048)>1000 && phase_current_ma(2081,2048)<1020);
    assert(phase_current_ma(2015,2048)<-1000 && phase_current_ma(2015,2048)>-1020);
    for (unsigned raw=1;raw<=4095;++raw) assert(bus_mv((uint16_t)raw)>=bus_mv((uint16_t)(raw-1)));
    assert(diagnostic_wake_allowed(true,true,12000));
    assert(diagnostic_wake_allowed(true,true,30000));
    assert(!diagnostic_wake_allowed(true,true,11999));
    assert(!diagnostic_wake_allowed(true,true,30001));
    assert(!diagnostic_wake_allowed(false,true,26000));
    assert(!diagnostic_wake_allowed(true,false,26000));
    return 0;
}
