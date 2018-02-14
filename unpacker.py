import argparse

import os

WND_LEN = 2048
WND_MASK = (WND_LEN - 1)


def unpack_buffer(buf):
    window = bytearray(WND_LEN)

    wnd_off = 0x7EE
    cmd_bits = 0
    cmd = 0

    write_off = 0
    read_off = 0
    dest_size = (buf[read_off + 0] << 24) |\
                (buf[read_off + 1] << 16) |\
                (buf[read_off + 2] << 8) |\
                (buf[read_off + 3] << 0)
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
            token = (buf[read_off + 0] << 8) | (buf[read_off + 1] << 0)
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


def auto_hex(x):
    return int(x, 16)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('file', action='store', help='File to pack or unpack')
    parser.add_argument('action', action='store', help='Action', type=str, choices=['c', 'd'])
    parser.add_argument('--offset', action='store', help='Data offset', type=auto_hex, default='0')

    args = parser.parse_args()

    if args.action == 'd':
        packed_size, unpacked_data = unpack_file(args.file, args.offset)

        fname, fext = os.path.splitext(args.file)
        with open('%s_%.6X%s' % (fname, args.offset, fext), 'wb') as f:
            f.write(unpacked_data)

        print 'Unpacked %d -> %d bytes' % (packed_size, len(unpacked_data))
