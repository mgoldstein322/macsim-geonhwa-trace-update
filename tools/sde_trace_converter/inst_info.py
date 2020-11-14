import struct
import numpy as np

class InstInfo:
    num_read_regs = np.uint8(0)    # 3-bits
    num_dest_regs = np.uint8(0)    # 3-bits
    src = []
    for _ in range(9):
        src.append(np.uint8(0)) # increased in 2019 version // 6-bits * 4 // back to 8
    dst = []
    for _ in range(6):
        dst.append(np.uint8(0)) # increased in 2019 version  6-bits * 4 // back to 8
    cf_type = np.uint8(0)          # 4 bits
    has_immediate = bool(False)       # 1bits
    opcode = np.uint8(31)           # 6 bits
    has_st = bool(False)                # 1 bit
    is_fp = bool(False)                 # 1bit
    write_flg = bool(False)             # 1bit
    num_ld = np.uint8(0)           # 2bit
    size = np.uint8(0)             # 5 bit
    # **** dynamic ****
    ld_vaddr1 = np.uint64(0)        # 4 bytes
    ld_vaddr2 = np.uint64(0)        # 4 bytes
    st_vaddr = np.uint64(0)         # 4 bytes
    ins_addr = np.uint64(0) # ins_addr # 4 bytes
    branch_target = np.uint64(0)    # not the dynamic info. static info  // 4 bytes
    mem_read_size = np.uint8(0)     # 8 bit
    mem_write_size = np.uint8(0)    # 8 bit
    rep_dir = bool(False)                # 1 bit
    actually_taken = bool(False)         # 1 ibt
    
    # added for TILESTORE
    num_st = np.uint8(0)
    st_vaddr2 = np.uint64(0)
    
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
        
