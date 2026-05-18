from PIL import Image
import atexit
import os
import numpy as np
from matplotlib import pyplot as plt

SCALE_COEF = 2


def attackImage(image: Image.Image, bitIndex: int) -> Image.Image:
    img = Image.new("L", image.size)
    pixelsIn = image.load()
    pixels = img.load()

    if pixelsIn is None or pixels is None:
        raise BaseException("pixel arrays are none")

    for x in range(img.size[0]):
        for y in range(img.size[1]):
            pixels[x, y] = 255 * (pixelsIn[x, y] & (1 << bitIndex))
    return img


def scaleImage(imgIn: Image.Image) -> Image.Image:
    imgOut = Image.new("L", (imgIn.size[0] * 2, imgIn.size[1] * 2))

    pixelsIn = imgIn.load()
    pixelsOut = imgOut.load()

    if pixelsIn is None or pixelsOut is None:
        raise BaseException("pixel arrays are none")

    BLOCKS = imgIn.size[0]

    for m in range(BLOCKS - 1):
        for n in range(BLOCKS - 1):
            x = m * SCALE_COEF
            y = n * SCALE_COEF
            pixelsOut[x, y] = pixelsIn[m, n]
            pixelsOut[x + 1, y] = (pixelsIn[m, n] + pixelsIn[m + 1, n]) // SCALE_COEF
            pixelsOut[x, y + 1] = (pixelsIn[m, n] + pixelsIn[m, n + 1]) // SCALE_COEF
            pixelsOut[x + 1, y + 1] = (
                SCALE_COEF * pixelsIn[m, n]
                + (pixelsIn[m + 1, n] + pixelsIn[m, n + 1]) // SCALE_COEF
            ) // (SCALE_COEF + 1)

    # Fill bottom border
    for m in range(BLOCKS):
        n = BLOCKS - 1
        for x in range(m * SCALE_COEF, (m + 1) * SCALE_COEF):
            for y in range(n * SCALE_COEF, (n + 1) * SCALE_COEF):
                pixelsOut[x, y] = pixelsIn[m, n]

    # Fill right border
    for n in range(BLOCKS):
        m = BLOCKS - 1
        for x in range(m * SCALE_COEF, (m + 1) * SCALE_COEF):
            for y in range(n * SCALE_COEF, (n + 1) * SCALE_COEF):
                pixelsOut[x, y] = pixelsIn[m, n]

    return imgOut


def injectMessage(imgIn: Image.Image, messageBits: tuple) -> tuple:
    imgOut = imgIn.copy()
    pixelsIn = imgIn.load()
    pixelsOut = imgOut.load()

    if pixelsIn is None or pixelsOut is None:
        raise BaseException("pixel arrays are none")

    # positions = []

    messageBitsIndex = 0
    # Going by blocks
    for x in range(0, imgOut.size[0] - SCALE_COEF * 2, SCALE_COEF):
        for y in range(0, imgOut.size[1] - SCALE_COEF * 2, SCALE_COEF):
            bitCounts = tuple(
                int(
                    np.log2(
                        max(np.abs(pixelsOut[x + x_i, y + y_i] - pixelsOut[x, y]), 1)
                    )
                )
                for y_i in range(SCALE_COEF)
                for x_i in range(SCALE_COEF)
            )
            for y_i in range(SCALE_COEF):
                for x_i in range(SCALE_COEF):
                    messageBitsNextIndex = (
                        messageBitsIndex + bitCounts[x_i + y_i * SCALE_COEF]
                    )
                    val = sum(
                        el << index
                        for index, el in enumerate(
                            reversed(
                                messageBits[messageBitsIndex:messageBitsNextIndex]
                            )
                        )
                    )
                    # if bitCounts[x_i + y_i * SCALE_COEF] > 0:
                    #     positions.append(tuple([x + x_i, y + y_i, val]))
                    pixelsOut[x + x_i, y + y_i] += val

                    if messageBitsNextIndex >= len(messageBits):
                        break
                    messageBitsIndex = messageBitsNextIndex
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
    return imgOut, messageBits


