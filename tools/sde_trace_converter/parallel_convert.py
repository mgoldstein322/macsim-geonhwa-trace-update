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

parser.add_argument(
    '-t', '--num_threads',
    help='num_threads',
    type=int,
    nargs='?',
    const=1,
    default=1,
    metavar='num_threads',
    )

# /home/geonhwajeong/sde-traces/spr/spr-32-32-32.txt
args = parser.parse_args()

if(args.input_file == None):
    print('[ERROR] Please specify the input file path.')
    print('Take a look at the help messages.')
    print('python3 parallel_convert.py -h')
    exit(-1)

# Please change the followings!!!

OPCODE_AMX_TILE_MEM = 105
OPCODE_AMX_TILE_COMPUTE_BF16 = 106

NUM_SIM_LINES = args.num_ins
NUM_DIVS = args.num_threads

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

use_time_tick = False
if use_time_tick:
    print("Find the line numbers for time function")
    tick_nums = find_ins(full_path, '0x434780')
    print(tick_nums)

    LINE_START = tick_nums[2] + 23
    LINE_END = tick_nums[3]  - 1

print("Begin conversion from SDE Trace to Macsim Trace")
if use_time_tick:
    print("from line # %d to %d"%(LINE_START, LINE_END))

# Read
# INS
# Write
# -> Trace
# Strips the newline character 

inst_info = InstInfo()
file1 = open(full_path, 'r')
lines = file1.readlines() 
if use_time_tick:
    lines = lines[LINE_START:LINE_END+1]
print('Check the first line\n %s'%(lines[0]))

# Now find array for division
# n_0, n_1, ... , n_8
# 0~n_0-1, n_0~n_1 -1 ... , n_8 ~ last
div_points = [0]
MANUAL = False
if MANUAL:
    div_points = [0, 5115177]
if MANUAL is False:
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
    div_points.append(len(lines)-1)
print(div_points)

file1.close()
lines = None
#######


