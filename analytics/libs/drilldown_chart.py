__author__ = 'Akhil'


class Series:
    def __init__(self, name, series_id):
        self.name = name
        self.id = series_id
        self.bars = []
        Graphable.drilldown.append(self)
    def __str__(self):
        return str(self.id)


class Bar:
    def __init__(self, name, value, drilldown):
        self.name = name
        self.value = value
        self.drilldown = drilldown


class Graphable:
    types = {'column': 'column', 'bar': 'bar', 'pie': 'pie', 'line': 'line', 'scatter': 'scatter'}
    height_per_bar = 100
    drilldown = []


    def __init__(self, category, year, branch, sub, subsub, graph_type='null'):
        self.category = category
        self.year = year
        self.branch = branch
        self.sub = sub
        self.subsub = subsub
        self.s_no = 0
        self.height = 500
        self.width = 'null'
        self.title = "Title"
        self.subtitle = "click a bar for more info."
        self.type = graph_type # 'column' "pie" , bar, scatter, line
        self.y_title = "Performance"
        Graphable.drilldown = []
        self.series = self.get_series()

    def get_series(self):
        series = Series('Title', 'id')
        bars = []
        names = ['a', 'b', 'c']
        values = [1, 2, 3]
        for i in range(len(names)):
            bars.append(
                Bar(
                    names[i],
                    values[i], # get the value for the bar
                    Series('Apple', 'Apple') # get a series for drilldown of the bar or leave 'null' if no drilldown
                )
            )
        series.bars = bars
        return series