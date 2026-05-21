import PIL.Image
import numpy
import scipy


class AUMPAnalysis:
    __WALL = 1

    @staticmethod
    def analyze(image: PIL.Image.Image, block_size: int, parameters: int) -> bool:
        pixels = numpy.array(image, dtype=numpy.float64)
        scipy.io.savemat("array.mat", {"X": pixels})
        try:
            return (
                AUMPAnalysis.__aump(pixels, block_size, parameters)
                > AUMPAnalysis.__WALL
            )
        except BaseException:
            return False

    @staticmethod
    def __aump(X, m, d):
        Xpred, _, w = AUMPAnalysis.__pred_aump(X, m, d)
        r = X - Xpred
        Xbar = X + 1 - 2 * (X % 2)
        beta = numpy.sum(w * (X - Xbar) * r)
        return beta

    @staticmethod
    def __pred_aump(X, m, d):
        sig_th = 1
        q = d + 1
        Kn = X.size // m
        Y = numpy.zeros((m, Kn))
        S = numpy.zeros_like(X)
        Xpred = numpy.zeros_like(X)

        x1 = numpy.linspace(1, m, m) / m
        H = numpy.vander(x1, q, increasing=True)

        for i in range(m):
            aux = X[:, i::m]
            Y[i, :] = aux.flatten()

        p = numpy.linalg.lstsq(H, Y, rcond=None)[0]
        Ypred = H @ p

        for i in range(m):
            Xpred[:, i::m] = Ypred[i, :].reshape(X[:, i::m].shape)

        sig2 = numpy.sum((Y - Ypred) ** 2, axis=0) / (m - q)
        sig2 = numpy.maximum(sig_th**2, sig2)

        Sy = numpy.ones((m, 1)) * sig2

        for i in range(m):
            S[:, i::m] = Sy[i, :].reshape(X[:, i::m].shape)

        s_n2 = Kn / numpy.sum(1.0 / sig2)
        w = numpy.sqrt(s_n2 / (Kn * (m - q))) / S

        return Xpred, S, w
