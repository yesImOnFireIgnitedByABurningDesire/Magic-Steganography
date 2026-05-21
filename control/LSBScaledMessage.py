import PIL.Image
from bitarray import bitarray
import numpy

SCALE_COEF = 2


class LSBScaledMessage:
    @staticmethod
    def scale_image(img_in: PIL.Image.Image) -> PIL.Image.Image:
        img_out = PIL.Image.new("L", (img_in.size[0] * 2, img_in.size[1] * 2))

        pixels_in = img_in.load()
        pixels_out = img_out.load()

        if pixels_in is None or pixels_out is None:
            raise BaseException("pixel arrays are none")

        BLOCKS = img_in.size[0]

        for m in range(BLOCKS - 1):
            for n in range(BLOCKS - 1):
                x = m * SCALE_COEF
                y = n * SCALE_COEF
                pixels_out[x, y] = pixels_in[m, n]
                pixels_out[x + 1, y] = (
                    pixels_in[m, n] + pixels_in[m + 1, n]
                ) // SCALE_COEF
                pixels_out[x, y + 1] = (
                    pixels_in[m, n] + pixels_in[m, n + 1]
                ) // SCALE_COEF
                pixels_out[x + 1, y + 1] = (
                    SCALE_COEF * pixels_in[m, n]
                    + (pixels_in[m + 1, n] + pixels_in[m, n + 1]) // SCALE_COEF
                ) // (SCALE_COEF + 1)

        # Fill bottom border
        for m in range(BLOCKS):
            n = BLOCKS - 1
            for x in range(m * SCALE_COEF, (m + 1) * SCALE_COEF):
                for y in range(n * SCALE_COEF, (n + 1) * SCALE_COEF):
                    pixels_out[x, y] = pixels_in[m, n]

        # Fill right border
        for n in range(BLOCKS):
            m = BLOCKS - 1
            for x in range(m * SCALE_COEF, (m + 1) * SCALE_COEF):
                for y in range(n * SCALE_COEF, (n + 1) * SCALE_COEF):
                    pixels_out[x, y] = pixels_in[m, n]

        return img_out

    @staticmethod
    def inject_message(
        img_in: PIL.Image.Image, message_bits: bitarray
    ) -> PIL.Image.Image:
        img_out = img_in.copy()
        pixels_in = img_in.load()
        pixels_out = img_out.load()

        if pixels_in is None or pixels_out is None:
            raise BaseException("pixel arrays are none")

        # positions = []

        message_bits_index = 0
        # Going by blocks
        for x in range(0, img_out.size[0] - SCALE_COEF * 2, SCALE_COEF):
            for y in range(0, img_out.size[1] - SCALE_COEF * 2, SCALE_COEF):
                bit_counts = tuple(
                    int(
                        numpy.log2(
                            max(
                                numpy.abs(
                                    pixels_out[x + x_i, y + y_i] - pixels_out[x, y]
                                ),
                                1,
                            )
                        )
                    )
                    for y_i in range(SCALE_COEF)
                    for x_i in range(SCALE_COEF)
                )
                for y_i in range(SCALE_COEF):
                    for x_i in range(SCALE_COEF):
                        message_bits_next_index = (
                            message_bits_index + bit_counts[x_i + y_i * SCALE_COEF]
                        )
                        val = sum(
                            el << index
                            for index, el in enumerate(
                                reversed(
                                    message_bits[
                                        message_bits_index:message_bits_next_index
                                    ]
                                )
                            )
                        )
                        # if bit_counts[x_i + y_i * SCALE_COEF] > 0:
                        #     positions.append(tuple([x + x_i, y + y_i, val]))
                        pixels_out[x + x_i, y + y_i] += val

                        if message_bits_next_index >= len(message_bits):
                            break
                        message_bits_index = message_bits_next_index
                    # broke a leg, falling down the stairs
                    else:
                        continue
                    break
                else:
                    continue
                break
            else:
                continue
            break

        # print(positions)
        return img_out

    @staticmethod
    def extract_message(img_in: PIL.Image.Image, message_bit_len: int) -> bitarray:
        pixels_in = img_in.load()
        if pixels_in is None:
            raise BaseException("pixels array is none")
        message_bits: list[int] = []
        # positions = []

        for x in range(0, img_in.size[0] - SCALE_COEF * 2, SCALE_COEF):
            for y in range(0, img_in.size[1] - SCALE_COEF * 2, SCALE_COEF):
                vals = (
                    0,
                    pixels_in[x + 1, y]
                    - (pixels_in[x, y] + pixels_in[x + SCALE_COEF, y]) // SCALE_COEF,
                    pixels_in[x, y + 1]
                    - (pixels_in[x, y] + pixels_in[x, y + SCALE_COEF]) // SCALE_COEF,
                    pixels_in[x + 1, y + 1]
                    - (
                        SCALE_COEF * pixels_in[x, y]
                        + (pixels_in[x + SCALE_COEF, y] + pixels_in[x, y + SCALE_COEF])
                        // SCALE_COEF
                    )
                    // (SCALE_COEF + 1),
                )
                bit_counts = tuple(
                    int(
                        numpy.log2(
                            max(
                                numpy.abs(
                                    pixels_in[x + x_i, y + y_i]
                                    - vals[x_i + y_i * SCALE_COEF]
                                    - pixels_in[x, y]
                                ),
                                1,
                            )
                        )
                    )
                    for y_i in range(SCALE_COEF)
                    for x_i in range(SCALE_COEF)
                )
                vals = tuple(
                    [int(i) for i in f"{val:0{bit_counts[index]}b}"]
                    if bit_counts[index] > 0
                    else []
                    for index, val in enumerate(vals)
                )
                # for y_i in range(SCALE_COEF):
                #     for x_i in range(SCALE_COEF):
                #         if bit_counts[x_i + y_i * SCALE_COEF] > 0:
                #             positions.append(
                #                 tuple([x + x_i, y + y_i, vals[x_i + y_i * SCALE_COEF]])
                #             )
                for val in vals:
                    message_bits += val
                    # message_bits += (
                    #     val[min(0, message_bit_len - len(message_bits)) :: -1]
                    # )[::-1]
                    if len(message_bits) >= message_bit_len:
                        diff = len(message_bits) - message_bit_len
                        # print(diff)
                        # vals = [x for x in vals if len(x) > 0]
                        message_bits = (
                            message_bits[: len(message_bits) - len(val)]
                            + val[::-1][: len(val) - diff][::-1]
                        )
                        # print(val)
                        # print(val[::-1][: len(val) - diff :][::-1])
                        break
                    else:
                        continue
                    break
                else:
                    continue
                break
            else:
                continue
            break
        # print(positions)

        return bitarray(message_bits)

    @staticmethod
    def get_max_capacity(img_in: PIL.Image.Image) -> int:
        pixels_in = img_in.load()
        if pixels_in is None:
            raise BaseException("pixels_in is none")
        capacity = 0
        for x in range(0, img_in.size[0] - SCALE_COEF, SCALE_COEF):
            for y in range(0, img_in.size[1] - SCALE_COEF, SCALE_COEF):
                bit_counts = tuple(
                    int(
                        numpy.log2(
                            max(
                                numpy.abs(
                                    pixels_in[x + x_i, y + y_i] - pixels_in[x, y]
                                ),
                                1,
                            )
                        )
                    )
                    for y_i in range(SCALE_COEF)
                    for x_i in range(SCALE_COEF)
                )
                capacity += sum(bit_counts)

        return capacity
