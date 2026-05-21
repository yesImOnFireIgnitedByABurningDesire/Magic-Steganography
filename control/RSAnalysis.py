import PIL.Image
import numpy


class RSAnalysis:
    ANALYSIS_COLOR_GRAYSCALE = -1
    ANALYSIS_COLOR_RED = 0
    ANALYSIS_COLOR_GREEN = 1
    ANALYSIS_COLOR_BLUE = 2

    def __init__(self, m: int, n: int):
        self.__mMask = [[0] * (m * n), [0] * (m * n)]

        k: int = 0
        for i in range(n):
            for j in range(m):
                if ((j % 2) == 0 and (i % 2) == 0) or ((j % 2) == 1 and (i % 2) == 1):
                    self.__mMask[0][k] = 1
                    self.__mMask[1][k] = 0
                else:
                    self.__mMask[0][k] = 0
                    self.__mMask[1][k] = 1
                k += 1

        self.__mM = m
        self.__mN = n

    # colorfull images are not supported currently
    # def analyze(self, image: Image.Image, color: int, overlap: bool) -> list[float]:
    def analyze(
        self,
        image: PIL.Image.Image,
        color: int = ANALYSIS_COLOR_GRAYSCALE,
        overlap: bool = True,
    ) -> bool:
        imgx: int = image.width
        imgy: int = image.height

        startx: int = 0
        starty: int = 0
        block: list[int] = [0] * (self.__mM * self.__mN)

        numregular: float = 0
        numsingular: float = 0
        numnegreg: float = 0
        numnegsing: float = 0
        numunusable: float = 0
        numnegunusable: float = 0
        variationB: float
        variationP: float
        variationN: float

        pixels = image.load()
        if pixels is None:
            raise BaseException("pixels is none")

        while startx < imgx and starty < imgy:
            for m in range(2):
                k: int = 0
                for i in range(self.__mN):
                    for j in range(self.__mM):
                        block[k] = pixels[startx + j, starty + i]
                        k += 1

                variationB = self.__getVariation(block, color)

                block = self.__flipBlock(block, self.__mMask[m])
                variationP = self.__getVariation(block, color)
                block = self.__flipBlock(block, self.__mMask[m])

                self.__mMask[m] = self.__invertMask(self.__mMask[m])
                variationN = self.__getNegativeVariation(block, color, self.__mMask[m])
                self.__mMask[m] = self.__invertMask(self.__mMask[m])

                if variationP > variationB:
                    numregular += 1
                if variationP < variationB:
                    numsingular += 1
                if variationP == variationB:
                    numunusable += 1

                if variationN > variationB:
                    numnegreg += 1
                if variationN < variationB:
                    numnegsing += 1
                if variationN == variationB:
                    numnegunusable += 1

            if overlap:
                startx += 1
            else:
                startx += self.__mM

            if startx >= (imgx - 1):
                startx = 0
                if overlap:
                    starty += 1
                else:
                    starty += self.__mN
            if starty >= (imgy - 1):
                break
        totalgroups: float = numregular + numsingular + numunusable
        allpixels: list[float] = self.__getAllPixelFlips(image, color, overlap)
        x: float = self.__getX(
            numregular,
            numnegreg,
            allpixels[0],
            allpixels[2],
            numsingular,
            numnegsing,
            allpixels[1],
            allpixels[3],
        )

        epf: float
        ml: float
        if 2 * (x - 1) == 0:
            epf = 0
        else:
            epf = abs(x / (2 * (x - 1)))

        if x - 0.5 == 0:
            ml = 0
        else:
            ml = abs(x / (x - 0.5))

        results: list[float] = [0] * 28

        results[0] = numregular
        results[1] = numsingular
        results[2] = numnegreg
        results[3] = numnegsing
        results[4] = abs(numregular - numnegreg)
        results[5] = abs(numsingular - numnegsing)
        results[6] = (numregular / totalgroups) * 100
        results[7] = (numsingular / totalgroups) * 100
        results[8] = (numnegreg / totalgroups) * 100
        results[9] = (numnegsing / totalgroups) * 100
        results[10] = (results[4] / totalgroups) * 100
        results[11] = (results[5] / totalgroups) * 100

        results[12] = allpixels[0]
        results[13] = allpixels[1]
        results[14] = allpixels[2]
        results[15] = allpixels[3]
        results[16] = abs(allpixels[0] - allpixels[1])
        results[17] = abs(allpixels[2] - allpixels[3])
        results[18] = (allpixels[0] / totalgroups) * 100
        results[19] = (allpixels[1] / totalgroups) * 100
        results[20] = (allpixels[2] / totalgroups) * 100
        results[21] = (allpixels[3] / totalgroups) * 100
        results[22] = (results[16] / totalgroups) * 100
        results[23] = (results[17] / totalgroups) * 100

        results[24] = totalgroups
        results[25] = epf
        results[26] = ml
        results[27] = ((imgx * imgy * 3) * ml) / 8

        return ml > 0.01

    def __getX(
        self,
        r: float,
        rm: float,
        r1: float,
        rm1: float,
        s: float,
        sm: float,
        s1: float,
        sm1: float,
    ) -> float:
        x: float = 0

        dzero: float = r - s
        dminuszero: float = rm - sm
        done: float = r1 - s1
        dminusone: float = rm1 - sm1

        a: float = 2 * (done + dzero)
        b: float = dminuszero - dminusone - done - (3 * dzero)
        c: float = dzero - dminuszero

        if a == 0:
            x = c / b

        discriminant: float = b * b - (4 * a * c)

        if discriminant >= 0:
            rootpos: float = ((-1 * b) + numpy.sqrt(discriminant)) / (2 * a)
            rootneg: float = ((-1 * b) - numpy.sqrt(discriminant)) / (2 * a)

            if numpy.abs(rootpos) <= numpy.abs(rootneg):
                x = rootpos
            else:
                x = rootneg

        else:
            cr = (rm - r) / (r1 - r + rm - rm1)
            cs = (sm - s) / (s1 - s + sm - sm1)
            x = (cr + cs) / 2

        if x == 0:
            ar = ((rm1 - r1 + r - rm) + (rm - r) / x) / (x - 1)
            as_ = ((sm1 - s1 + s - sm) + (sm - s) / x) / (x - 1)
            if as_ > 0 or ar < 0:
                cr = (rm - r) / (r1 - r + rm - rm1)
                cs = (sm - s) / (s1 - s + sm - sm1)
                x = (cr + cs) / 2

        return x

    def __getAllPixelFlips(
        self, image: PIL.Image.Image, color: int, overlap: bool
    ) -> list[float]:
        allmask: list[int] = [1] * (self.__mM * self.__mN)

        imgx: int = image.width
        imgy: int = image.height

        startx: int = 0
        starty: int = 0
        block: list[int] = [0] * (self.__mM * self.__mN)

        numregular: float = 0
        numsingular: float = 0
        numnegreg: float = 0
        numnegsing: float = 0
        numunusable: float = 0
        numnegunusable: float = 0
        variationB: float
        variationP: float
        variationN: float

        pixels = image.load()
        if pixels is None:
            raise BaseException("pixels is none")

        while startx < imgx and starty < imgy:
            for m in range(2):
                k: int = 0
                for i in range(self.__mN):
                    for j in range(self.__mM):
                        block[k] = pixels[startx + j, starty + i]
                        k += 1

                block = self.__flipBlock(block, allmask)

                variationB = self.__getVariation(block, color)

                block = self.__flipBlock(block, self.__mMask[m])
                variationP = self.__getVariation(block, color)
                block = self.__flipBlock(block, self.__mMask[m])

                self.__mMask[m] = self.__invertMask(self.__mMask[m])
                variationN = self.__getNegativeVariation(block, color, self.__mMask[m])
                self.__mMask[m] = self.__invertMask(self.__mMask[m])

                if variationP > variationB:
                    numregular += 1
                if variationP < variationB:
                    numsingular += 1
                if variationP == variationB:
                    numunusable += 1

                if variationN > variationB:
                    numnegreg += 1
                if variationN < variationB:
                    numnegsing += 1
                if variationN == variationB:
                    numnegunusable += 1

            if overlap:
                startx += 1
            else:
                startx += self.__mM

            if startx >= (imgx - 1):
                startx = 0
                if overlap:
                    starty += 1
                else:
                    starty += self.__mN
            if starty >= (imgy - 1):
                break

        results: list[float] = [0] * 4

        results[0] = numregular
        results[1] = numsingular
        results[2] = numnegreg
        results[3] = numnegsing

        return results

    @staticmethod
    def getResultNames() -> tuple[str, ...]:
        return (
            "Number of regular groups (positive)",
            "Number of singular groups (positive)",
            "Number of regular groups (negative)",
            "Number of singular groups (negative)",
            "Difference for regular groups",
            "Difference for singular groups",
            "Percentage of regular groups (positive)",
            "Percentage of singular groups (positive)",
            "Percentage of regular groups (negative)",
            "Percentage of singular groups (negative)",
            "Difference for regular groups %",
            "Difference for singular groups %",
            "Number of regular groups (positive for all flipped)",
            "Number of singular groups (positive for all flipped)",
            "Number of regular groups (negative for all flipped)",
            "Number of singular groups (negative for all flipped)",
            "Difference for regular groups (all flipped)",
            "Difference for singular groups (all flipped)",
            "Percentage of regular groups (positive for all flipped)",
            "Percentage of singular groups (positive for all flipped)",
            "Percentage of regular groups (negative for all flipped)",
            "Percentage of singular groups (negative for all flipped)",
            "Difference for regular groups (all flipped) %",
            "Difference for singular groups (all flipped) %",
            "Total number of groups",
            "Estimated percent of flipped pixels",
            "Estimated message length (in percent of pixels)(p)",
            "Estimated message length (in bytes)",
        )

    def __getVariation(self, block: list[int], color: int) -> float:
        var: float = 0
        color1: int
        color2: int
        for i in range(0, len(block), 4):
            color1 = self.__getPixelColor(block[0 + i], color)
            color2 = self.__getPixelColor(block[1 + i], color)
            var += numpy.abs(color1 - color2)
            color1 = self.__getPixelColor(block[3 + i], color)
            color2 = self.__getPixelColor(block[2 + i], color)
            var += numpy.abs(color1 - color2)
            color1 = self.__getPixelColor(block[1 + i], color)
            color2 = self.__getPixelColor(block[3 + i], color)
            var += numpy.abs(color1 - color2)
            color1 = self.__getPixelColor(block[2 + i], color)
            color2 = self.__getPixelColor(block[0 + i], color)
            var += numpy.abs(color1 - color2)
        return var

    def __getNegativeVariation(
        self, block: list[int], color: int, mask: list[int]
    ) -> float:
        var: float = 0
        color1: int
        color2: int
        for i in range(0, len(block), 4):
            color1 = self.__getPixelColor(block[0 + i], color)
            color2 = self.__getPixelColor(block[1 + i], color)
            if mask[0 + i] == -1:
                color1 = self.__invertLSB(color1)
            if mask[1 + i] == -1:
                color2 = self.__invertLSB(color2)
            var += numpy.abs(color1 - color2)

            color1 = self.__getPixelColor(block[1 + i], color)
            color2 = self.__getPixelColor(block[3 + i], color)
            if mask[1 + i] == -1:
                color1 = self.__invertLSB(color1)
            if mask[3 + i] == -1:
                color2 = self.__invertLSB(color2)
            var += numpy.abs(color1 - color2)

            color1 = self.__getPixelColor(block[3 + i], color)
            color2 = self.__getPixelColor(block[2 + i], color)
            if mask[3 + i] == -1:
                color1 = self.__invertLSB(color1)
            if mask[2 + i] == -1:
                color2 = self.__invertLSB(color2)
            var += numpy.abs(color1 - color2)

            color1 = self.__getPixelColor(block[2 + i], color)
            color2 = self.__getPixelColor(block[0 + i], color)
            if mask[2 + i] == -1:
                color1 = self.__invertLSB(color1)
            if mask[0 + i] == -1:
                color2 = self.__invertLSB(color2)
            var += numpy.abs(color1 - color2)
        return var

    def __getPixelColor(self, pixel: int, color: int) -> int:
        return pixel

    def __flipBlock(self, block: list[int], mask: list[int]) -> list[int]:
        for i in range(len(block)):
            if mask[i] == 1:
                block[i] = self.__negateLSB(block[i])
            elif mask[i] == -1:
                block[i] = self.__invertLSB(block[i])
        return block

    def __negateLSB(self, abyte: int) -> int:
        temp = abyte & 0xFE
        if temp == abyte:
            return abyte | 0x1
        else:
            return temp

    def __invertLSB(self, abyte: int) -> int:
        if abyte == 255:
            return 256
        if abyte == 256:
            return 255
        return self.__negateLSB(abyte + 1) - 1

    def __invertMask(self, mask: list[int]) -> list[int]:
        return [x * -1 for x in mask]