def process_data(thread_id, file_name, idx_range):
    file1 = open(base_dir + file_name, 'r')
    if(thread_id != 0):
        for i, line in enumerate(file1):
            if i == idx_range[0]-1:
                break
    num_read_lines = idx_range[1]-idx_range[0]+1
    print("thread %d is reponsible from %d to %d"%(thread_id, idx_range[0], idx_range[1]))
    tot_zero_count = 0

    mem_rd_cnt = 0
    mem_wt_cnt = 0
    count = 0
    count_ins = 0
    ins = b''
    ready_to_push = False
    inst_info = InstInfo()
    cur_ins = ''

    pattern_state = 0
    pattern_ins = []
    for i in range(5):
        pattern_ins.append(InstInfo())
    pattern_success = 0
    pattern_fail = 0

    reading_lines = False
    block_size = 512*1024*1024
    read_block_count = 0
    num_blocks = num_read_lines/block_size
    num_lines = 0
    done_read=False

    tot_tdpbf16_count = 0
    tot_num_elements = 0
    tot_zero_elements = 0

    tmm_byte_mask = [[], [], [], [], [], [], [], []]
    while done_read is False:
        if(num_lines % ((num_read_lines)/10) == 0):
                print('thread %d processed %d %% lines'%(thread_id,
                int(num_lines/int((num_read_lines/10))*10)))
        read_block_count+=1
        lines = None

        lines = file1.readlines(block_size)
        print(len(lines))
        print(num_read_lines)
        if(len(lines) >= num_read_lines):
            lines = lines[:num_read_lines]
            done_read = True
        else:
            while(check_line(lines[len(lines)-1]) != 3):
                if(check_line(lines[len(lines)-1]) == 0):
                    print("last line")
                    break
                new_line = file1.readline()
                print(new_line)
                lines.append(new_line)
            
        num_lines += len(lines)

        if not lines:
            break
        #lines = file1.readlines() 
        #if use_time_tick:
        #    lines = lines[LINE_START:LINE_END+1]
        #lines = lines[idx_range[0]:idx_range[1]]


        # Read
        # INS
        # Write
        # -> Trace
        # Strips the newline character 

        
        
        # TODO: Update dividing into tasks to not choose tdpbf16ps or tileload as dividing point
        # pattern matching
        

        print("tid %d: # of lines: %d"%(thread_id,len(lines)))
        cur_percentage = int(0)
        unit = len(lines) / 10
        unit = int(unit)
        for i in range(len(lines)):
            if(i > int(cur_percentage * unit)):
                print('thread %d processed %d %% lines'%(thread_id,
                cur_percentage*10))
                cur_percentage += 1
            if(reading_lines):
                line_type = 1
            else:
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
                start_pattern_state = pattern_state
                if(ready_to_push):
                    if(cur_ins == 'tileloadd'):
                        #print(inst_info.src)
                        #print(inst_info.dst)
                        assert(inst_info.num_dest_regs == 1)
                        if(pattern_state == 1):
                            pattern_ins[1].copy_ins(inst_info)
                            pattern_ins[1].ins_addr = inst_info.ins_addr
                            inst_info.init_ins()
                            pattern_state += 1
                            #for ii in range(pattern_state):
                            #    print(pattern_ins[ii].src)
                        
                        if(pattern_state == 3):
                            pattern_ins[3].copy_ins(inst_info)
                            pattern_ins[3].ins_addr = inst_info.ins_addr
                            inst_info.init_ins()
                            pattern_state += 1
                            #for ii in range(pattern_state):
                            #    print(pattern_ins[ii].src)

                    if(cur_ins == 'tdpbf16ps'):
                        assert(inst_info.num_read_regs == 3)
                        assert(inst_info.num_dest_regs == 1)
                        #dst_reg = reg_states[j].split('=')[0]
                        #inst_info.dst[j] = np.uint8(constant.regs[dst_reg])
                        #dst_regs.append(dst_reg)
                        if(pattern_state == 0):
                            pattern_ins[0].copy_ins(inst_info)
                            pattern_ins[0].ins_addr = inst_info.ins_addr
                            inst_info.init_ins()
                            pattern_state += 1

                        if(pattern_state == 2):
                            pattern_ins[2].copy_ins(inst_info)
                            pattern_ins[2].ins_addr = inst_info.ins_addr
                            inst_info.init_ins()
                            pattern_state += 1


                        if(pattern_state == 4):
                            pattern_ins[4].copy_ins(inst_info)
                            pattern_ins[4].ins_addr = inst_info.ins_addr
                            inst_info.init_ins()
                            pattern_state += 1


                        '''
                        if we identify this, 
                        66 72 70 / 66
                        68 72 71 / 68
                        67 73 70 / 67
                        69 73 71 / 69

                        0 tdpbf16ps tmm0, tmm6, tmm4 \\
                        1 tileloadd tmm5 BTile1 \\
                        2 tdpbf16ps tmm2, tmm6, tmm5 \\
                        3 tileloadd tmm7 ATile1 \\
                        4 tdpbf16ps tmm1, tmm7, tmm4 \\
                        5 tdpbf16ps tmm3, tmm7, tmm5 \\
                        
                        Swap [2-3] with [4-5]
                        70
                        72
                        71
                        73
                        70
                        72
                        '''
                        

                    if(cur_ins == 'tilestored'):
                        #TODO FIX HERE
                        #assert(inst_info.num_st == 16)
                        #assert(inst_info.mem_write_size == 255)
                        inst_info.mem_write_size = np.uint8(64)
                        # This instruction will generate 16 uops, and each uop will load 64 bytes.
                        inst_info.num_st = 1
                        # STRINGOP
                        # inst_info.opcode = np.uint8(76)
                        inst_info.opcode = np.uint8(OPCODE_AMX_TILE_MEM) # For AMX_TILE_MEM
                        
                        
                        stride = inst_info.st_vaddr2 - inst_info.st_vaddr
                        #print('tilestored addr with %x, stride %d'%(inst_info.st_vaddr, stride))
                        
                        #inst_info.ld_vaddr1 = np.uint64(num)                
                        inst_info.ld_vaddr2 = np.uint64(stride)
                    
                    # ? bool B uint8 Q uint64
                    
                    #print(struct.calcsize('BBBBBBBBBBBBBBBBBB?B???BBQQQQQBB??'))
                    #x = struct.unpack('BBBBBBBBBBBBBBBBBB?B???BBQQQQQBB??', info)
                    #print(hex(ins_addr) + " " + hex(ld_vaddr1))
                    if(pattern_state == 0):
                        ins += inst_info.get_macsim_ins()
                        count += 1
                        if(NUM_SIM_LINES != 0):
                            if(count == NUM_SIM_LINES):
                                break
                        inst_info.init_ins()

                    else:
                        if(start_pattern_state == pattern_state):
                            # 1. pattern_ins[0:pattern state] update
                            for ii in range(pattern_state):
                                ins += pattern_ins[ii].get_macsim_ins()
                                count += 1
                                if(NUM_SIM_LINES != 0):
                                    if(count == NUM_SIM_LINES):
                                        break
                                pattern_ins[ii].init_ins()

                            # 2. cur state update
                            ins += inst_info.get_macsim_ins()
                            count += 1
                            if(NUM_SIM_LINES != 0):
                                if(count == NUM_SIM_LINES):
                                    break
                            inst_info.init_ins()
                            pattern_state = 0
                            pattern_fail +=1 
                        elif (pattern_state == 5):
                            tmp = InstInfo()
                            tmp.copy_ins(pattern_ins[3])
                            pattern_ins[3].copy_ins(pattern_ins[1])
                            pattern_ins[1].copy_ins(tmp)

                            tmp.copy_ins(pattern_ins[4])
                            pattern_ins[4].copy_ins(pattern_ins[2])
                            pattern_ins[2].copy_ins(tmp)

                            # 1. pattern_ins[0:pattern state] update
                            for ii in range(pattern_state):
                                ins += pattern_ins[ii].get_macsim_ins()
                                count += 1
                                if(NUM_SIM_LINES != 0):
                                    if(count == NUM_SIM_LINES):
                                        break
                                pattern_ins[ii].init_ins()
                            
                            pattern_success +=1 
                            pattern_state = 0
                        else:
                            pass
                    
                    ready_to_push = False
            
            if(line_type == 1):     # Read 0 = *(UINT8*)0x00007ffda64d7bf3
                if(reading_lines == False):
                    line = lines[i].split(" ")
                    assert(line[0] == 'Read')
                reading_lines = False
                while(len(lines[i].split('=')) == 1): # This means this line doesn't have address
                    i += 1
                    if(i == len(lines)):
                        reading_lines = True
                        break
                
                if(reading_lines):
                    continue
                    #           00000003_8031c0a0_ffffffff_ffffffff = *(UINT19456*)0x00007ffc8322ca40
                read_addr = lines[i].replace(' ', '').split("=")[1] 
                
                assert(read_addr[:6] == '*(UINT')
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
                    
                    # Check for overflow
                    if(int(inst_info.mem_read_size) + int(size) > 255):
                        #print('Check here')
                        inst_info.mem_read_size = np.uint8(255)
                    else:
                        inst_info.mem_read_size += size
                    # TODO
                    # We need to fix here.
                    # tileload loads 16*512 bytes to tmm register.
                    #raise NotImplementedError

                inst_info.num_ld = inst_info.num_ld + np.uint8(1)

                mem_rd_cnt += 1
                
                #if(i == len(lines)-1):
                #    assert(False)
            
            if(line_type == 2): # Write *(UINT64*)0x00007fcc8031ac60 = 0x107ff1a94b01b2
                line = lines[i].split(" ")
                assert(line[0] == 'Write')
                addr = int(line[1].split(')')[1], 16)

                if(inst_info.has_st is True):
                    size = get_data_size(line[1])
                    # Check for overflow
                    if(int(inst_info.mem_write_size) + int(size) > 255):
                        #print('Check here')
                        inst_info.mem_write_size = np.uint8(255)
                    else:
                        inst_info.mem_write_size += np.uint8(size)
                    
                    if(inst_info.num_st == 1):
                        inst_info.st_vaddr2 = addr
                    
                    inst_info.num_st += np.uint8(1)
                    
                else:
                    inst_info.has_st = bool(True)
                    inst_info.st_vaddr = addr
                    inst_info.mem_write_size = get_data_size(line[1])
                    inst_info.num_st = np.uint8(1)
                
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
                
                cur_ins = ins_parts[3]
                
                if(cur_ins == 'tileloadd'):
                    #print(inst_info.num_ld)
                    #TODO FIX HERE
                    #assert(inst_info.num_ld == 16)
                    #assert(inst_info.mem_read_size == 255)
                    inst_info.mem_read_size = np.uint8(64)
                    # This instruction will generate 16 uops, and each uop will load 64 bytes.
                    inst_info.num_ld = 1
                    # STRINGOP
                    # inst_info.opcode = np.uint8(76)
                    inst_info.opcode = np.uint8(OPCODE_AMX_TILE_MEM) # For AMX_TILE_MEM
                    
                    stride = inst_info.ld_vaddr2 - inst_info.ld_vaddr1
                    #print('tileload addr with %x, stride %d'%(inst_info.ld_vaddr1, stride))                
                    inst_info.ld_vaddr2 = np.uint64(stride)
                
                if(cur_ins == 'tdpbf16ps'):
                    inst_info.opcode = np.uint8(OPCODE_AMX_TILE_COMPUTE_BF16) # For AMX_TILE_MEM
                    #print('Detect tdpbf16ps')
                    # TODO Set src/dst registers
                
                tmp_parts = ins_parts
                if(ins_parts[3] in constant.prefixes):
                    ins_parts = ins_parts[5:]
                else:
                    ins_parts = ins_parts[4:]

                # Set dest regs for tdpbf16ps
                if(cur_ins == 'tdpbf16ps'):
                    #print(ins_parts)
                    assert(len(ins_parts) == 3)
                    dst_reg = ins_parts[0]
                    inst_info.dst[0] = np.uint8(constant.regs[dst_reg])
                    dst_regs.append(dst_reg)
                    inst_info.num_dest_regs = np.uint8(len(dst_regs))

                # Set dest regs for tileloadd
                if(cur_ins == 'tileloadd'):
                    assert(len(ins_parts) == 3)                
                    dst_reg = ins_parts[0]
                    inst_info.dst[0] = np.uint8(constant.regs[dst_reg])
                    dst_regs.append(dst_reg)
                    inst_info.num_dest_regs = np.uint8(len(dst_regs))


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
                        
                        elif(part in constant.regs.keys() and (not part in src_regs)):
                            # tdpbf16ps tmm0, tmm1, tmm2 -> tmm0 is both read and written

                            if(cur_ins == 'tdpbf16ps'):
                                src_regs.append(part)
                            else:
                                if(not part in dst_regs):
                                    src_regs.append(part)

                # TODO Update for tmm registers
                inst_info.num_read_regs = np.uint8(len(src_regs))
                for j in range(len(src_regs)):
                    inst_info.src[j] = np.uint8(constant.regs[src_regs[j]])

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

                # read tmm register values
                if(cur_ins == 'tdpbf16ps' or cur_ins == 'tileloadd' or cur_ins == 'tilezero'):
                    if(cur_ins == 'tdpbf16ps'):
                        #print(src_regs) # ex) tmm1, tmm2, tmm3
                        for src_idx in range(len(src_regs)):
                            inst_info.src_bitmask[src_idx] = tmm_byte_mask[int(src_regs[src_idx][3])]

                            # calculate sparsity in the operands for BF16
                            assert(len(inst_info.src_bitmask[src_idx]) == 16)
                            if(src_idx == 1): # skip the first one since it's output
                                tot_num_elements += 16*32
                                for row in inst_info.src_bitmask[src_idx]: # row is np.uint64
                                    tot_zero_elements += get_num_zeros_bf16(row);

                
                    i += 1
                    target = None
                    target_val = []
                    num_target_rows = 0
                    num_target_cols = 0
                    #print(lines[i])

                    (target, num_target_rows, num_target_cols) = read_header(lines[i]);
                    i += 1

                    while(starts_blank(lines[i])):
                        (zero_count, row, mask) = read_row(lines[i:i+2])
                        tot_zero_count += zero_count
                        target_val.append(mask);
                        #print(row)
                        #print(mask)
                        i += 2

                    while(len(target_val) < 16):
                        target_val.append(np.uint64(0))

                    '''
                    if(cur_ins == 'tdpbf16ps'):
                        print('tdpbf16ps')
                    if(cur_ins == 'tilezero'):
                        print('tilezero')
                    if(cur_ins == 'tileloadd'):
                        print('tileloadd')
                    '''
                    #print(int(target[3]))
                    tmm_byte_mask[int(target[3])] = target_val

                    #print("target val size {}".format(len(target_val)))
                    #print("target val row size {}".format(len(target_val[0])))

                    i -= 1;
                    if(cur_ins == 'tdpbf16ps'):
                        for dst_idx in range(len(dst_regs)):
                            inst_info.dst_bitmask[dst_idx] = tmm_byte_mask[int(dst_regs[dst_idx][3])]
                    
                        #print(dst_regs) # ex) tmm1
                        tot_tdpbf16_count += 1

                

    outfile_name = str(thread_id) + '_' + file_name
    with open(base_dir + outfile_name, 'wb') as out_file:
        out_file.write(ins)

    print("tid:%d Complete conversion from SDE Trace to Macsim Trace"%(thread_id))

    print("Total num of ins: %d %d" % (count, count_ins))
    print("Total memory read count: %d" % mem_rd_cnt)
    print("Total memory write count: %d" % mem_wt_cnt)
    print("Num pattern success: %d" % pattern_success)
    print("Num pattern fail: %d" % pattern_fail)

    print("Total zero count: %d" % tot_zero_count)

    print("tot_tdpbf16_count: %d" % tot_tdpbf16_count)
    print("tot_zero_elements: %d" % tot_zero_elements)
    print("tot_num_elements: %d" % tot_num_elements)
    sparsity = tot_zero_elements / tot_num_elements
    print("Sparsity in operands: %f" % sparsity)

# Create new processes
processes = []
for i in range(NUM_DIVS):
    if True:
    #if(i in {11}):
        process = multiprocessing.Process(target=process_data, args=(i, file_name, (div_points[i], div_points[i+1])))
        processes.append(process)
        process.start()

for p in processes:
    p.join()

'''
processes = []
for i in range(NUM_DIVS):
    if i>=NUM_DIVS/folds:
    #if(i in {11}):
        process = multiprocessing.Process(target=process_data, args=(i, file_name, (div_points[i], div_points[i+1])))
        processes.append(process)
        process.start()

for p in processes:
   p.join()
'''
# Merge the generated results
print("Now merge the results from %d process(es)"%(NUM_DIVS))
ins = b''
for i in range(NUM_DIVS):
    #if i != 11:
    #    continue
    tmp_file_name = str(i) + '_' + file_name
    with open(base_dir + tmp_file_name, 'rb') as tmp_file:
        lines = tmp_file.read()
        ins += lines
        
with gzip.open(out_path, 'wb') as f:
    f.write(ins)
    
print("Done conversion for %d instructions"%(len(ins)/(80+ 3*8*16))) 
