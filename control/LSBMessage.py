import PIL.Image
from bitarray import bitarray


class LSBMessage:
    @staticmethod
    def inject_message(
        img_in: PIL.Image.Image, message_bits: bitarray
    ) -> PIL.Image.Image:
        img = img_in.copy()
        pixels_in = img_in.load()
        pixels = img.load()
        if pixels_in is None or pixels is None:
            raise BaseException("pixels_in is None")

        msg_index = 0

        def index_in():
            return msg_index < len(message_bits) - 1

        def mi():
            try:
                return (message_bits[msg_index] << 1) | message_bits[msg_index + 1]
            except BaseException:
                return 0b100

        for x in range(img.size[0]):
            for y in range(img.size[1]):
                if not index_in():
                    break

                byte = pixels_in[x, y]
                clp = (byte & 0b11000000) >> 6
                cmp = (byte & 0b01100000) >> 5
                crp = (byte & 0b00110000) >> 4

                if mi() == clp:
                    byte |= 1 << 2
                    msg_index += 2
                else:
                    byte &= ~(1 << 2)
                if mi() == cmp:
                    byte |= 1 << 1
                    msg_index += 2
                else:
                    byte &= ~(1 << 1)
                if mi() == crp:
                    byte |= 1
                    msg_index += 2
                else:
                    byte &= ~(1)

                pixels[x, y] = byte
            else:
                continue
            break

        return img

    @staticmethod
    def extract_message(img_in: PIL.Image.Image, message_bit_len: int) -> bitarray:
        pixels_in = img_in.load()
        msg_index = 0
        message_bits = [0] * message_bit_len
        if pixels_in is None:
            raise BaseException("pixels_in is None")

        def index_in():
            return msg_index < len(message_bits) - 1

        for x in range(img_in.size[0]):
            for y in range(img_in.size[1]):
                if not index_in():
                    break

                byte = pixels_in[x, y]
                clp = (byte & 0b11000000) >> 6
                cmp = (byte & 0b01100000) >> 5
                crp = (byte & 0b00110000) >> 4

                if byte & (1 << 2):
                    message_bits[msg_index] = clp >> 1
                    message_bits[msg_index + 1] = clp & 1
                    msg_index += 2
                    if not index_in():
                        break

                if byte & (1 << 1):
                    message_bits[msg_index] = cmp >> 1
                    message_bits[msg_index + 1] = cmp & 1
                    msg_index += 2
                    if not index_in():
                        break

                if byte & (1):
                    message_bits[msg_index] = crp >> 1
                    message_bits[msg_index + 1] = crp & 1
                    msg_index += 2
            else:
                continue
            break

        return bitarray(message_bits[:msg_index])

    @staticmethod
    def get_max_capacity(img_in: PIL.Image.Image, message_bits: bitarray):
        img = img_in.copy()
        pixels_in = img_in.load()
        pixels = img.load()
        if pixels_in is None or pixels is None:
            raise BaseException("pixels_in is None")

        msg_index = 0

        def index_in():
            return msg_index < len(message_bits) - 1

        def mi():
            try:
                return (message_bits[msg_index] << 1) | message_bits[msg_index + 1]
            except BaseException:
                return 0b100

        for x in range(img.size[0]):
            for y in range(img.size[1]):
                if not index_in():
                    break

                byte = pixels_in[x, y]
                clp = (byte & 0b11000000) >> 6
                cmp = (byte & 0b01100000) >> 5
                crp = (byte & 0b00110000) >> 4

                if mi() == clp:
                    byte |= 1 << 2
                    msg_index += 2
                else:
                    byte &= ~(1 << 2)
                if mi() == cmp:
                    byte |= 1 << 1
                    msg_index += 2
                else:
                    byte &= ~(1 << 1)
                if mi() == crp:
                    byte |= 1
                    msg_index += 2
                else:
                    byte &= ~(1)

                pixels[x, y] = byte
            else:
                continue
            break

        return msg_index
