from analytics.libs import db_helper
from analytics.libs.drilldown_chart import Series, Graphable, Bar

__author__ = 'Akhil'


class TimelineGraph(Graphable):
    def __init__(self, faculty):
        self.faculty = faculty
        super().__init__()

    def get_series(self):
        self.title = "TimeLine"
        self.type = 'line'
        return self.build_faculty_timeline_series()

    def build_faculty_timeline_series(self):
        """
        get faculty object
        get cfs objects from faculty
        get dates from feedback using cfs = relation
        1. get all the timelines of the faculty
        2. for each timeline, get all the ratings
        :return:
        """
        series = Series('Timeline', 'timeline', self)

        timelines = db_helper.get_all_timelines(self.faculty)

        bars = []

        for timeline in timelines:
            bars.append(
                Bar(
                    str(timeline.date),
                    sum(timeline.rating) / len(timeline.rating),
                    'null'
                )
            )

        series.bars = bars
        series.color_by_point = 'false'
        return series