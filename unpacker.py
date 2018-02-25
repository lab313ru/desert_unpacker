import argparse

import os
from struct import pack

WND_LEN = 2048
WND_MASK = (WND_LEN - 1)


def read_word(buf, offset):
    return (buf[offset + 0] << 8) |\
           (buf[offset + 1] << 0)


def read_dword(buf, offset):
    return (buf[offset + 0] << 24) |\
           (buf[offset + 1] << 16) |\
           (buf[offset + 2] << 8) |\
           (buf[offset + 3] << 0)


def unpack_buffer(buf):
    window = bytearray(WND_LEN)

    wnd_off = 0x7EE
    cmd_bits = 0
    cmd = 0

    write_off = 0
    read_off = 0
    dest_size = read_dword(buf, read_off)
    read_off += 4

    dest = bytearray(dest_size)

    while True:
        cmd_bits -= 1

        if cmd_bits < 0:
            cmd = buf[read_off]
            cmd_bits = 7
            read_off += 1

        bit = (cmd & 1)
        cmd >>= 1

        if bit:
            dest[write_off] = window[wnd_off] = buf[read_off]
            write_off += 1
            read_off += 1
            dest_size -= 1
            wnd_off = (wnd_off + 1) & WND_MASK
        else:
            token = read_word(buf, read_off)
            copy_from = ((token & 0xF0) << 4) | (token >> 8)
            copy_count = (token & 0x0F) + 3
            read_off += 2

            i = 0
            while i < copy_count and dest_size > 0:
                dest[write_off + i] = window[(wnd_off + i) & WND_MASK] = window[(copy_from + i) & WND_MASK]
                i += 1
                dest_size -= 1

            write_off += copy_count
            wnd_off = (wnd_off + copy_count) & WND_MASK

        if dest_size == 0:
            break

    return read_off, dest


def unpack_file(path, offset):
    with open(path, 'rb') as f:
        f.seek(offset)
        data = bytearray(f.read())

        in_size, out_data = unpack_buffer(data)
        return in_size, str(out_data)


def read_word_or(buf, offset, d):
    return (d & 0xFFFF0000) | read_word(buf, offset)


def swap_words(d):
    return ((d >> 16) & 0x0000FFFF) |\
           ((d << 16) & 0xFFFF0000)


def swap_and_read(buf, offset, d):
    return swap_words((swap_words(d) & 0xFFFF0000) | read_word(buf, offset))


