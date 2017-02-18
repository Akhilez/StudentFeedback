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
    column_type = 'column'
    bar_type = 'bar'
    pie_type = 'pie'
    scatter_type = 'scatter'
    line_type = 'line'
    drilldown = []
    def __init__(self, category, year, branch, sub, subsub):
        self.category = category
        self.year = year
        self.branch = branch
        self.sub = sub
        self.subsub = subsub
        self.s_no = 0
        self.height = 'null'
        self.width = 'null'
        self.title = "Title"
        self.subtitle = "click a bar for more info."
        self.type = "column" # 'column' "pie" , bar, scatter, line
        self.y_title = "Performance"
        Graph.drilldown = []
        self.series = self.get_series()


    def get_series(self):
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
                series = Series(title, 'all_branches')
                itr = 2
            elif self.year == 'all_sections':
                # By Class all years all branches all sections
                title = 'All Years, Branches, Sections'
                series = Series(title, 'all_sections')
                itr = 3

        elif self.category == 'fac':
            if len(self.subsub) == 0:
                # By Faculty table
                title = 'All Faculty'
                self.type = Graph.bar_type
                series = Series(title, 'all_faculty')
                series.bars = self.get_all_faculty_bars()
                itr = 4
            else:
                # selected faculty - subsub
                title = self.subsub
                series = Series(title, title)
                itr = 5

        elif self.category == 'stu':
            if len(self.branch) == 0:
                # All subjects table
                title = 'All Subjects'
                series = Series(title, 'all_subjects')
                itr = 6
            else:
                # Selected subject graph - year, branch
                title = self.year+'-'+self.branch
                series = Series(title, title)
                itr = 7
        self.s_no = itr
        self.title = title

        Graph.drilldown = [Graph.drilldown[x] for x in range(1, len(Graph.drilldown))]
        return series


    def get_all_faculty_bars(self):
        height = 0
        bars = []
        all_faculty = db_helper.get_all_faculty()

        for i in range(len(all_faculty)):
            height += 50
            bars.append(Bar(
                all_faculty[i],
                db_helper.get_faculty_value(all_faculty[i]),
                self.build_faculty_ques_series(all_faculty[i]))
            )
        self.height = height
        return bars

    def build_faculty_ques_series(self, faculty):
        return 'null'

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