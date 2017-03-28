from analytics.libs.drilldown_chart import Graphable, Series, Bar

__author__ = 'Akhil'

from analytics.libs import db_helper
from analytics.libs.db_helper import Timeline


class Graph(Graphable):
    def __init__(self, category, year, branch, sub, subsub, graph_type='null'):
        self.category = category
        self.year = year
        self.branch = branch
        self.sub = sub
        self.subsub = subsub
        super().__init__(graph_type)


    def get_series(self):
        itr = 0
        series = None
        title = 'Title'

        if self.category == 'fac' or self.category == '':
            if len(self.subsub) == 0:
                # By Faculty table
                title = 'All Faculty'
                if self.type == 'null': self.type = Graph.types['bar']
                series = Series(title, 'all_faculty', self)
                series.bars = self.get_all_faculty_bars()
                itr = 4
            else:
                # selected faculty - subsub
                faculty_name = db_helper.get_faculty_name(self.subsub)
                title = faculty_name
                if self.type == 'null': self.type = Graph.types['bar']
                series = self.build_faculty_ques_series(faculty_name)
                itr = 5

        elif self.category == 'class':
            if len(self.year) == 0:
                # By Class table
                title = 'All Years'
                series = Series(title, 'all_years', self)
                series.bars = self.get_all_years_bars()
                itr = 1
            elif self.year == 'all_branches':
                # By Class all years all branches
                title = 'All Years, Branches'
                if self.type == 'null': self.type = Graph.types['bar']
                series = Series(title, 'all_branches', self)
                series.bars = self.get_all_branches_bars()
                itr = 2
            elif self.year == 'all_sections':
                # By Class all years all branches all sections
                title = 'All Years, Branches, Sections'
                if self.type == 'null': self.type = Graph.types['bar']
                series = Series(title, 'all_sections', self)
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
                title = self.year+'-'+self.branch
                series = Series(title, title, self)
                itr = 7
        self.s_no = itr
        self.title = title

        return series.rev_sort()

    def get_all_faculty_bars(self):
        bars = []
        all_faculty = db_helper.get_all_faculty()

        if self.type == Graph.types['bar']:
            self.height = len(all_faculty) * Graph.height_per_bar

        for i in range(len(all_faculty)):
            bars.append(Bar(
                all_faculty[i].name,
                db_helper.get_faculty_value(all_faculty[i]),
                self.build_faculty_ques_series(all_faculty[i].name)
            ))

        return bars

    def build_faculty_ques_series(self, faculty):
        questions = db_helper.get_all_question_texts()

        if self.type == Graphable.types['bar']:
            if self.height < len(questions) * Graph.height_per_bar:
                self.height = len(questions) * Graph.height_per_bar

        bars = []
        series = Series(faculty, faculty, self)

        for i in range(len(questions)):
            if i in Timeline.selected_questions:
                bars.append(Bar(
                    questions[i].question,
                    db_helper.get_question_value(faculty, questions[i]),
                    'null'
                ))

        series.bars = bars
        return series.rev_sort()

    def build_all_subjects_series(self):
        subjects = db_helper.get_all_subjects_all_years()

        if self.type == Graph.types['bar']:
            self.height = len(subjects) * Graph.height_per_bar

        bars = []
        title = 'All Subjects'
        series = Series(title, title, self)

        for i in range(len(subjects)):
            bars.append(Bar(
                subjects[i],
                db_helper.get_subject_value(subjects[i]),
                self.build_faculty_for_subject_series(subjects[i])
            ))

        series.bars = bars
        return series.rev_sort()

    def build_faculty_for_subject_series(self, subject):
        faculty = db_helper.get_faculty_for_subject(subject)

        bars = []
        series = Series(subject, subject, self)

        for i in range(len(faculty)):
            bars.append(Bar(
                faculty[i].name,
                db_helper.get_faculty_value_for_subject(subject, faculty[i]),
                'null'
            ))

        series.bars = bars
        return series.rev_sort()


    def get_all_years_bars(self):
        bars = []
        years = db_helper.get_years()

        for i in range(len(years)):
            bars.append(Bar(years[i], db_helper.get_year_value(years[i]), self.build_class_branch_series(years[i])))

        return bars

    def build_class_branch_series(self, year):
        series = Series(year, year, self)
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
        return series.rev_sort()

    def build_section_series(self, year, branch):
        series = Series(year+' '+branch, year+' '+branch, self)
        sections = db_helper.get_sections(year, branch)
        bars = []

        for i in range(len(sections)):
            bars.append(Bar(
                sections[i],
                db_helper.get_section_value(year, branch, sections[i]),
                self.build_faculty_series(year, branch, sections[i])
            ))

        series.bars = bars
        return series.rev_sort()

    def build_faculty_series(self, year, branch, section):
        series = Series(year+' '+branch+' '+section, year+' '+branch+' '+section, self)
        faculty = db_helper.get_faculty(year, branch, section)
        bars = []
        for i in range(len(faculty)):
            cfss = db_helper.get_cfs(faculty[i].name, year, branch, section)
            for cfs in cfss:
                bars.append(Bar(
                    faculty[i].name+' ('+cfs.subject_id.name+')',
                    db_helper.get_cfs_value(cfs),
                    self.build_faculty_ques_series(faculty[i].name)
                    #'null'
                ))
        series.bars = bars
        return series.rev_sort()

    def get_all_branches_bars(self):
        bars = []
        all_years_branches = db_helper.get_all_year_branches()

        if self.type == 'bar':
            self.height = self.height_per_bar * len(all_years_branches)/2

        for each in all_years_branches:
            bars.append(Bar(
                db_helper.formatter[str(each[0])]+' '+each[1],
                db_helper.get_branch_value(db_helper.formatter[str(each[0])], each[1]),
                'null'
            ))
        return bars

    def get_all_sections_bars(self):
        bars = []
        all_years_sections = db_helper.get_all_year_sections()

        if self.type == 'bar':
            self.height = self.height_per_bar * len(all_years_sections)

        for each in all_years_sections:
            bars.append(Bar(
                db_helper.formatter[str(each[0])]+' '+each[1]+' '+each[2],
                db_helper.get_section_value(db_helper.formatter[str(each[0])], each[1], each[2]),
                'null'
            ))
        return bars





    






