def expand_data(buf):
    read_off = 0

    dest = ''

    count = read_word(buf, read_off)
    read_off += 2

    d0 = 0
    d1 = 0
    d2 = 0
    d3 = 0
    a0 = 0
    a1 = 0
    a2 = 0
    a3 = 0

    while count > 0:
        token = read_word(buf, read_off)
        read_off += 2

        for i in xrange(2):
            p1 = (token >> 0) & 0x0F
            p2 = (token >> 4) & 0x0F
            token >>= 8

            # part 1
            if p1 == 1:
                d0 = swap_and_read(buf, read_off, d0)
                read_off += 2

            elif p1 == 2:
                d0 = read_word_or(buf, read_off, d0)
                read_off += 2

            elif p1 == 3:
                d0 = read_dword(buf, read_off)
                read_off += 4

            elif p1 == 4:
                d1 = swap_and_read(buf, read_off, d1)
                read_off += 2

            elif p1 == 5:
                d0 = swap_and_read(buf, read_off, d0)
                read_off += 2

                d1 = swap_and_read(buf, read_off, d1)
                read_off += 2

            elif p1 == 6:
                d0 = read_word_or(buf, read_off, d0)
                read_off += 2

                d1 = swap_and_read(buf, read_off, d1)
                read_off += 2

            elif p1 == 7:
                d0 = read_dword(buf, read_off)
                read_off += 4

                d1 = swap_and_read(buf, read_off, d1)
                read_off += 2

            elif p1 == 8:
                d1 = read_word_or(buf, read_off, d1)
                read_off += 2

            elif p1 == 9:
                d0 = swap_and_read(buf, read_off, d0)
                read_off += 2

                d1 = read_word_or(buf, read_off, d1)
                read_off += 2

            elif p1 == 10:
                d0 = read_word_or(buf, read_off, d0)
                read_off += 2

                d1 = read_word_or(buf, read_off, d1)
                read_off += 2

            elif p1 == 11:
                d0 = read_dword(buf, read_off)
                read_off += 4

                d1 = read_word_or(buf, read_off, d1)
                read_off += 2

            elif p1 == 12:
                d1 = read_dword(buf, read_off)
                read_off += 4

            elif p1 == 13:
                d0 = swap_and_read(buf, read_off, d0)
                read_off += 2

                d1 = read_dword(buf, read_off)
                read_off += 4

            elif p1 == 14:
                d0 = read_word_or(buf, read_off, d0)
                read_off += 2

                d1 = read_dword(buf, read_off)
                read_off += 4

            elif p1 == 15:
                d0 = read_dword(buf, read_off)
                read_off += 4

                d1 = read_dword(buf, read_off)
                read_off += 4

            # part 2
            if p2 == 1:
                d2 = swap_and_read(buf, read_off, d2)
                read_off += 2

            elif p2 == 2:
                d2 = read_word_or(buf, read_off, d2)
                read_off += 2

            elif p2 == 3:
                d2 = read_dword(buf, read_off)
                read_off += 4

            elif p2 == 4:
                d3 = swap_and_read(buf, read_off, d3)
                read_off += 2

            elif p2 == 5:
                d2 = swap_and_read(buf, read_off, d2)
                read_off += 2

                d3 = swap_and_read(buf, read_off, d3)
                read_off += 2

            elif p2 == 6:
                d2 = read_word_or(buf, read_off, d2)
                read_off += 2

                d3 = swap_and_read(buf, read_off, d3)
                read_off += 2

            elif p2 == 7:
                d2 = read_dword(buf, read_off)
                read_off += 4

                d3 = swap_and_read(buf, read_off, d3)
                read_off += 2

            elif p2 == 8:
                d3 = read_word_or(buf, read_off, d3)
                read_off += 2

            elif p2 == 9:
                d2 = swap_and_read(buf, read_off, d2)
                read_off += 2

                d3 = read_word_or(buf, read_off, d3)
                read_off += 2

            elif p2 == 10:
                d2 = read_word_or(buf, read_off, d2)
                read_off += 2

                d3 = read_word_or(buf, read_off, d3)
                read_off += 2

            elif p2 == 11:
                d2 = read_dword(buf, read_off)
                read_off += 4

                d3 = read_word_or(buf, read_off, d3)
                read_off += 2

            elif p2 == 12:
                d3 = read_dword(buf, read_off)
                read_off += 4

            elif p2 == 13:
                d2 = swap_and_read(buf, read_off, d2)
                read_off += 2

                d3 = read_dword(buf, read_off)
                read_off += 4

            elif p2 == 14:
                d2 = read_word_or(buf, read_off, d2)
                read_off += 2

                d3 = read_dword(buf, read_off)
                read_off += 4

            elif p2 == 15:
                d2 = read_dword(buf, read_off)
                read_off += 4

                d3 = read_dword(buf, read_off)
                read_off += 4

            d0, a0 = a0, d0
            d1, a1 = a1, d1
            d2, a2 = a2, d2
            d3, a3 = a3, d3

        dest += pack('>IIIIIIII', d0, d1, d2, d3, a0, a1, a2, a3)
        count -= 1

    return read_off, dest


def expand_file(path, offset):
    with open(path, 'rb') as f:
        f.seek(offset)
        data = bytearray(f.read())

        in_size, out_data = expand_data(data)
        return in_size, out_data


def auto_hex(x):
    return int(x, 16)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('file', action='store', help='File to pack or unpack')
    parser.add_argument('action', action='store', help='Action', type=str, choices=['c', 'd', 'e'])
    parser.add_argument('--offset', action='store', help='Data offset', type=auto_hex, default='0')

    args = parser.parse_args()

    if args.action == 'd':
        packed_size, unpacked_data = unpack_file(args.file, args.offset)

        fname, fext = os.path.splitext(args.file)
        with open('%s_%.6X%s' % (fname, args.offset, fext), 'wb') as f:
            f.write(unpacked_data)

        print 'Unpacked %d -> %d bytes' % (packed_size, len(unpacked_data))
    elif args.action == 'e':
        in_size, expanded_data = expand_file(args.file, args.offset)

        fname, fext = os.path.splitext(args.file)
        with open('%s_%.6X%s' % (fname, args.offset, fext), 'wb') as f:
            f.write(expanded_data)

        print 'Unpacked %d -> %d bytes' % (in_size, len(expanded_data))
