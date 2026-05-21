import matplotlib
import matplotlib.patheffects
import matplotlib.pyplot
import numpy


class PlotBuilder:
    __COLORS = ("tab:blue", "tab:red", "tab:green")

    @staticmethod
    def build_plot(title: str, data):
        matplotlib.rcParams.update({"font.size": 14})
        # matplotlib.pyplot.ion()

        # xt, y = zip(*data.items())
        xt = data.keys()
        data = list(data.values())
        data = {k: [x[k] for x in data] for k in data[0].keys()}

        x = numpy.arange(len(xt))
        width = 0.25
        multiplier = 0

        fix, ax = matplotlib.pyplot.subplots(constrained_layout=True)

        for index, (attribute, measurement) in enumerate(data.items()):
            offset = width * multiplier
            rects = ax.bar(
                x + offset,
                measurement,
                width,
                label=attribute,
                color=PlotBuilder.__COLORS[index],
            )
            ax.bar_label(rects, padding=3)
            multiplier += 1
        for text in ax.texts:
            text.set_path_effects(
                [matplotlib.patheffects.withStroke(linewidth=4, foreground="w")]
            )

        ax.set_xticks(x + width, [str(x) for x in xt])
        ax.grid(axis="y")
        ax.legend()
        if fix.canvas.manager is not None:
            fix.canvas.manager.set_window_title(title)

        matplotlib.pyplot.show()
