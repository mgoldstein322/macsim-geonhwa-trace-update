import struct
import numpy as np
from tqdm import tqdm
import argparse

import constant


def check_line(line):
    if (line == '# $eof\n'):
        return 0
    words = line.split(" ")
    line_type = words[0]
    
    try:
        if (line_type == 'Read'):
            return 1    # 1 for Read
        elif (line_type == 'Write'):
            return 2    # 2 for Write
        elif (line_type == 'INS'):
            return 3    # 3 for INS
        elif (line_type == '' or line_type[0] == '' or line_type[0] == '\t'):
            return -1
        else:
            print(line)
            print(line_type)
            assert(False)
    except:
        print(line_type)
        print(words)
        assert(False)


parser = argparse.ArgumentParser(description='Arguments')
parser.add_argument(
    '-n', '--num_ins',
    help='number of instructions to convert',
    type=int,
    nargs='?',
    const=100,         # Default value if -t is supplied
    default=100,     # Default value if -t is not supplied
    metavar='num_sim_lines')

args = parser.parse_args()

NUM_SIM_LINES = args.num_ins


LINE_START = 4635898
LINE_END = 4744237

LINE_START = 8281893
LINE_END = 8286976

LINE_START = 5309601 + 12 + 1
LINE_END = 6131247 - 1

#LINE_START = 9050809 + 12 + 1
#LINE_END = 9073095 - 1
arch = 'spr'
base_dir = '/home/geonhwajeong/sde-traces/%s/'%arch
file_name = '%s-32-32-32.txt'%arch
#file_name = 'skx-xgemm.txt'
full_path = base_dir + file_name
out_path = full_path.split('.')[0] + '-analysis.txt'

# find the line number for call ins_addr
# ex. ins_addr = 0x1234
def find_ins(ins_addr):
    line_nums = []
    file1 = open(full_path, 'r')
    lines = file1.readlines()
    
    for i in tqdm(range(len(lines))): 
        line_type = check_line(lines[i])
        if(line_type == 0):
            continue
        if(line_type == -1):
            continue
        
        if(line_type == 1): # Read 0 = *(UINT8*)0x00007ffda64d7bf3
            continue
        
        if(line_type == 2): # Write *(UINT64*)0x00007fcc8031ac60 = 0x107ff1a94b01b2
            continue    
        
        if(line_type == 3): # Update INS
            line = lines[i].split(" ")
            line = list(filter(lambda a: a != '', line))
            if(len(line) < 5):
                continue
            
            if((line[3] == 'call') and (line[4] == ins_addr)):
                line_nums.append(i)
                #print(line)
    file1.close()
    return line_nums

tick_nums = find_ins('0x434780')
print(tick_nums)

LINE_START = tick_nums[2] + 23
LINE_END = tick_nums[3]  - 1
    

def is_immediate(val):
    if(len(val) > 2):
        if(val[:2] == "0x"):
            return True
    
    return False

#*(UINT64*)0x00007fcc8031aee0\n
def get_data_size(data):
    assert(data[:6] == '*(UINT')
    size = data[6:].split('*')[0]
    return np.uint8(int(size)/8)

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
        


inst_counts = 0
op_counts = {}
ext_counts = {}


file1 = open(full_path, 'r')

print("Begin analyzing SDE Traces: " + full_path)

lines = file1.readlines()

lines = lines[LINE_START:LINE_END+1]
 
for i in tqdm(range(len(lines))): 
    line_type = check_line(lines[i])
    if(line_type == 0):
        continue
    if(line_type == -1):
        continue
    
    if(line_type == 1):     # Read 0 = *(UINT8*)0x00007ffda64d7bf3
        continue
    
    if(line_type == 2): # Write *(UINT64*)0x00007fcc8031ac60 = 0x107ff1a94b01b2
        continue    
    
    if(line_type == 3): # Update INS
        line = lines[i].split(" ")
        
        # ins_addr = np.uint64(int(line[1], 16))
        
        # dst register analysis
        # | r9 = 0x7fd00031b418, rflags = 0x206
        
        #ins_parts = list(filter(lambda a: a != '', ins_parts))
        
        # ['INS', '0x00007fcc8010e790', 'BASE', 'mov', 'rax,', 'qword', 'ptr', '[rdx+0x8]']
        
        line = list(filter(lambda a: a != '', line))
        #addr = line[1][2:]
        ext = line[2]
        
        if ext in ext_counts.keys():
            ext_counts[ext] += 1
        else:
            ext_counts[ext] = 1
        
        if (ext == 'AMX_BF16') or (ext == 'AMX_TILE'):
            print(ext)
            print(line)
            
        opcode = line[3]
        if(opcode[-1] == '\n'):
            opcode = opcode[:-1]
        if line[3] in constant.prefixes:
            opcode = opcode + ' ' + line[4]
        
        if opcode in op_counts.keys():
            op_counts[opcode] += 1
        else:
            op_counts[opcode] = 1
        
        inst_counts += 1

