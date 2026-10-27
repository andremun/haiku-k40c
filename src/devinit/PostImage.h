// Copyright 2026 Mario Andres Munoz.
// Distributed under the terms of the MIT License.
#pragma once
#include "devinit/BoardPolicy.h"
#include "devinit/Interpreter.h"
namespace k40::devinit {
struct PostInstruction { uint32_t offset = 0, bytes = 0; uint8_t opcode = 0; };
// Inspection has no approval status. Execution always constructs its own layout
// from the privately owned, hashed snapshot. Public inspection permits fuzz tests.
class PostLayout {
public:
    Error inspect(const uint8_t*, uint32_t);
    uint32_t count() const { return count_; }
    uint32_t roots() const { return roots_; }
    uint32_t root(uint32_t index) const { return index < roots_ ? rootsList_[index] : 0; }
    const PostInstruction* instruction(uint32_t pc) const;
    const PostInstruction* at(uint32_t index) const { return index < count_ ? &code_[index] : nullptr; }
    Tables tables(uint8_t group) const { return {conditions_,macros_,uint8_t(groups_),group}; }
    bool group(uint8_t strap, uint8_t& result) const;
    bool allow(uint32_t pc, uint32_t reg, unsigned width, bool write) const;
private:
    bool span(uint32_t, uint32_t) const;
    uint32_t get(uint32_t at, unsigned bytes) const;
    bool normal(uint32_t) const;
    bool table(uint32_t field, uint32_t& pointer) const;
    Error parse();
    const uint8_t* rom_ = nullptr;
    uint32_t size_ = 0, conditions_ = 0, macros_ = 0, groups_ = 0, roots_ = 0, count_ = 0;
    uint32_t gpio_ = 0;
    std::array<uint8_t,16> ram_{};
    // no source: software parser capacities; exhaustion denies input.
    std::array<uint32_t,256> rootsList_{};
    // no source: software parser capacity, not a hardware limit.
    std::array<PostInstruction,1024> code_{};
};
class BoundPost;
class PostImage {
    friend class BoundPost;
public:
    PostImage(const uint8_t*, uint32_t);
    PostImage(const PostImage&) = delete;
    PostImage& operator=(const PostImage&) = delete;
    bool approved() const { return approved_; }
    Error layoutError() const { return layoutError_; }
    Error selectRam(Backend&); // At most one attempted read; host-only.
    bool ramSelected() const { return selected_; }
    uint8_t ramIndex() const { return group_; }
    uint32_t instructionCount() const { return layout_.count(); }
    uint32_t roots() const { return layout_.roots(); }
    uint32_t root(uint32_t i) const { return layout_.root(i); }
    bool allow(uint32_t pc, uint32_t reg, unsigned width, bool write) const {
        return approved_ && layout_.allow(pc,reg,width,write);
    }
private:
    // Large storage belongs in a persistent owner or host heap, not a kernel stack.
    std::array<uint8_t,approvedRomBytes> rom_{};
    PostLayout layout_;
    bool i2cPreparationAttempted_ = false;
    bool approved_ = false, selectionAttempted_ = false, selected_ = false, attempted_ = false;
    uint8_t group_ = 0;
    Error layoutError_ = Error::Input;
};
}
