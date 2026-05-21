import PIL.Image
import scipy.stats
import numpy


class ChiSquaredAnalysis:
    __MIN_BIN = 5
    __WALL = 0.5

    @staticmethod
    def analyze(image: PIL.Image.Image, block_size: int = 128) -> bool:
        pixels = image.load()
        if pixels is None:
            raise BaseException
        outs = []

        for x_max in range(0, image.width, block_size):
            for y_max in range(0, image.height, block_size):
                x_min = min(0, x_max - block_size)
                y_min = min(0, y_max - block_size)

                distribution_actual: list[int] = [0] * 8
                for x in range(x_min, x_max):
                    for y in range(y_min, y_max):
                        distribution_actual[pixels[x, y] & 0b111] += 1

                distribution_mean: list[int] = [0] * len(distribution_actual)
                for index in range(0, len(distribution_actual) - 1, 2):
                    mean = (
                        distribution_actual[index] + distribution_actual[index + 1]
                    ) / 2
                    if mean.is_integer():
                        distribution_mean[index] = distribution_mean[index + 1] = int(
                            mean
                        )
                    elif distribution_actual[index] < distribution_actual[index + 1]:
                        distribution_mean[index] = int(mean)
                        distribution_mean[index + 1] = int(mean) + 1
                    else:
                        distribution_mean[index] = int(mean) + 1
                        distribution_mean[index + 1] = int(mean)

                # print(distribution_actual)
                # print(distribution_mean)
                # combine bins
                index = 0
                ChiSquaredAnalysis.__MIN_BIN = numpy.average(distribution_actual)
                while index < len(distribution_actual):
                    if distribution_actual[index] < ChiSquaredAnalysis.__MIN_BIN:
                        val_sum = distribution_actual[index]
                        stop = index
                        for jindex in range(index + 1, len(distribution_actual)):
                            val_sum += distribution_actual[jindex]
                            if val_sum >= ChiSquaredAnalysis.__MIN_BIN:
                                stop = jindex
                                break
                        else:
                            stop = len(distribution_actual) - 1

                        distribution_actual[index : stop + 1] = [
                            sum(distribution_actual[index : stop + 1])
                        ]
                        distribution_mean[index : stop + 1] = [
                            sum(distribution_mean[index : stop + 1])
                        ]

                    index += 1
                if distribution_actual[-1] < ChiSquaredAnalysis.__MIN_BIN:
                    distribution_actual[-2:] = [sum(distribution_actual[-2:])]
                    distribution_mean[-2:] = [sum(distribution_mean[-2:])]
                del index

                for x in distribution_actual:
                    if x == 0:
                        break
                else:
                    if len(distribution_actual) == 2:
                        if distribution_actual[0] == 0 or distribution_actual[1] == 0:
                            outs.append(1)
                            continue

                    if len(distribution_actual) == 1:
                        outs.append(1)
                        continue

                    outs.append(
                        scipy.stats.chisquare(
                            f_obs=distribution_actual, f_exp=distribution_mean, ddof=1
                        )[1]
                    )
        # print(outs)
        # print(numpy.average(outs))
        # outs = [x for x in outs if x > 0.000001]
        # return numpy.average(outs) > 0.5
        return numpy.average(outs) < ChiSquaredAnalysis.__WALL
