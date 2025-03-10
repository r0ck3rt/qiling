#!/usr/bin/env python3
#
# Cross Platform and Multi Architecture Advanced Binary Emulation Framework

from unicorn.x86_const import (
    UC_X86_REG_EAX,    UC_X86_REG_RAX, UC_X86_REG_RCX, UC_X86_REG_RDI,
    UC_X86_REG_RDX,    UC_X86_REG_RSI,    UC_X86_REG_R8, UC_X86_REG_R9,
    UC_X86_REG_R10
)

from qiling.cc import QlCommonBaseCC, make_arg_list

class QlIntelBaseCC(QlCommonBaseCC):
    """Calling convention base class for Intel-based systems.
    Supports arguments passing over registers and stack.
    """

    def setReturnAddress(self, addr: int) -> None:
        self.arch.stack_push(addr)

    def unwind(self, nslots: int) -> int:
        # no cleanup; just pop out the return address
        return self.arch.stack_pop()

class QlIntel64(QlIntelBaseCC):
    """Calling convention base class for Intel-based 64-bit systems.
    """

    _retreg = UC_X86_REG_RAX

    @staticmethod
    def getNumSlots(argbits: int) -> int:
        return max(argbits, 64) // 64

class QlIntel32(QlIntelBaseCC):
    """Calling convention base class for Intel-based 32-bit systems.
    """

    _retreg = UC_X86_REG_EAX

    @staticmethod
    def getNumSlots(argbits: int) -> int:
        return max(argbits, 32) // 32

    def getRawParam(self, slot: int, nbits: int = 0) -> int:
        __super_getparam = super().getRawParam

        if nbits == 64:
            lo = __super_getparam(slot)
            hi = __super_getparam(slot + 1)

            val = (hi << 32) | lo
        else:
            val = __super_getparam(slot, nbits)

        return val

class amd64(QlIntel64):
    """Default calling convention for POSIX (x86-64).
    First 6 arguments are passed in regs, the rest are passed on the stack.
    """

    _argregs = make_arg_list(UC_X86_REG_RDI, UC_X86_REG_RSI, UC_X86_REG_RDX, UC_X86_REG_R10, UC_X86_REG_R8, UC_X86_REG_R9)

class ms64(QlIntel64):
    """Default calling convention for Windows and UEFI (x86-64).
    First 4 arguments are passed in regs, the rest are passed on the stack.

    Each stack frame starts with a shadow space in size of 4 items, corresponding
    to the first arguments passed in regs.
    """

    _argregs = make_arg_list(UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R9)
    _shadow = 4

class macosx64(QlIntel64):
    """Default calling convention for Mac OS (x86-64).
    First 6 arguments are passed in regs, the rest are passed on the stack.
    """

    _argregs = make_arg_list(UC_X86_REG_RDI, UC_X86_REG_RSI, UC_X86_REG_RDX, UC_X86_REG_RCX, UC_X86_REG_R8, UC_X86_REG_R9)

class cdecl(QlIntel32):
    """Calling convention used by all operating systems (x86).
    All arguments are passed on the stack.

    The caller is resopnsible to unwind the stack.
    """

    _argregs = make_arg_list()

class stdcall(QlIntel32):
    """Calling convention used by all operating systems (x86).
    All arguments are passed on the stack.

    The callee is resopnsible to unwind the stack.
    """

    _argregs = make_arg_list()

    def unwind(self, nslots: int) -> int:
        retaddr = super().unwind(nslots)

        self.arch.regs.arch_sp += (nslots * self._asize)

        return retaddr
