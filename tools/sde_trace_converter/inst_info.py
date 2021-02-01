import struct
import numpy as np

class InstInfo:
    def __init__(self):
        self.num_read_regs = np.uint8(0)    # 3-bits
        self.num_dest_regs = np.uint8(0)    # 3-bits
        self.src = []
        for _ in range(9):
            self.src.append(np.uint8(0)) # increased in 2019 version // 6-bits * 4 // back to 8
        self.dst = []
        for _ in range(6):
            self.dst.append(np.uint8(0)) # increased in 2019 version  6-bits * 4 // back to 8
        self.cf_type = np.uint8(0)          # 4 bits
        self.has_immediate = bool(False)       # 1bits
        self.opcode = np.uint8(31)           # 6 bits
        self.has_st = bool(False)                # 1 bit
        self.is_fp = bool(False)                 # 1bit
        self.write_flg = bool(False)             # 1bit
        self.num_ld = np.uint8(0)           # 2bit
        self.size = np.uint8(0)             # 5 bit
        # **** dynamic ****
        self.ld_vaddr1 = np.uint64(0)        # 4 bytes
        self.ld_vaddr2 = np.uint64(0)        # 4 bytes
        self.st_vaddr = np.uint64(0)         # 4 bytes
        self.ins_addr = np.uint64(0) # ins_addr # 4 bytes
        self.branch_target = np.uint64(0)    # not the dynamic info. static info  // 4 bytes
        self.mem_read_size = np.uint8(0)     # 8 bit
        self.mem_write_size = np.uint8(0)    # 8 bit
        self.rep_dir = bool(False)                # 1 bit
        self.actually_taken = bool(False)         # 1 ibt
        
        # added for TILESTORE
        self.num_st = np.uint8(0)
        self.st_vaddr2 = np.uint64(0)
    def test(self):
        print(self.opcode)
    def init_ins(self):
        self.num_read_regs = np.uint8(0)    # 3-bits
        self.num_dest_regs = np.uint8(0)    # 3-bits
        self.src = []
        for _ in range(9):
            self.src.append(np.uint8(0)) # increased in 2019 version // 6-bits * 4 // back to 8
        self.dst = []
        for _ in range(6):
            self.dst.append(np.uint8(0)) # increased in 2019 version  6-bits * 4 // back to 8
        self.cf_type = np.uint8(0)          # 4 bits
        self.has_immediate = bool(False)       # 1bits
        self.opcode = np.uint8(31)           # 6 bits
        self.has_st = bool(False)                # 1 bit
        self.is_fp = bool(False)                 # 1bit
        self.write_flg = bool(False)             # 1bit
        self.num_ld = np.uint8(0)           # 2bit
        self.size = np.uint8(0)             # 5 bit
        # **** dynamic ****
        self.ld_vaddr1 = np.uint64(0)        # 4 bytes
        self.ld_vaddr2 = np.uint64(0)        # 4 bytes
        self.st_vaddr = np.uint64(0)         # 4 bytes
        self.instruction_addr = np.uint64(0) # 4 bytes
        self.branch_target = np.uint64(0)    # not the dynamic info. static info  // 4 bytes
        self.mem_read_size = np.uint8(0)     # 8 bit
        self.mem_write_size = np.uint8(0)    # 8 bit
        self.rep_dir = bool(False)                # 1 bit
        self.actually_taken = bool(False)         # 1 ibt
        
        # added for TILESTORE
        self.num_st = np.uint8(0)
        self.st_vaddr2 = np.uint64(0) 

    # Copy ins from copy to this except inst
    def copy_ins(self, tmp):
        self.num_read_regs = tmp.num_read_regs    # 3-bits
        self.num_dest_regs = tmp.num_dest_regs    # 3-bits
        for i in range(9):
            self.src[i] = tmp.src[i] # increased in 2019 version // 6-bits * 4 // back to 8
        for i in range(6):
            self.dst[i] = tmp.dst[i] # increased in 2019 version  6-bits * 4 // back to 8
        self.cf_type = tmp.cf_type          # 4 bits
        self.has_immediate = tmp.has_immediate       # 1bits
        self.opcode = tmp.opcode           # 6 bits
        self.has_st = tmp.has_st                # 1 bit
        self.is_fp = tmp.is_fp                 # 1bit
        self.write_flg = tmp.write_flg             # 1bit
        self.num_ld = tmp.num_ld           # 2bit
        self.size = tmp.size             # 5 bit
        # **** dynamic ****
        self.ld_vaddr1 = tmp.ld_vaddr1        # 4 bytes
        self.ld_vaddr2 = tmp.ld_vaddr2        # 4 bytes
        self.st_vaddr = tmp.st_vaddr         # 4 bytes
        #self.instruction_addr = np.uint64(0) # 4 bytes DON'T CHANGE PC
        self.branch_target = tmp.branch_target    # not the dynamic info. static info  // 4 bytes
        self.mem_read_size = tmp.mem_read_size     # 8 bit
        self.mem_write_size = tmp.mem_write_size    # 8 bit
        self.rep_dir = tmp.rep_dir                # 1 bit
        self.actually_taken = tmp.actually_taken         # 1 ibt
        
        # added for TILESTORE
        self.num_st = tmp.num_st
        self.st_vaddr2 = tmp.st_vaddr2 
    
    def get_macsim_ins(self):
        info = struct.pack('BBBBBBBBBBBBBBBBBB?B???BBQQQQQBB??', 
                self.num_read_regs, self.num_dest_regs, 
                self.src[0], self.src[1], self.src[2], self.src[3], self.src[4], self.src[5], self.src[6], self.src[7], self.src[8], 
                self.dst[0], self.dst[1], self.dst[2], self.dst[3], self.dst[4], self.dst[5],
                self.cf_type, self.has_immediate, self.opcode, self.has_st, self.is_fp, self.write_flg, self.num_ld, self.size, 
                self.ld_vaddr1, self.ld_vaddr2, self.st_vaddr, self.ins_addr, self.branch_target, self.mem_read_size, self.mem_write_size,
                self.rep_dir, self.actually_taken)
            
        ins = info + b'0000'
        assert(len(ins) == 80)
        return ins
        
