from pymem.process import module_from_name
import pymem.memory

pm = pymem.Pymem("Tutorial-i386.exe")


def get(base, offsets):
    addr = pm.read_int(base)
    for i in offsets:
        if i != offsets[-1]:
            addr = pm.read_int(addr + i)
    return addr + offsets[-1]


game = module_from_name(pm.process_handle, "Tutorial-i386.exe").lpBaseOfDll
pm_base = pm.process_handle
adress = 0x0173D318
print(pm.read_int(get(game + 0x0017F160, [0x8B4, 0x1C, 0xC, 0x14, 0x14, 0x264, 0x770])))