op_counts = sorted(op_counts.items(), key=lambda x: x[1], reverse=True)
ext_counts = sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)

print(ext_counts)
print(op_counts) 

out_file = open(out_path, 'w')
out_file.write(str(ext_counts) + '\n')      
out_file.write(str(op_counts))          
    

        
print("Total number of instructions: %d"%inst_counts)
print("Done analyzing trace")
print("Saved result at " + out_path)

assert(False)

# Using readlines() 
#file1 = open('sde-debugtrace-out.txt', 'r')

  
mem_rd_cnt = 0
mem_wt_cnt = 0
count = 0
ins = b''

reg_to_idx = {}
addr_to_xed = {}
addr_to_opcode = {}
# Read
# INS
# Write
# -> Trace
# Strips the newline character 

ready_to_push = False
inst_info = InstInfo()

file2 = open('./xsmm-files/spr-dis.txt', 'r')
lines = file2.readlines() 
for i in tqdm(range(len(lines))): 
    line = lines[i].split(' ')
    if(len(line) <= 1):
        continue
    
    if line[0] == 'XDIS':
        empty_idxs = []
        for i in range(len(line)):
            if(line[i] == ''):
                empty_idxs.append(i)
        cnt = 0
        for i in empty_idxs:
            del(line[ i- cnt])
            cnt+= 1
        addr = line[1][:-1]
        xed_cat = line[2]
        opcode = line[5]
        val = (xed_cat, opcode)
        addr_to_xed[addr] = val
        
file1 = open('./xsmm-files/spr-xgemm.txt', 'r')
lines = file1.readlines() 
for i in tqdm(range(len(lines))): 
    line_type = check_line(lines[i])
    if(line_type == 0):
        continue
    if(line_type == -1):
        #print('continued line')
        #print(lines[i])
        #line = lines[i]
        #assert(line[1:4] == 'XMM')
        continue
    
    if(line_type == 1):     # Read 0 = *(UINT8*)0x00007ffda64d7bf3
        continue
    
    if(line_type == 2): # Write *(UINT64*)0x00007fcc8031ac60 = 0x107ff1a94b01b2
        continue

    
    
    if(line_type == 3): # Update INS
        line = lines[i].split(" ")
        pruned_line = []
        is_opcode = True
        tmp_word = []
        
        inst_info.ins_addr = np.uint64(int(line[1], 16))
        
        # dst register analysis
        # | r9 = 0x7fd00031b418, rflags = 0x206
        reg_states = lines[i].split('|')
        assert(len(reg_states) < 3)
        dst_regs = []
        if(len(reg_states) == 2):
            reg_states = reg_states[1]
            reg_states = reg_states.replace(' ', '')
            reg_states = reg_states.split(',')
            
            if(len(reg_states[0]) > 9 and reg_states[0][:9] == "returning"):
                    continue
            inst_info.num_dest_regs = np.uint8(len(reg_states))
            for j in range(len(reg_states)):
                dst_reg = reg_states[j].split('=')[0]
                inst_info.dst[j] = np.uint8(constant.regs[dst_reg])
                dst_regs.append(dst_reg)
        
        ins_parts = lines[i].replace(',', '').split('|')[0]
        ins_parts = ins_parts.split(' ')
        ins_parts = list(filter(lambda a: a != '', ins_parts))
        if(ins_parts[-1][-1] == '\n'):
            ins_parts[-1] = ins_parts[-1][:-1]
        
        # ['INS', '0x00007fcc8010e790', 'BASE', 'mov', 'rax,', 'qword', 'ptr', '[rdx+0x8]']
        
        ins_parts = ins_parts[4:]

        line = list(filter(lambda a: a != '', line))
        addr = line[1][2:]
        for i in range(len(addr)):
            if addr[i] != '0':
                addr = addr[i:]
                break
        opcode = line[3]
        
        
        val = addr_to_xed[addr]
        
        assert(False)
    
        # Check whether dst_reg can only be at the first operand.
            
        #print(ins_parts)
        #print('src_regs: ' + str(src_regs))
        
        # parse pruned_line into opcode and arguments
        
        
        ''' All regs except dst regs should be src regs
        num_src_regs = np.uint8(1)
        src[0] = np.uint8(constant.regs[pruned_line[2][0]])
        '''
        # for memory access
        #if(pruned_line[0] == 'mov'):
        #    opcode = np.uint8(30)  

print("Done analyzing trace")

assert(False)


        
    
   
import gzip
with gzip.open('trace_0.raw', 'wb') as f:
    f.write(ins)

print("Complete conversion from SDE Trace to Macsim Trace")

print("Total num of ins: %d" % count)
print("Total memory read count: %d" % mem_rd_cnt)
print("Total memory write count: %d" % mem_wt_cnt)
