# For converting Intel SDE trace to MacSim trace
import gzip
import multiprocessing

import numpy as np
import argparse

from inst_info import InstInfo
from helper import *
import constant

# Command Example
# python3 parallel_convert.py -n 0 -i /home/geonhwajeong/sde-traces/spr/spr-32-32-32.txt

parser = argparse.ArgumentParser(description='Arguments')
parser.add_argument(
    '-n', '--num_ins',
    help='number of instructions to convert',
    type=int,
    nargs='?',
    const=100,         # Default value if -t is supplied
    default=100,     # Default value if -t is not supplied
    metavar='num_sim_lines')

parser.add_argument(
    '-i', '--input_file',
    help='absolute directory of the Intel SDE trace file',
    type=str,
    nargs='?',
    )

# /home/geonhwajeong/sde-traces/spr/spr-32-32-32.txt
args = parser.parse_args()

if(args.input_file == None):
    print('[ERROR] Please specify the input file path.')
    print('Take a look at the help messages.')
    print('python3 parallel_convert.py -h')
    exit(-1)

# Please change the followings!!!

NUM_SIM_LINES = args.num_ins
NUM_DIVS = 1

#ARCH = 'spr'
full_path = args.input_file
 
file_name = full_path.split('/')[-1]
base_dir = full_path[:-len(file_name)]
print(base_dir)
#base_dir = '/home/geonhwajeong/sde-traces/%s/'%ARCH
#file_name = '%s-32-32-32.txt'%ARCH
#file_name = 'skx-xgemm.txt'
#full_path = base_dir + file_name
out_path = full_path.split('.')[0] + '-trace_0.raw'

print('Converting Intel SDE Trace: %s'%(full_path))
print('The result will be saved at: %s'%(out_path))

print("Find the line numbers for time function")
tick_nums = find_ins(full_path, '0x434780')
print(tick_nums)

LINE_START = tick_nums[2] + 23
LINE_END = tick_nums[3]  - 1

print("Begin conversion from SDE Trace to Macsim Trace")
print("from line # %d to %d"%(LINE_START, LINE_END))

# Read
# INS
# Write
# -> Trace
# Strips the newline character 

inst_info = InstInfo()
file1 = open(full_path, 'r')
lines = file1.readlines() 
lines = lines[LINE_START:LINE_END+1]
print('Check the first line\n %s'%(lines[0]))

# Now find array for division
# n_0, n_1, ... , n_8
# 0~n_0-1, n_0~n_1 -1 ... , n_8 ~ last
div_points = [0]

# we need num_divs - 1 points
for i in range(NUM_DIVS-1):
    start_candidate = int((i+1) * len(lines) / NUM_DIVS)
    #print(int(start_candidate))
    while(True):
        #print(str(start_candidate) + ": " + str(check_line(lines[start_candidate])) + "," + str(check_line(lines[start_candidate+1]) ))
        if((check_line(lines[start_candidate]) == 3) and (check_line(lines[start_candidate+1]) == 3)):
            div_points.append(start_candidate+1)
            break
        elif((check_line(lines[start_candidate]) == 2) and (check_line(lines[start_candidate+1]) == 3)):
            div_points.append(start_candidate+1)
            break
        else:
            start_candidate += 1
div_points.append(len(lines))
print(div_points)

file1.close()
#######

