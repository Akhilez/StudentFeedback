__author__ = 'Akhil'


class Series:
    def __init__(self, name, series_id, graph, color_by_point='true'):
        self.name = name
        self.id = series_id
        self.bars = []
        self.color_by_point = color_by_point
        graph.drilldown.append(self)

    def __str__(self):
        return str(self.id)

    def rev_sort(self):
        alist = self.bars
        for passnum in range(len(alist) - 1, 0, -1):
            for i in range(passnum):
                if alist[i].value < alist[i + 1].value:
                    temp = alist[i]
                    alist[i] = alist[i + 1]
                    alist[i + 1] = temp
        self.bars = alist
        return self


class Bar:
    def __init__(self, name, value, drilldown):
        self.name = name
        self.value = value
        self.drilldown = drilldown


class Graphable:
    types = ['column', 'bar', 'pie', 'line', 'scatter']
    height_per_bar = 50

    def __init__(self, graph_type='null'):
        self.s_no = 0
        self.height = 500
        self.width = 'null'
        self.title = "Title"
        self.subtitle = "click a bar for more info."
        self.type = graph_type  # 'column' "pie" , bar, scatter, line
        self.y_title = "Performance"
        self.drilldown = []
        self.series = self.get_series()
        del self.drilldown[0]

    def get_series(self):
        series = Series('Title', 'id', self)
        bars = []
        names = ['a', 'b', 'c']
        values = [1, 2, 3]
        for i in range(len(names)):
            bars.append(
                Bar(
                    names[i],
                    values[i],  # get the value for the bar
                    Series('Apple', 'Apple', self)
                    # get a series for drilldown of the bar or leave 'null' if no drilldown
                )
            )
        series.bars = bars
        return series.rev_sort()

        # def set_height(self, no_of_bars):
        #return sqrt(no_of_bars)