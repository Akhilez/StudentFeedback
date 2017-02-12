__author__ = 'Akhil'


class Graph:
    def __init__(self, category, year, branch, sub, subsub):
        self.category = category
        self.year = year
        self.branch = branch
        self.sub = sub
        self.subsub = subsub
        self.s_no = self.get_s_no()
        self.title = "Title"
        self.subtitle = "Subtitle"
        self.type = "column" # "pie" , bar, scatter
        self.y_title = "Performance"
        self.series = None
        self.drilldown = None


    def build(self):
        """
        step1: get the x axis parameters
        step2: get the points for each x parameter
        step3: make title
        """

        x_axis = self.get_x_params()
        y_points = self.get_y_points()

        self.series = Series(self.year, self.year)

        for i in range(len(x_axis)):
            #self.chart.series.bars.append(Bar(x_axis[i], y_points[i]))
            self.series.bars.append(Bar(x_axis[i], y_points[i]))


    def get_x_params(self):
        return ['Akhil', 'Raj', 'Ravi']

    def get_y_points(self):
        return [1.5, 2.5, 4.25]

    def get_s_no(self):
        itr = 0
        if self.category == 'class':
            if len(self.year) == 0:
                # By Class table
                itr = 1
            elif len(self.branch) == 0:
                # all branches(sec, fac) in i year
                itr = 2
            elif len(self.sub) == 0:
                # all sections(fac) in i year, j branch
                itr = 3
            else:
                # all faculty in i year, j branch, k section
                itr = 4
        elif self.category == 'fac':
            if len(self.subsub) == 0:
                # By Faculty table
                itr = 5
            else:
                # selected faculty
                itr = 6
        elif self.category == 'stu':
            if len(self.year) == 0:
                itr = 7
            elif len(self.branch) == 0:
                itr = 8
            elif len(self.sub) == 0:
                itr = 9
            else:
                itr = 10
        return itr


class Series:
    def __init__(self, name, series_id):
        self.name = name
        self.id = series_id
        self.bars = []

class Drilldown:
    def __init__(self):
        self.series = []

class Bar:
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.drilldown = None