def process_data(thread_id, file_name, idx_range):
    file1 = open(base_dir + file_name, 'r')
    
    lines = file1.readlines() 
    lines = lines[LINE_START:LINE_END+1]
    lines = lines[idx_range[0]:idx_range[1]]
    
    mem_rd_cnt = 0
    mem_wt_cnt = 0
    count = 0
    count_ins = 0
    ins = b''

    print("thread %d is reponsible from %d to %d"%(thread_id, idx_range[0], idx_range[1]))
    # Read
    # INS
    # Write
    # -> Trace
    # Strips the newline character 

    ready_to_push = False
    inst_info = InstInfo()
    print("# of lines: %d"%len(lines))
    for i in range(len(lines)):
        if(i % int(len(lines)/10) == 0):
            print('thread %d processed %d %% lines'%(thread_id, int(i/int(len(lines)/10)*10))) 
        line_type = check_line(lines[i])
        if(line_type == 0):
            continue
        if(line_type == -1):
            continue
            #print('continued line')
            #print(lines[i])
            #line = lines[i]
            #assert(line[1:4] == 'XMM')
        # First check whether it is ready to push ins
        if((line_type == 1) or (line_type == 3)):
            if(ready_to_push):
                # ? bool B uint8 Q uint64
                
                #print(struct.calcsize('BBBBBBBBBBBBBBBBBB?B???BBQQQQQBB??'))
                #x = struct.unpack('BBBBBBBBBBBBBBBBBB?B???BBQQQQQBB??', info)
                #print(hex(ins_addr) + " " + hex(ld_vaddr1))
                ins += inst_info.get_macsim_ins()
                count += 1
                if(NUM_SIM_LINES != 0):
                    if(count == NUM_SIM_LINES):
                        break
                    
                inst_info.init_ins()
                #print(hex(ld_vaddr1))
                ready_to_push = False
        
        if(line_type == 1):     # Read 0 = *(UINT8*)0x00007ffda64d7bf3
            line = lines[i].split(" ")
            assert(line[0] == 'Read')
            
            while(len(lines[i].split('=')) == 1): # This means this line doesn't have address
                i += 1
                #           00000003_8031c0a0_ffffffff_ffffffff = *(UINT19456*)0x00007ffc8322ca40
            read_addr = lines[i].replace(' ', '').split("=")[1] 
            
            #print(read_addr)
            assert(read_addr[:6] == '*(UINT')
            #assert(line[3][:11] == '*(UINT128*)'
            #        or line[3][:10] == '*(UINT64*)' or line[3][:10] == '*(UINT32*)'
            #        or line[3][:10] == '*(UINT16*)' or line[3][:9] == '*(UINT8*)')
            
            # TODO Fix here
            num = int(read_addr.split(')')[1], 16)
            
            if(inst_info.num_ld == 0):
                inst_info.ld_vaddr1 = np.uint64(num)
                
                size = get_data_size(read_addr)
                
                inst_info.mem_read_size += size
                
            elif(inst_info.num_ld == 1):
                inst_info.ld_vaddr2 = np.uint64(num)
                size = get_data_size(read_addr)
                inst_info.mem_read_size += size
            
            else:
                #print(i)
                #print(line)
                #print(inst_info.num_ld)
                size = get_data_size(read_addr)
                inst_info.mem_read_size += size
                if(int(inst_info.mem_read_size) + int(size) > 255):
                    #print('Check here')
                    inst_info.mem_read_size = 255
                # TODO
                # We need to fix here.
                # tileload loads 16*512 bytes to tmm register.
                #raise NotImplementedError

            inst_info.num_ld = inst_info.num_ld + np.uint8(1)

            mem_rd_cnt += 1
            
            if(i == len(lines)-1):
                assert(False)
        
        if(line_type == 2): # Write *(UINT64*)0x00007fcc8031ac60 = 0x107ff1a94b01b2
            line = lines[i].split(" ")
            assert(line[0] == 'Write')
            addr = int(line[1].split(')')[1], 16)
            inst_info.has_st = bool(True)
            inst_info.st_vaddr = addr
            inst_info.mem_write_size = get_data_size(line[1])
            
            mem_wt_cnt += 1
            
            if(i == len(lines)-1):
                assert(ready_to_push)

                ins += inst_info.get_macsim_ins()
                count += 1
                if(NUM_SIM_LINES != 0):
                    if(count == NUM_SIM_LINES):
                        break
                    
                inst_info.init_ins()
                ready_to_push = False
        
        if(line_type == 3): # Update INS
            count_ins += 1
            #print(lines[i])

            if(ready_to_push):
                assert(False)
            line = lines[i].split(" ")
            
            pruned_line = []
            is_opcode = True
            tmp_word = []
            
            inst_info.ins_addr = np.uint64(int(line[1], 16))
            
            # dst register analysis
            # | r9 = 0x7fd00031b418, rflags = 0x206
            # TODO TMM/YMM register writes are now shown after |
            # instead, they are in the next line
            reg_states = lines[i].split('|')
            assert(len(reg_states) < 3)
            dst_regs = []
            if(len(reg_states) == 2):
                reg_states = reg_states[1]
                reg_states = reg_states.replace(' ', '')
                reg_states = reg_states.split(',')
                
                if(len(reg_states[0]) > 9 and reg_states[0][:9] == "returning"):
                    pass
                else:
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
            
            if(ins_parts[3] == 'tileloadd'):
                # print('tileloadd')
                inst_info.mem_read_size = np.uint8(64)
                # This instruction will generate 16 uops, and each uop will load 64 bytes.
                inst_info.num_ld = 1
                # STRINGOP
                # inst_info.opcode = np.uint8(76)
                inst_info.opcode = np.uint8(106) # For AMX_TILE_MEM
                #inst_info.ld_vaddr1 = np.uint64(num)                
                inst_info.ld_vaddr2 = np.uint64(0)
            
            
            tmp_parts = ins_parts
            if(ins_parts[3] in constant.prefixes):
                ins_parts = ins_parts[5:]
            else:
                ins_parts = ins_parts[4:]

            src_regs = []
            for part in ins_parts:
                if(len(part.split(":")) > 1):
                    part = part.split(":")[1]
                if(len(part) > 2 and part[0] == '[' and part[-1] == ']'):
                    #[rcx+rax*4+0x12]
                    part = part[1:-1]
                    part = part.replace('-', '+').replace('*', '+')
                    part = part.split('+')
                    for sub_part in part:
                        if(sub_part in constant.word_constants or (len(sub_part)>=2 and sub_part[:2] == '0x')):
                            continue
                        elif(not sub_part in constant.regs.keys()):
                            print(ins_parts)
                            print(part)
                            print("2New register: " + sub_part)
                            assert(False)
                        elif(sub_part in constant.regs.keys() and (not sub_part in src_regs)):
                            src_regs.append(sub_part)
                else:
                    # TODO Ignore this [rsp+0x18]{1to16}
                    if(len(part) > 2 and part[0] == '[' and part[-1] == '}'):
                        pass
                    elif(len(part.split('{')) >= 2):
                        #zmm0{k6}
                        pass
                    elif(part in constant.word_constants or (len(part)>=2 and part[:2] == '0x')):
                        pass
                    elif(part.isdigit()):
                        pass
                    
                    elif(not part in constant.regs.keys()):
                        print(tmp_parts)
                        print(ins_parts)
                        print(part)
                        print("New register: " + part)
                        assert(False)
                    elif(part in constant.regs.keys() and (not part in dst_regs) and (not part in src_regs)):
                        src_regs.append(part)
                        
            # TODO Update for tmm registers
            inst_info.num_src_regs = np.uint8(len(src_regs))
            for j in range(len(src_regs)):
                inst_info.dst[j] = np.uint8(constant.regs[src_regs[j]])
            
            ready_to_push = True
            if(i == len(lines)-1):
                assert(ready_to_push)

                ins += inst_info.get_macsim_ins()
                count += 1
                if(NUM_SIM_LINES != 0):
                    if(count == NUM_SIM_LINES):
                        break
                    
                inst_info.init_ins()
                ready_to_push = False

    outfile_name = str(thread_id) + '_' + file_name
    with open(base_dir + outfile_name, 'wb') as out_file:
        out_file.write(ins)

    print("Complete conversion from SDE Trace to Macsim Trace")

    print("Total num of ins: %d %d" % (count, count_ins))
    print("Total memory read count: %d" % mem_rd_cnt)
    print("Total memory write count: %d" % mem_wt_cnt)


processes = []
# Create new processes
for i in range(NUM_DIVS):
    if(True):
        process = multiprocessing.Process(target=process_data, args=(i, file_name, (div_points[i], div_points[i+1])))
        processes.append(process)
        process.start()

for p in processes:
   p.join()

# Merge the generated results
print("Now merge the results from %d process(es)"%(NUM_DIVS))
ins = b''
for i in range(NUM_DIVS):
    tmp_file_name = str(i) + '_' + file_name
    with open(base_dir + tmp_file_name, 'rb') as tmp_file:
        lines = tmp_file.read()
        ins += lines
        
with gzip.open(out_path, 'wb') as f:
    f.write(ins)
    
print("Done conversion for %d instructions"%(len(ins)/80))
