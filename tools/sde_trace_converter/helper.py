from tqdm import tqdm
import numpy as np

def is_immediate(val):
    if(len(val) > 2):
        if(val[:2] == "0x"):
            return True
    
    return False

# Check a line in the Intel SDE Trace and return the type
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

# find the line number for call ins_addr
# ex. ins_addr = 0x1234
def find_ins(full_path, ins_addr):
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

#*(UINT64*)0x00007fcc8031aee0\n
def get_data_size(data):
    assert(data[:6] == '*(UINT')
    size = data[6:].split('*')[0]
    return np.uint8(int(size)/8)

def remove_blank(in_list):
    return list(filter(lambda a: a != '', in_list))