import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import io
import base64
import reedsolo
import sys

def generate_error_corrected_codewords(data_bytes, ecc_codewords):
    rs = reedsolo.RSCodec(ecc_codewords)
    encoded_data = rs.encode(bytes(data_bytes))  # returns data + ecc
    ecc = encoded_data[-ecc_codewords:]          # extract only ECC portion
    full = data_bytes + list(ecc)                # combine data + ecc
    corrected_bits = ''.join(format(byte, '08b') for byte in full)  # convert to bit string
    return corrected_bits

def build_qr_payload(data_bytes, ecc_level='L', V=1):
    bits = '0100'  # byte mode
    bits += format(len(data_bytes), '08b')  # character count

    for byte in data_bytes:
        bits += format(byte, '08b')  # data bits assembly

    bits += '0000'  # terminator if room / padding

    while len(bits) % 8 != 0:
        bits += '0'

    # Pad with alternating bytes to reach 152 bits
    pad_bytes = ['11101100', '00010001']
    print(bits)

    def check_len():
        print("len = ", len(bits), " | vlen = ", vlen)
        if len(bits) > vlen:
            return True
        else:
            return False
        
    vlen = 152
    ecc_table = {
        (1, 'L'): 152, (1, 'M'): 128, (1, 'Q'): 104, (1, 'H'): 72,
        (2, 'L'): 272, (2, 'M'): 224, (2, 'Q'): 176, (2, 'H'): 128,
        # Add more versions if needed
    }
    ecc_order = ['H', 'Q', 'M', 'L']
    vlen = ecc_table.get((V, ecc_level))
    version_limit = 2
    while True:
        if check_len() == False:
            break
        index = ecc_order.index(ecc_level)
        print('V = ', V, ' | ECC_level = ', ecc_level, " | vlen = ", vlen, " | ", "length of bits = ", len(bits))
        V += 1
        print(V)
        if V > version_limit:
            V -= 1
            print("Cannot go up a version so lowering ecc rate")
            vlen = ecc_table.get((V, ecc_level))
            if index < len(ecc_order) - 1:
                ecc_level = ecc_order[index + 1]  # go down one level
                vlen = ecc_table.get((V, ecc_level))
                print('lowering ecc_level to ', ecc_level)
            else:
                print("Cannot lower ecc rate nor version level")
                break
        vlen = ecc_table.get((V, ecc_level))

    print('end', 'V = ', V, ' | ECC_level = ', ecc_level, " | vlen = ", vlen, " | ", "length of bits = ", len(bits))

    i = 0
    if V == 1:
        while len(bits) < vlen:
            bits += pad_bytes[i % 2]
            i += 1
    elif V == 2:
        while len(bits) < vlen:
            bits += pad_bytes[i % 2]
            i += 1

    data_codewords = [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)] # splits bytes
    print("after padding", bits)
    return data_codewords, V, ecc_level

def generate_grid(size=21):
    grid = [[0] * size for _ in range(size)]

    def place_finder_pattern(x, y):
        pattern = [
            [1,1,1,1,1,1,1],
            [1,0,0,0,0,0,1],
            [1,0,1,1,1,0,1],
            [1,0,1,1,1,0,1],
            [1,0,1,1,1,0,1],
            [1,0,0,0,0,0,1],
            [1,1,1,1,1,1,1],
        ]
        for i in range(7):
            for j in range(7):
                grid[y+i][x+j] = pattern[i][j]

    place_finder_pattern(0, 0)
    if size == 21:
        place_finder_pattern(14, 0)
        place_finder_pattern(0, 14)
    if size > 21:
        place_finder_pattern(18, 0)
        place_finder_pattern(0, 18)

    return grid

def add_timing_patterns(grid):
    size = len(grid)
    for i in range(7, size - 7):
        if (i % 2 == 0):
            grid[6][i] = 1
            grid[i][6] = 1

def add_alignment_patterns(grid):
    size = len(grid)
    pattern = [
        [1,1,1,1,1],
        [1,0,0,0,1],
        [1,0,1,0,1],
        [1,0,0,0,1],
        [1,1,1,1,1]
    ]
    x = size-7-2
    y = size-7-2
    for i in range(5):
        for j in range(5):
            grid[x+i][j+y] = pattern[i][j]

def add_dark_module(grid):
    size = len(grid)
    grid[size-8][8] = 1
    # if size == 21:
    #     grid[size-8][8] = 1
    # elif size > 21:
    #     grid[17][8] = 1

def is_reserved(r, c, size=21):
    if (r < 9 and c < 9) or (r < 9 and c >= size - 8) or (r >= size - 8 and c < 9):
        return True  # Finder patterns
    if c == 6 or r == 6:
        return True  # Timing patterns
    if (r, c) == (size-8, 8):
        return True  # Dark module
    if size>21:
        if (r > size-7-3 and r < size-4) and (c > size-7-3 and c < size-4):
            return True
    if logo and size>21:
        if (r < size-10 and r > 10 and c > 10 and c < size-10):
            return True
    return False

