// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "memstage/Faults.h"
#include "memory/VramArena.h"
namespace k40::memstage {
enum class Lock:uint8_t {Window,Mmu};
enum class CacheProfile:uint8_t {Unknown,ExplicitUncached};
class Io:public ReadPort {
public:
    virtual bool active() const=0; // Private native grant/latch decides; no public activation API.
    virtual CacheProfile profile() const=0;
    virtual bool acquire(Lock)=0; // Bounded, never an unbounded blocking wait.
    virtual void release(Lock)=0;
    virtual bool write32(uint32_t,uint32_t)=0;
    virtual bool storeFence()=0;
    virtual bool loadFence()=0;
    virtual bool barRead32(uint64_t offset,uint32_t& value)=0; // Read-only BAR1 prefix.
    virtual bool barWrite32(uint64_t offset,uint32_t value)=0; // Only the reviewed GP_PUT word.
};
class LockGuard {
public:
    LockGuard(Io& io,Lock lock):io_(io),lock_(lock),held_(io.acquire(lock)){}
    ~LockGuard(){if(held_)io_.release(lock_);}
    bool held() const{return held_;}
    LockGuard(const LockGuard&)=delete;LockGuard& operator=(const LockGuard&)=delete;
private:Io& io_;Lock lock_;bool held_;
};
enum class Image:uint8_t {Zero,Pattern,Complement};
// Supplies the 32-bit words of one bulk write (S3 images and page tables).
class WordSource {
public:
    virtual ~WordSource()=default;
    virtual uint32_t at(uint32_t index) const=0;
};
class Upload {
public:
    Upload(Io& io,Faults& faults,Journal& journal,memory::vram::Arena& arena)
        :io_(io),faults_(faults),journal_(journal),arena_(arena){}
    bool zero(memory::vram::Token);
    bool exercise(memory::vram::Token a,memory::vram::Token b);
    // S2: write and verify the address-dependent pattern of the copy source.
    bool fill(memory::vram::Token source);
    // S2: read every word of dest; true only if it equals the pattern of source.
    // A difference is journaled as a Compare event and latches no error: teardown still runs.
    bool matches(memory::vram::Token dest,memory::vram::Token source);
    // S3: write count words at a byte offset, flush once, read all back and compare.
    // update: the record is referenced (Arena::update); otherwise it must not be.
    bool store(memory::vram::Token,uint64_t offset,uint32_t count,const WordSource&,bool update=false);
    // S3: read count words at a byte offset into out (result buffers).
    bool load(memory::vram::Token,uint64_t offset,uint32_t count,uint32_t* out);
    bool flush();
    void phase(Phase p){phase_=p;} // The journal phase of later operations (S3 stage).
    bool healthy() const{return error_==Error::None && arena_.healthy() && faults_.ready();}
    Error error() const{return error_;}
    static uint32_t pattern(uint64_t physical,Image);
private:
    friend class Mapper;
    friend class Channel;
    bool fail(Error,uint32_t=0,uint32_t=0);
    bool allowed();
    bool begin();
    bool tick(uint64_t budget);
    bool address(memory::vram::Token,uint64_t,uint64_t&);
    bool transfer(memory::vram::Token,Image,bool write,const memory::vram::Record* like=nullptr);
    bool window(uint64_t physical,uint64_t& selected);
    bool flushLocked();
    bool patch(memory::vram::Token,uint64_t offset,uint64_t value,bool update=false);
    Io& io_;Faults& faults_;Journal& journal_;memory::vram::Arena& arena_;
    Phase phase_=Phase::Physical;Error error_=Error::None;uint64_t start_=0,last_=0;
};
}
