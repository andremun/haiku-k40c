// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
// Replay captured slave ACK responses, not Linux's unrelated callback schedule.
#include "i2c_wire.h"
#include "devinit/I2c.h"
#include <iostream>
using namespace k40::devinit;
struct ResponseWire:Wire {
    std::vector<unsigned> responses;
    bool read32(uint32_t at,uint32_t& out) override {
        if(!Wire::read32(at,out))return false;
        if(active && phase==9) {
            if(!ack || ack>responses.size())return false;
            out=(out&~0x20u)|(responses[ack-1]?0:0x20u);
        }
        return true;
    }
};
int main()
{
    unsigned cases=0,address,reg,value,count;
    while(std::cin>>address>>reg>>value>>count) {
        ResponseWire wire;std::vector<uint8_t> expected;
        for(unsigned i=0;i<count;++i) {unsigned byte,ack;if(!(std::cin>>byte>>ack))return 2;expected.push_back(uint8_t(byte));wire.responses.push_back(ack);}
        I2cBus bus;bus.index=2;bus.type=5;bus.drive=2;
        DedicatedI2c engine(wire,wire);
        if(!engine.initialize(bus))return 3;
        const bool success=engine.i2cWrite(bus,uint8_t(address),uint8_t(reg),uint8_t(value));
        const auto result=engine.result();
        if(wire.decoded!=expected || wire.starts!=1 || wire.stops!=1 || result.cleanup!=I2cError::None)return 4;
        if(count==1 && (success || result.primary!=I2cError::Nack || result.phase!=I2cPhase::Address || result.bit!=8))return 5;
        if(count==3 && (!success || result.primary!=I2cError::None))return 6;
        std::cout<<"case "<<++cases<<" success "<<success<<" primary "<<unsigned(result.primary)<<" cleanup "<<unsigned(result.cleanup)<<" phase "<<unsigned(result.phase)<<" bit "<<result.bit<<" transmitted "<<wire.decoded.size()<<"\n";
    }
    return cases?0:7;
}