def add_data(grid, data):
    size = len(grid)
    direction = -1
    col = size - 1
    bit_index = 0

    while col > 0:
        if col == 6:
            col -= 1

        for i in range(size):
            row = (size - 1 - i) if direction == -1 else i
            for offset in [0, -1]:
                c = col + offset
                if is_reserved(row, c, size):
                    if logo and is_reserved(row, c, size) == 2:
                        grid[row][c] = is_reserved(row, c, size)
                    continue
                if bit_index < len(data):
                    grid[row][c] = int(data[bit_index])
                    bit_index += 1

        col -= 2
        direction *= -1

    return grid

def penalty_1(grid):
    size = len(grid)
    curr_count = 0
    penalty_score = 0
    for r in range(size):
        for c in range(size):
            if (is_reserved(r, c, size)):
                continue
            if (grid[r][c] == 1):
                curr_count += 1
                if (curr_count > 5):
                    penalty_score += 1
            else:
                curr_count = 0
            if (curr_count == 5):
                penalty_score += 3
    return penalty_score

def penalty_2(grid):
    size = len(grid)
    penalty_score = 0
    for r in range(size - 1):
        for c in range(size - 1):
            # Check if any of the 4 cells in the 2x2 block are reserved
            if (is_reserved(r, c, size) or
                is_reserved(r, c + 1, size) or
                is_reserved(r + 1, c, size) or
                is_reserved(r + 1, c + 1, size)):
                continue
            # Check if all 4 cells in the 2x2 block are the same
            if (grid[r][c] == grid[r][c + 1] ==
                grid[r + 1][c] == grid[r + 1][c + 1]):
                penalty_score += 3
    return penalty_score

def penalty_3(grid):
    size = len(grid)
    penalty_score = 0
    pattern1 = [1,0,1,1,1,0,1,0,0,0,0]
    pattern2 = [0,0,0,0,1,0,1,1,1,0,1]
    pattern_length = len(pattern1)
    for r in range(size):
        for c in range(size - pattern_length + 1):
            window = grid[r][c:c+pattern_length]
            if window == pattern1 or window == pattern2:
                # print("Found pattern at row", r, "col", c, ":", window)
                penalty_score += 40
    for c in range(size):
        for r in range(size - pattern_length + 1):
            window = [grid[r+i][c] for i in range(pattern_length)]
            if window == pattern1 or window == pattern2:
                penalty_score += 40
                # print("Found pattern at col", c, "rpw", r, ":", window)
    return penalty_score

