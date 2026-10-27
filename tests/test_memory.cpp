// Copyright 2026 Mario Andrés Muñoz.
// Distributed under the terms of the MIT License.
#include "memory/Memory.h"
#include <cstdio>
#include <cstring>
#include <type_traits>
#include <vector>
using namespace k40::memory;
static unsigned checks=0, failed=0;
#define CHECK(c) do { ++checks; if (!(c)) { ++failed; std::printf("FAIL line %d: %s\n",__LINE__,#c); } } while(0)
struct Fake : Backend {
    std::vector<unsigned char> storage;
    unsigned frees=0, retained=0, writes=0;
    bool allocateOk=true, writeOk=true, publishOk=true, freeOk=true, verified=true;
    uint64_t device=0x100000, sizeOverride=0;
    bool allocate(uint64_t bytes,uint64_t,Placement p,Allocation& a) override {
        storage.resize(bytes); a.id=1; a.bytes=sizeOverride ? sizeOverride : bytes; a.placement=p;
        a.device={device}; a.vram={device};
        a.deviceAddressVerified=verified && p==Placement::Host;
        a.vramAddressVerified=verified && p==Placement::Vram;
        return allocateOk;
    }
    bool write(const Allocation&,uint64_t off,const void* ptr,size_t n) override {
        ++writes; if(n) std::memcpy(storage.data()+off,ptr,n); return writeOk;
    }
    bool read(const Allocation&,uint64_t off,void* ptr,size_t n) override {
        if(n) std::memcpy(ptr,storage.data()+off,n);
        return true;
    }
    bool publish(const Allocation&) override { return publishOk; }
    bool release(const Allocation&) override { ++frees; return freeOk; }
    void quarantine(const Allocation&) override { ++retained; }
};
int main() {
    static_assert(!std::is_convertible<GuestPhysical,DeviceIova>::value);
    static_assert(!std::is_convertible<DeviceIova,GpuVirtual>::value);
    static_assert(!std::is_copy_constructible<Buffer>::value);
    { Fake f; Buffer b(f); CHECK(!b.allocate(0,4,Placement::Host)); CHECK(!b.allocate(8,3,Placement::Host));
      CHECK(b.allocate(16,8,Placement::Host)); CHECK(!b.allocate(16,8,Placement::Host));
      DeviceIova address{0}; CHECK(b.deviceAddress(address) && address.value==f.device);
      CHECK(!b.pinForSubmission()); const unsigned value=0x12345678; unsigned got=0;
      CHECK(b.write(12,&value,4)); CHECK(b.read(12,&got,4) && got==value);
      CHECK(!b.write(13,&value,4)); CHECK(!b.read(UINT64_MAX,&got,4)); CHECK(!b.write(0,nullptr,4));
      CHECK(b.publish() && b.pinForSubmission()); CHECK(!b.write(0,&value,4));
      CHECK(!b.close() && !b.retire(false) && f.frees==0);
      CHECK(b.retire(true)); CHECK(b.close() && f.frees==1); CHECK(!b.deviceAddress(address)); CHECK(!b.publish()); }
    { Fake f; Buffer b(f); CHECK(b.allocate(16,4,Placement::Host)); CHECK(b.publish());
      f.writeOk=false; unsigned v=0; CHECK(!b.write(0,&v,4)); CHECK(!b.visible() && !b.pinForSubmission()); }
    { Fake f; f.verified=false; Buffer b(f); DeviceIova a{0}; CHECK(b.allocate(16,4,Placement::Host)); CHECK(!b.deviceAddress(a)); CHECK(b.publish() && !b.pinForSubmission()); }
    { Fake f; f.publishOk=false; Buffer b(f); CHECK(b.allocate(16,4,Placement::Vram)); CHECK(!b.publish() && !b.pinForSubmission()); }
    { Fake f; f.allocateOk=false; Buffer b(f); CHECK(!b.allocate(16,4,Placement::Host) && !b.owned() && f.frees==1); }
    { Fake f; f.sizeOverride=8; Buffer b(f); CHECK(!b.allocate(16,4,Placement::Host) && f.frees==1); }
    { Fake f; f.device=UINT64_MAX-7; Buffer b(f); CHECK(!b.allocate(16,8,Placement::Host) && f.frees==1); }
    { Fake f; f.device=3; Buffer b(f); CHECK(!b.allocate(16,8,Placement::Host) && f.frees==1); }
    { Fake f; { Buffer b(f); CHECK(b.allocate(16,4,Placement::Host)); CHECK(b.publish() && b.pinForSubmission()); }
      CHECK(f.retained==1 && f.frees==0); }
    { Fake f; f.freeOk=false; { Buffer b(f); CHECK(b.allocate(16,4,Placement::Host)); CHECK(!b.close()); }
      CHECK(f.retained==1); }
    { Fake f; f.allocateOk=false; f.freeOk=false; { Buffer b(f); CHECK(!b.allocate(16,4,Placement::Host)); }
      CHECK(f.frees==1 && f.retained==1); }
    { Fake f; Buffer b(f); CHECK(b.allocate(16,4,Placement::Host) && b.publish());
      f.freeOk=false; CHECK(!b.close() && b.owned() && !b.visible());
      DeviceIova address{0}; unsigned value=0;
      CHECK(!b.deviceAddress(address) && !b.publish() && !b.pinForSubmission());
      CHECK(!b.read(0,&value,4) && !b.write(0,&value,4));
      f.freeOk=true; CHECK(b.close() && !b.owned()); }
    std::printf("memory ownership/publication: %u checks, %u failures (HOST_ONLY)\n",checks,failed);
    return failed ? 1 : 0;
}
