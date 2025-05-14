import reedsolo

def is_reserved(r, c, size=21):
    if (r < 9 and c < 9) or (r < 9 and c >= size - 8) or (r >= size - 8 and c < 9):
        return True  # Finder patterns
    if c == 6 or r == 6:
        return True  # Timing patterns
    if (r, c) == (13, 8):
        return True  # Dark module
    return False

def generate_error_corrected_codewords(data_bytes, ecc_codewords):
    rs = reedsolo.RSCodec(ecc_codewords)
    encoded_data = rs.encode(data_bytes)
    corrected_bits = ''.join(format(byte, '08b') for byte in encoded_data)
    return corrected_bits

def build_qr_payload(data_bytes):
    bits = '0100'  # Mode indicator (byte mode)
    bits += format(len(data_bytes), '08b')  # Byte count

    for byte in data_bytes:
        bits += format(byte, '08b')

    bits += '0000'  # Terminator

    while len(bits) % 8 != 0:
        bits += '0'

    pad_bytes = ['11101100', '00010001']
    i = 0
    while len(bits) < 152:
        bits += pad_bytes[i % 2]
        i += 1

    return [int(bits[i:i+8], 2) for i in range(0, len(bits), 8)]

def generate_grid():
    size = 21
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
    place_finder_pattern(14, 0)
    place_finder_pattern(0, 14)

    return grid

def add_timing_patterns(grid, size=21):
    for i in range(8, size - 8):
        grid[6][i] = i % 2
        grid[i][6] = i % 2

def add_dark_module(grid):
    grid[13][8] = 1

def place_data_in_grid(grid, data_bits):
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
                    continue
                if bit_index < len(data_bits):
                    grid[row][c] = int(data_bits[bit_index])
                    bit_index += 1

        col -= 2
        direction *= -1

    return grid

def apply_mask(grid, size=21):
    for y in range(size):
        for x in range(size):
            if grid[y][x] in [0, 1] and not is_reserved(y, x, size):
                if (x + y) % 2 == 0:
                    grid[y][x] ^= 1

def get_format_bits(error_correction='01', mask_pattern='000'):
    format_data = error_correction + mask_pattern
    data = int(format_data, 2) << 10
    generator = 0b10100110111

    for i in range(14, 10, -1):
        if (data >> i) & 1:
            data ^= generator << (i - 10)

    # Combine and mask
    full_format = (int(format_data, 2) << 10) | data
    masked = full_format ^ 0b101010000010010

    return format(masked, '015b')

def place_format_bits(grid, format_bits):
    size = len(grid)

    # Around top-left
    for i in range(6):
        grid[i][8] = int(format_bits[i])         # Vertical above
    grid[7][8] = int(format_bits[6])
    grid[8][8] = int(format_bits[7])
    grid[8][7] = int(format_bits[8])
    for i in range(6):
        grid[8][5 - i] = int(format_bits[9 + i])  # Horizontal left

    # Near top-right
    for i in range(8):
        grid[8][size - 1 - i] = int(format_bits[i])

    # Near bottom-left
    for i in range(7):
        grid[size - 1 - i][8] = int(format_bits[8 + i])

# === Main ===
text = input("Enter text: ")
text_encoded = bytearray(text, 'utf-8')

ecc_codewords = 7

data_codewords = build_qr_payload(text_encoded)
corrected_bits = generate_error_corrected_codewords(data_codewords, ecc_codewords)

grid = generate_grid()
add_timing_patterns(grid)
add_dark_module(grid)
place_data_in_grid(grid, corrected_bits)
apply_mask(grid)

format_bits = get_format_bits()
place_format_bits(grid, format_bits)

# Visual print
for row in grid:
    print(''.join('⬛' if cell else '⬜' for cell in row))