def penalty_4(grid):
    size = len(grid)
    dark_modules = 0
    reserved_modules = 0
    for r in range(size):
        for c in range(size):
            if is_reserved(r, c):
                continue
            reserved_modules += 1
            if grid[r][c] == 1:
                dark_modules += 1
    percent = (dark_modules * 100) // reserved_modules
    prev_multiple = (percent // 5) * 5
    next_multiple = prev_multiple + 5 if percent % 5 != 0 else prev_multiple

    # calculate deviation from 50 for both multiples
    deviation_prev = abs(prev_multiple - 50)
    deviation_next = abs(next_multiple - 50)

    # divide each by 5
    prev_multiple_ratio = deviation_prev / 5
    next_multiple_ratio = deviation_next / 5

    penalty = next_multiple_ratio
    if prev_multiple_ratio > next_multiple_ratio:
        penalty = prev_multiple_ratio

    # return the penalty (the smaller deviation * 10)
    penalty *= 10
    return penalty

def apply_mask_pattern(grid, m=0):
    size = len(grid)
    grid_copy = grid
    mask_pattern_no = m
    for r in range(size):
        for c in range(size):
            if (is_reserved(r, c, size)):
                continue
            if mask_pattern_no == 0:
                if (r + c) % 2 == 0:
                    grid_copy[r][c] ^= 1
            elif mask_pattern_no == 1:
                if r % 2 == 0:
                    grid_copy[r][c] ^= 1
            elif mask_pattern_no == 2:
                if c % 3 == 0:
                    grid_copy[r][c] ^= 1
            elif mask_pattern_no == 3:
                if (r + c) % 3 == 0:
                    grid_copy[r][c] ^= 1
            elif mask_pattern_no == 4:
                if ((r // 2) + (c // 3)) % 2 == 0:
                    grid_copy[r][c] ^= 1
            elif mask_pattern_no == 5:
                if ((r * c) % 2) + ((r * c) % 3) == 0:
                    grid_copy[r][c] ^= 1
            elif mask_pattern_no == 6:
                if ( ((r * c) % 2) + ((r * c) % 3) ) % 2 == 0:
                    grid_copy[r][c] ^= 1
            elif mask_pattern_no == 7:
                if ( ((r + c) % 2) + ((r * c) % 3) ) % 2 == 0:
                    grid_copy[r][c] ^= 1
    return grid_copy

def get_format_bits(ec='L', mask_pattern_no=0):
    mask_pattern = "000"
    if mask_pattern_no == 1:
        mask_pattern = "001"
    elif mask_pattern_no == 2:
        mask_pattern = "010"
    elif mask_pattern_no == 3:
        mask_pattern = "011"
    elif mask_pattern_no == 4:
        mask_pattern = "100"
    elif mask_pattern_no == 5:
        mask_pattern = "101"
    elif mask_pattern_no == 6:
        mask_pattern = "110"
    elif mask_pattern_no == 7:
        mask_pattern = "111"
    
    if ec == 'L':
        error_correction = '01'
    if ec == 'M':
        error_correction = '00'
    if ec == 'Q':
        error_correction = '11'
    if ec == 'H':
        error_correction = '10'

    format_data = error_correction + mask_pattern
    format_data_value = int(format_data, 2)
    data = format_data_value << 10
    generator = 0b10100110111

    for i in range(14, 9, -1):
        if (data >> i) & 1:
            data ^= generator << (i - 10)

    # Combine original 5 bits and 10-bit error correction
    full_format = (format_data_value << 10) | data

    # Apply mask (0x5412)
    masked = full_format ^ 0b101010000010010

    return format(masked, '015b')

def place_format_bits(grid, format_bits):
    size = len(grid)-1
    c = 0
    for i in range(9):
        if i == 6:
            continue ## dark module
        if i > 6:
            grid[8][i] = int(format_bits[i-1])
        else:
            grid[8][i] = int(format_bits[i])
    c=7
    for i in reversed(range(8)):
        if i == 6:
            continue ## alignment area
        if i < 6:
            grid[i][8] = int(format_bits[1+c])
        else:
            grid[i][8] = int(format_bits[c])
        c+=1
    c=0
    for i in range(8):
        grid[size-i][8] = int(format_bits[i])
    c=7
    for i in range(8):
        grid[8][size-7+i] = int(format_bits[i+c])

def calculate_ecc_codewords(V, ecc_level):
    if V == 1 and ecc_level == 'L':
        ecc_codewords = 7
    if V == 1 and ecc_level == 'M':
        ecc_codewords = 10
    if V == 1 and ecc_level == 'Q':
        ecc_codewords = 13
    if V == 1 and ecc_level == 'H':
        ecc_codewords = 17
    if V == 2 and ecc_level == 'L':
        ecc_codewords = 10
    if V == 2 and ecc_level == 'M':
        ecc_codewords = 16
    if V == 2 and ecc_level == 'Q':
        ecc_codewords = 22
    if V == 2 and ecc_level == 'H':
        ecc_codewords = 28
    return ecc_codewords

#text = input() ## accept input string
logo = False
def process_input(data, ecc_level='H', logoBool=False):
    print("Processing in processor.py:", data)
    text = data
    global logo
    logo = logoBool
    V = 1

    # if len(data) > 17:
    #     V = 2

    textEncoded = bytearray(text, 'utf-8') ## to utf-8 to turn into byte mode | Correct handling of byte mode
    print(list(textEncoded))

    ecc_codewords = calculate_ecc_codewords(V, ecc_level)

    padding = ["11101100", "00010001"]
    data_codewords, V, ecc_level = build_qr_payload(textEncoded, ecc_level, V) # data_codewords [/]
    print("codewords -> ", data_codewords)
    print("codewords -> ", len(data_codewords))
    ecc_codewords = calculate_ecc_codewords(V, ecc_level)
    corrected_bits = generate_error_corrected_codewords(data_codewords, ecc_codewords) # ecc_codewords [/]
    # print(corrected_bits) 
    size = (((V-1)*4)+21)
    grid = generate_grid(size)
    add_timing_patterns(grid)
    if V == 2:
        add_alignment_patterns(grid) ## version 2 only
    add_dark_module(grid)
    add_data(grid, corrected_bits)

    # apply_mask_pattern(grid)

    # format_bits = get_format_bits("00", 0)
    # place_format_bits(grid, format_bits)

    # print(get_format_bits())

    # print("penalty 1 - >",  penalty_1(grid))
    # print("penalty 2 - >",  penalty_2(grid))
    # print("penalty 3 - >",  penalty_3(grid))
    # print("penalty 4 - >",  penalty_4(grid))

    penalty_score_0 = penalty_1(apply_mask_pattern(grid, 0)) + penalty_2(apply_mask_pattern(grid, 0)) + penalty_3(apply_mask_pattern(grid, 0)) + penalty_4(apply_mask_pattern(grid, 0))
    penalty_score_1 = penalty_1(apply_mask_pattern(grid, 1)) + penalty_2(apply_mask_pattern(grid, 1)) + penalty_3(apply_mask_pattern(grid, 1)) + penalty_4(apply_mask_pattern(grid, 1))
    penalty_score_2 = penalty_1(apply_mask_pattern(grid, 2)) + penalty_2(apply_mask_pattern(grid, 2)) + penalty_3(apply_mask_pattern(grid, 2)) + penalty_4(apply_mask_pattern(grid, 2))
    penalty_score_3 = penalty_1(apply_mask_pattern(grid, 3)) + penalty_2(apply_mask_pattern(grid, 3)) + penalty_3(apply_mask_pattern(grid, 3)) + penalty_4(apply_mask_pattern(grid, 3))
    penalty_score_4 = penalty_1(apply_mask_pattern(grid, 4)) + penalty_2(apply_mask_pattern(grid, 4)) + penalty_3(apply_mask_pattern(grid, 4)) + penalty_4(apply_mask_pattern(grid, 4))
    penalty_score_5 = penalty_1(apply_mask_pattern(grid, 5)) + penalty_2(apply_mask_pattern(grid, 5)) + penalty_3(apply_mask_pattern(grid, 5)) + penalty_4(apply_mask_pattern(grid, 5))
    penalty_score_6 = penalty_1(apply_mask_pattern(grid, 6)) + penalty_2(apply_mask_pattern(grid, 6)) + penalty_3(apply_mask_pattern(grid, 6)) + penalty_4(apply_mask_pattern(grid, 6))
    penalty_score_7 = penalty_1(apply_mask_pattern(grid, 7)) + penalty_2(apply_mask_pattern(grid, 7)) + penalty_3(apply_mask_pattern(grid, 7)) + penalty_4(apply_mask_pattern(grid, 7))
    penalty_score = min(penalty_score_0, penalty_score_1, penalty_score_2, penalty_score_3, penalty_score_4, penalty_score_5, penalty_score_6, penalty_score_7)
    mask = 0
    penalty_3(grid)
    if penalty_score == penalty_score_7:
        mask = 7
    elif penalty_score == penalty_score_6:
        mask = 6
    elif penalty_score == penalty_score_5:
        mask = 5
    elif penalty_score == penalty_score_4:
        mask = 4
    elif penalty_score == penalty_score_3:
        mask = 3
    elif penalty_score == penalty_score_2:
        mask = 2
    elif penalty_score == penalty_score_1:
        mask = 1
    elif penalty_score == penalty_score_0:
        mask = 0


    grid = apply_mask_pattern(grid, mask)

    format_bits = get_format_bits(ecc_level, mask)
    place_format_bits(grid, format_bits)

    for row in grid:
        print(''.join('🟨' if cell == 2 else '⬛' if cell == 1 else '⬜' for cell in row))
        # print(''.join('⬛' if cell else '⬜' for cell in row))

    image = visualize_qr(grid, ecc_level)
    return image

def calculate_image_size(grid, ecc_level):
    size_table = {
        (1, 'L'): 0.05, (1, 'M'): 0.055, (1, 'Q'): 0.065, (1, 'H'): 0.075,
        (2, 'L'): 0.0525, (2, 'M'): 0.075, (2, 'Q'): 0.075, (2, 'H'): 0.055,
    }
    V = 1
    if len(grid) > 21:
        V = 2
    size = size_table.get((V, ecc_level))
    return 0

def visualize_qr(grid, ecc_level, image_path="./test_image.png"):
    # Create the plot
    fig, ax = plt.subplots()
    ax.imshow(grid, cmap='binary')
    ax.axis('off')
    image_size = calculate_image_size(grid, ecc_level)
    # Load the image to overlay
    center_img = mpimg.imread(image_path)
    imagebox = OffsetImage(center_img, zoom=image_size)  # control image size with zoom

    # Get grid center
    rows = len(grid)
    cols = len(grid[0]) if grid else 0
    grid_center = (cols / 2 - 4, rows / 2 - 4)

    # Add the image to the plot
    ab = AnnotationBbox(imagebox, grid_center, frameon=False, box_alignment=(0,1))
    ax.add_artist(ab)

    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.25)
    plt.close(fig)
    buf.seek(0)

    # Encode as base64
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64



# # === Visualize the QR Code ===
# def visualize_qr(grid):
#     # Use Matplotlib to visualize the QR code as a 2D image
#     plt.imshow(grid, cmap='binary')  # 'binary' colormap renders 0 as white, 1 as black
#     plt.axis('off')  # Turn off axis
#     plt.show()

# visualize_qr(grid)