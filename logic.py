from PIL import Image
import atexit
import os
import numpy as np
from matplotlib import pyplot as plt

TEMP_IMAGE_PATH = "~temp.bmp"
TEMP_IMAGE_FORMAT = "bmp"


def atexit_handler():
    os.remove(TEMP_IMAGE_PATH)


atexit.register(atexit_handler)


def attackImage(path: str, bit_index: int):
    imgIn = Image.open(path)
    img = Image.new("L", imgIn.size)
    pixelsIn = imgIn.load()
    pixels = img.load()
    for x in range(img.size[0]):
        for y in range(img.size[1]):
            pixels[x, y] = 255 * (pixelsIn[x, y] & (1 << bit_index))
    img.save(TEMP_IMAGE_PATH, TEMP_IMAGE_FORMAT)


def injectMessage(path: str, messageBits: tuple) -> tuple:
    imgIn = Image.open(path)
    img = imgIn.copy()
    pixelsIn = imgIn.load()
    pixels = img.load()

    msgIndex = 0

    def indexIn():
        return msgIndex < len(messageBits) - 1

    def mi():
        try:
            return (messageBits[msgIndex] << 1) | messageBits[msgIndex + 1]
        except:
            return 0b100

    for x in range(img.size[0]):
        for y in range(img.size[1]):
            if not indexIn():
                break

            byte = pixelsIn[x, y]
            clp = (byte & 0b11000000) >> 6
            cmp = (byte & 0b01100000) >> 5
            crp = (byte & 0b00110000) >> 4

            if mi() == clp:
                byte |= 1 << 2
                msgIndex += 2
            else:
                byte &= ~(1 << 2)
            if mi() == cmp:
                byte |= 1 << 1
                msgIndex += 2
            else:
                byte &= ~(1 << 1)
            if mi() == crp:
                byte |= 1
                msgIndex += 2
            else:
                byte &= ~(1)

            pixels[x, y] = byte
        else:
            continue
        break

    img.save(TEMP_IMAGE_PATH, TEMP_IMAGE_FORMAT)
    return messageBits


def extractMessage(path: str, messageBitLen: int) -> tuple:
    imgIn = Image.open(path)
    pixelsIn = imgIn.load()
    msgIndex = 0
    messageBits = [0] * messageBitLen
    foundLen = 0

    def indexIn():
        return msgIndex < len(messageBits) - 1

    for x in range(imgIn.size[0]):
        for y in range(imgIn.size[1]):
            if not indexIn():
                break

            byte = pixelsIn[x, y]
            clp = (byte & 0b11000000) >> 6
            cmp = (byte & 0b01100000) >> 5
            crp = (byte & 0b00110000) >> 4

            if byte & (1 << 2):
                messageBits[msgIndex] = clp >> 1
                messageBits[msgIndex + 1] = clp & 1
                msgIndex += 2
                if not indexIn():
                    break

            if byte & (1 << 1):
                messageBits[msgIndex] = cmp >> 1
                messageBits[msgIndex + 1] = cmp & 1
                msgIndex += 2
                if not indexIn():
                    break

            if byte & (1):
                messageBits[msgIndex] = crp >> 1
                messageBits[msgIndex + 1] = crp & 1
                msgIndex += 2
        else:
            continue
        break

    return tuple(messageBits[:msgIndex])


def getPSNR(clean: str, noise: str):
    imgClean = Image.open(clean)
    imgNoise = Image.open(noise)

    pixelsClean = imgClean.load()
    pixelsNoise = imgNoise.load()

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


def copyImage(src: str, dest: str, format: str = TEMP_IMAGE_FORMAT):
    Image.open(src).save(dest, format)
