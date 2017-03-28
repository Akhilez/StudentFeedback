from analytics.libs import db_helper
from analytics.libs.db_helper import Timeline
from analytics.libs.drilldown_chart import Graphable, Series, Bar
import math

__author__ = 'Akhil'


class FacultyGraph(Graphable):

    def __init__(self, faculty):
        self.faculty = faculty
        super().__init__()

    def get_series(self):
        self.title = "All Quesitons"
        self.type = 'bar'
        return self.build_faculty_ques_series()

    def build_faculty_ques_series(self):
        questions = db_helper.get_all_question_texts()

        bars = []
        series = Series(self.faculty, self.faculty, self)

        for i in range(len(questions)):
            if i in Timeline.selected_questions:
                bars.append(Bar(
                    questions[i].question,
                    db_helper.get_question_value(self.faculty, questions[i]),
                    'null'
                ))

        if self.type == 'bar':
            self.height = math.sqrt(len(bars)) * 5 * self.height_per_bar

        series.bars = bars
        series.color_by_point = 'false'
        return series.rev_sort()