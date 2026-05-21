import PIL.Image
from bitarray import bitarray


class LSBSeq:
    @staticmethod
    def inject_message(img_in: PIL.Image.Image, message: bitarray) -> PIL.Image.Image:
        img = img_in.copy()
        pixels = img.load()
        last_x = None
        last_y = None
        msg_index = 0
        max_valid = len(message) - len(message) % 3
        if pixels is None:
            raise BaseException("pixels_in is None")
        for x in range(img.width):
            for y in range(img.height):
                if msg_index >= max_valid:
                    last_x = x
                    last_y = y
                    break
                byte = pixels[x, y]

                for index in range(3):
                    if message[msg_index + index]:
                        byte |= 1 << index
                    else:
                        byte &= ~(1 << index)

                pixels[x, y] = byte

                msg_index += 3
            else:
                continue
            break

        if last_x is not None and last_y is not None:
            last_bits_len = len(message) % 3
            byte = pixels[last_x, last_y]
            for index in range(last_bits_len):
                if message[-(last_bits_len - index)]:
                    byte |= 1 << index
                else:
                    byte &= ~(1 << index)
            pixels[last_x, last_y] = byte

        return img

    @staticmethod
    def get_max_capacity(img_in: PIL.Image.Image) -> int:
        return img_in.width * img_in.height // 3
