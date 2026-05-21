import PIL.Image


class VisualAttacker:
    @staticmethod
    def attack_image(img_in: PIL.Image.Image, bit_index: int) -> PIL.Image.Image:
        img = PIL.Image.new("L", img_in.size)
        pixels_in = img_in.load()
        pixels = img.load()

        if pixels_in is None or pixels is None:
            raise BaseException("pixel arrays are none")

        for x in range(img.size[0]):
            for y in range(img.size[1]):
                pixels[x, y] = 255 * (pixels_in[x, y] & (1 << bit_index))
        return img
