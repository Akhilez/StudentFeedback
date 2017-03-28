from analytics.libs import db_helper
from analytics.libs.db_helper import selected_questions
from analytics.libs.drilldown_chart import Series, Graphable, Bar

__author__ = 'Akhil'


class ClassSubGraph(Graphable):

    def __init__(self, faculty):
        self.faculty = faculty
        super().__init__()

    def get_series(self):
        self.title = "Classes"
        self.type = 'pie'
        return self.build_faculty_series()

    def build_faculty_series(self):
        cfs = db_helper.get_faculty_cfs(self.faculty)

        if self.type == Graphable.types['bar']:
            if self.height < len(cfs) * self.height_per_bar:
                self.height = len(cfs) * self.height_per_bar

        bars = []
        series = Series('Classes', 'class-sub', self)

        for i in range(len(cfs)):
            bars.append(Bar(
                str(cfs[i].class_id)+' ( '+cfs[i].subject_id.name+' )',
                db_helper.get_cfs_value(cfs[i]),
                self.build_faculty_ques_series(cfs[i])
            ))

        series.bars = bars
        return series.rev_sort()

    def build_faculty_ques_series(self, cfs):
        questions = db_helper.get_all_question_texts()

        bars = []
        series = Series(str(cfs), str(cfs), self)

        for i in range(len(questions)):
            if i in selected_questions:
                bars.append(Bar(
                    questions[i].question,
                    db_helper.get_question_value_for_cfs(cfs.cfs_id, questions[i]),
                    'null'
                ))

        series.bars = bars
        return series.rev_sort()