def extractMessage(imgIn: Image.Image, messageBitLen: int) -> tuple:
    pixelsIn = imgIn.load()
    if pixelsIn is None:
        raise BaseException("pixels array is none")
    messageBits = []
    # positions = []

    for x in range(0, imgIn.size[0] - SCALE_COEF * 2, SCALE_COEF):
        for y in range(0, imgIn.size[1] - SCALE_COEF * 2, SCALE_COEF):
            vals = (
                0,
                pixelsIn[x + 1, y]
                - (pixelsIn[x, y] + pixelsIn[x + SCALE_COEF, y]) // SCALE_COEF,
                pixelsIn[x, y + 1]
                - (pixelsIn[x, y] + pixelsIn[x, y + SCALE_COEF]) // SCALE_COEF,
                pixelsIn[x + 1, y + 1]
                - (
                    SCALE_COEF * pixelsIn[x, y]
                    + (pixelsIn[x + SCALE_COEF, y] + pixelsIn[x, y + SCALE_COEF])
                    // SCALE_COEF
                )
                // (SCALE_COEF + 1),
            )
            bitCounts = tuple(
                int(
                    np.log2(
                        max(
                            np.abs(
                                pixelsIn[x + x_i, y + y_i]
                                - vals[x_i + y_i * SCALE_COEF]
                                - pixelsIn[x, y]
                            ),
                            1,
                        )
                    )
                )
                for y_i in range(SCALE_COEF)
                for x_i in range(SCALE_COEF)
            )
            vals = tuple(
                [int(i) for i in f"{val:0{bitCounts[index]}b}" if i.isdigit()]
                if bitCounts[index] > 0
                else []
                for index, val in enumerate(vals)
            )
            # for y_i in range(SCALE_COEF):
            #     for x_i in range(SCALE_COEF):
            #         if bitCounts[x_i + y_i * SCALE_COEF] > 0:
            #             positions.append(
            #                 tuple([x + x_i, y + y_i, vals[x_i + y_i * SCALE_COEF]])
            #             )
            for val in vals:
                messageBits += val
                # messageBits += (
                #     val[min(0, messageBitLen - len(messageBits)) :: -1]
                # )[::-1]
                if len(messageBits) >= messageBitLen:
                    diff = len(messageBits) - messageBitLen
                    # print(diff)
                    # vals = [x for x in vals if len(x) > 0]
                    messageBits = (
                        messageBits[: len(messageBits) - len(val)]
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

    return tuple(messageBits)


def getCapacity(imgIn: Image.Image):
    pixelsIn = imgIn.load()
    if pixelsIn is None:
        raise BaseException("pixelsIn is none")
    capacity = 0
    for x in range(0, imgIn.size[0] - SCALE_COEF, SCALE_COEF):
        for y in range(0, imgIn.size[1] - SCALE_COEF, SCALE_COEF):
            bitCounts = tuple(
                int(
                    np.log2(
                        max(np.abs(pixelsIn[x + x_i, y + y_i] - pixelsIn[x, y]), 1)
                    )
                )
                for y_i in range(SCALE_COEF)
                for x_i in range(SCALE_COEF)
            )
            capacity += sum(bitCounts)

    return (capacity, capacity / (imgIn.size[0] * imgIn.size[1]))


def getPSNR(imgClean: Image.Image, imgNoise: Image.Image):
    pixelsClean = imgClean.load()
    pixelsNoise = imgNoise.load()

    if pixelsClean is None or pixelsNoise is None:
        raise BaseException("pixels arrays are none")

    MSE = (
        1
        / (imgClean.size[0] * imgClean.size[1])
        * sum(
            (pixelsClean[x, y] - pixelsNoise[x, y]) ** 2
            for x in range(imgClean.size[0])
            for y in range(imgClean.size[1])
        )
    )
    return 10 * np.log10(255**2 / MSE)


def drawPlot(x, y, xlabel, ylabel):
    a = np.arange(len(x))
    plt.ion()
    fig, ax = plt.subplots(layout="constrained")
    ax.plot(a, y, "-^")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.xaxis.set_ticks(a)
    ax.xaxis.set_ticklabels(x)
    ax.grid(axis="y")
    fig.show()
