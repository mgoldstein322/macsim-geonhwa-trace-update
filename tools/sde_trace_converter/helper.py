from tqdm import tqdm
import numpy as np

def is_immediate(val):
    if(len(val) > 2):
        if(val[:2] == "0x"):
            return True
    
    return False

def starts_blank(val):
    if(val[0] == ' '  or val[0] == '\t'):
        return True;
    
    return False;

def remove_blank(val):
    print('remove blank')
    #print(val)
    i = 0
    while(val[i] == ' '  or val[i] == '\t'):
        i += 1
    
    return val.substr(i,len(val))

def read_header(val):
    val = val.split('\t')
    val = val[1]
    val = val.split(' ')
    val = val[0]
    val = val.split('[')
    target = val[0].lower()
    num_target_rows = int(val[1][:-1])
    num_target_cols = int(val[2][:-1])
    
    #print(target)
    #print(num_target_rows)
    #print(num_target_cols)
    
    return (target, num_target_rows, num_target_cols);

def get_num_zeros_bf16(val):
    num_zeros = 0

    for i in range(32):
        mask = np.uint64(3)
        if(not (val & mask)):
            num_zeros += 1
        mask = mask << np.uint64(2)

    return num_zeros

def read_row(val):
    zero_count = 0
    fst_line = val[0]
    snd_line = val[1]
    fst_line = fst_line.strip()
    fst_line = fst_line.split(']')[1].strip()
    snd_line = snd_line.strip()

    fst_line += " "
    fst_line += snd_line

    # replace 0 to 00000000 (4 bytes)
    fst_line = fst_line.split(" ")
    for i in range(len(fst_line)):
        if(fst_line[i] == "0"):
            fst_line[i] = "00000000"
        elif(len(fst_line[i]) == 4): # bd09 instead of 0000bd09
            fst_line[i] = "0000" + fst_line[i]

    #fst_line = fst_line.replace(" ", "")
    fst_line = "".join(fst_line)

    # the value will be 0 if the corresponding byte == 0
    byte_mask = []
    mask = np.uint64(0) 
    assert(len(fst_line) == 64 * 2)

    i = 0
    for _ in range(64):
        if(fst_line[i] == '0' and fst_line[i+1] == '0'):
            byte_mask.append(False)
            zero_count += 1
        else:
            byte_mask.append(True)
            mask = mask | np.uint64(1)
        if(i != 63*2):
            mask = mask << np.uint64(1)
        i += 2

    return (zero_count, byte_mask, mask);



# Check a line in the Intel SDE Trace and return the type
def check_line(line):
    if (line == '# $eof\n' or line == '# $eof'):
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
            #print(line)
            #print(line_type)
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