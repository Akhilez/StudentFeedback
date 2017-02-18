__author__ = 'Akhil'

from analytics.libs import db_helper


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
    drilldown = []
    def __init__(self, category, year, branch, sub, subsub):
        self.category = category
        self.year = year
        self.branch = branch
        self.sub = sub
        self.subsub = subsub
        self.s_no = 0
        self.title = "Title"
        self.subtitle = "click a bar for more info."
        self.type = "column" # 'column' "pie" , bar, scatter, line
        self.y_title = "Performance"
        Graph.drilldown = []
        self.series = self.get_series()


    def get_series(self):
        itr = 0
        series = None

        if self.category == 'class' or self.category == '':
            if len(self.year) == 0:
                # By Class table
                series = Series('All Years', 'all_years')
                self.title = 'All Years'
                series.bars = self.get_all_years_bars()
                itr = 1
            elif self.year == 'all_branches':
                # By Class all years all branches
                series = Series('All Years, Branches', 'all_branches')
                itr = 2
            elif self.year == 'all_sections':
                # By Class all years all branches all sections
                series = Series('All Years, Branches, Sections', 'all_sections')
                itr = 3

        elif self.category == 'fac':
            if len(self.subsub) == 0:
                # By Faculty table
                series = Series('All Faculty', 'all_faculty')
                itr = 4
            else:
                # selected faculty - subsub
                series = Series(self.subsub, self.subsub)
                itr = 5

        elif self.category == 'stu':
            if len(self.branch) == 0:
                # All subjects table
                series = Series('All Subjects', 'all_subjects')
                itr = 6
            else:
                # Selected subject graph - year, branch
                series = Series(self.year+'-'+self.branch, self.year+'-'+self.branch)
                itr = 7
        self.s_no = itr

        Graph.drilldown = [Graph.drilldown[x] for x in range(1, len(Graph.drilldown))]
        return series


    def get_all_years_bars(self):
        bars = []
        years = db_helper.get_years()

        for i in range(len(years)):
            bars.append(Bar(years[i], db_helper.get_year_value(years[i]), self.build_class_branch_series(years[i])))

        return bars



    def build_class_branch_series(self, year):
        series = Series(year, year)
        branches = db_helper.get_branches(year)
        bars = []

        for i in range(len(branches)):
            bars.append(
                Bar(
                    branches[i],
                    db_helper.get_branch_value(year, branches[i]),
                    self.build_section_series(year, branches[i])
                )
            )
        series.bars = bars
        return series

    def build_section_series(self, year, branch):
        series = Series(year+' '+branch, year+' '+branch)
        sections = db_helper.get_sections(year, branch)
        bars = []

        for i in range(len(sections)):
            bars.append(Bar(
                sections[i],
                db_helper.get_section_value(year, branch, sections[i]),
                self.build_faculty_series(year, branch, sections[i])
            ))

        series.bars = bars
        return series

    def build_faculty_series(self, year, branch, section):
        series = Series(year+' '+branch+' '+section, year+' '+branch+' '+section)
        faculty = db_helper.get_faculty(year, branch, section)
        bars = []
        for i in range(len(faculty)):
            cfss = db_helper.get_cfs(faculty[i], year, branch, section)
            for cfs in cfss:
                bars.append(Bar(
                    faculty[i]+' ('+cfs.subject_id.name+')',
                    db_helper.get_cfs_value(cfs),
                    'null'
                ))
        series.bars = bars
        return series