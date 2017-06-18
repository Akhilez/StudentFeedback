__author__ = 'Ravi'

from analytics.libs import LOAdb_helper


class Series:
    def __init__(self, name, series_id):
        self.name = name
        self.id = series_id
        self.bars = []
        Graph.drilldown.append(self)

    def __str__(self):
        return str(self.id)


class Bar:
    def __init__(self, name, value, drilldown):
        self.name = name
        self.value = value
        self.drilldown = drilldown


class Graph:
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
        self.type = graph_type  # 'column' "pie" , bar, scatter, line
        self.y_title = "Performance"
        Graph.drilldown = []
        self.series = self.get_series()

    def get_series(self):  # arey, till this method get_series, I'll
        itr = 0
        series = None
        title = 'Title'

        if self.category == 'class' or self.category == '':
            if len(self.year) == 0:
                # By Class table
                title = 'All Years'
                series = Series(title, 'all_years')
                series.bars = self.get_all_years_bars()
                itr = 1
            elif self.year == 'all_branches':
                # By Class all years all branches
                title = 'All Years, Branches'
                if self.type == 'null': self.type = Graph.types['bar']
                series = Series(title, 'all_branches')
                series.bars = self.get_all_branches_bars()
                itr = 2
            elif self.year == 'all_sections':
                # By Class all years all branches all sections
                title = 'All Years, Branches, Sections'
                if self.type == 'null': self.type = Graph.types['bar']
                series = Series(title, 'all_sections')
                series.bars = self.get_all_sections_bars()
                itr = 3



        elif self.category == 'stu':
            if len(self.branch) == 0:
                # All subjects table
                title = 'All Subjects'
                if self.type == 'null': self.type = Graph.types['bar']
                series = self.build_all_subjects_series()
                itr = 6
            else:
                # Selected subject graph - year, branch
                title = self.year + '-' + self.branch
                series = Series(title, title)
                itr = 7
        self.s_no = itr
        self.title = title

        Graph.drilldown = [Graph.drilldown[x] for x in range(1, len(Graph.drilldown))]
        return series


    def build_all_subjects_series(self):  # subject graphs
        subjects = LOAdb_helper.get_subjects_in_feedback()

        if self.type == Graph.types['bar']:
            self.height = len(subjects) * Graph.height_per_bar

        bars = []
        title = 'All Subjects'
        series = Series(title, title)

        for i in range(len(subjects)):
            bars.append(Bar(
                subjects[i],
                LOAdb_helper.get_subject_value(subjects[i]),
                self.build_sections_for_subject_series(subjects[i])
                #'null'
            ))

        series.bars = bars
        return series

    def build_sections_for_subject_series(self, subject):  # sections in subjects graph
        sections = LOAdb_helper.get_feedback_sections_subject(subject)

        bars = []
        series = Series(subject, subject)

        for i in range(len(sections)):
            bars.append(Bar(
                sections[i],  #my code
                LOAdb_helper.get_sections_value_for_subject(subject, sections[i]),
                'null'
            ))

        series.bars = bars
        return series


    def get_all_years_bars(self):
        bars = []
        years = LOAdb_helper.get_years()

        for i in range(len(years)):
            bars.append(Bar(
                years[i],  # name
                LOAdb_helper.get_year_value(years[i]),  # value
                self.build_class_branch_series(years[i])  # Where to go after click/drilldown
            ))

        return bars

    def build_class_branch_series(self, year):
        series = Series(year, year)
        branches = LOAdb_helper.get_branches(year)
        bars = []

        for i in range(len(branches)):
            bars.append(
                Bar(
                    branches[i],  # name of the branch
                    LOAdb_helper.get_branch_value(year, branches[i]),  #value of the branch
                    self.build_section_series(year, branches[i])  #drilldown to sections
                )
            )
        series.bars = bars
        return series

    def build_section_series(self, year, branch):
        series = Series(year + ' ' + branch, year + ' ' + branch)
        sections = LOAdb_helper.get_sections(year, branch)
        bars = []

        for i in range(len(sections)):
            bars.append(Bar(
                sections[i],  # section name
                LOAdb_helper.get_section_value(year, branch, sections[i]),  #section value
                self.get_all_subject_values(year, branch, sections[i])  #my code
                #'null'
            ))

        series.bars = bars
        return series


    def get_all_branches_bars(self):
        bars = []
        all_years_branches = LOAdb_helper.get_all_year_branches()
        for each in all_years_branches:
            bars.append(Bar(
                LOAdb_helper.formatter[str(each[0])] + ' ' + each[1],
                LOAdb_helper.get_branch_value(LOAdb_helper.formatter[str(each[0])], each[1]),
                'null'
            ))
        return bars

    def get_all_sections_bars(self):
        bars = []
        all_years_sections = LOAdb_helper.get_all_year_sections()
        for each in all_years_sections:
            bars.append(Bar(
                LOAdb_helper.formatter[str(each[0])] + ' ' + each[1] + ' ' + each[2],
                LOAdb_helper.get_section_value(LOAdb_helper.formatter[str(each[0])], each[1], each[2]),
                'null'
            ))
        return bars

    def get_all_subject_values(self, year, branch, section):  # my code
        series = Series(year + ' ' + branch + ' ' + section, year + ' ' + branch + ' ' + section)
        bars = []
        subject = LOAdb_helper.get_subjects(year, branch)
        bars = []
        for i in range(len(subject)):
            bars.append(Bar(
                subject[i],
                LOAdb_helper.get_subject_value(subject[i]),  #this is the one i should take care
                'null'
            ))
        series.bars = bars
        return series

