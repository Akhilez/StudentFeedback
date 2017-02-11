__author__ = 'Akhil'


from analytics.libs import db_helper


def getTree():
    years = db_helper.get_years()
    year_objs = []
    for year in years:
        year_objs.append(get_year(year))

    return year_objs

def get_year(year):
    year_obj = Year(year)
    branches = db_helper.get_branches(year)
    for branch in branches:
        year_obj.add_branch(get_branch(year, branch))

    return year_obj

def get_branch(year, branch):
    branch_obj = Branch(branch)

    sections = db_helper.get_sections(year, branch)
    for section in sections:
        branch_obj.add_section(get_section(year, branch, section))

    subjects = db_helper.get_subjects(year, branch)
    for subject in subjects:
        branch_obj.add_subject(get_subject(subject))

    return branch_obj

def get_section(year, branch, section):
    section_obj = Section(section)

    facultys = db_helper.get_faculty(year, branch, section)
    for faculty in facultys:
        section_obj.add_faculty(faculty)

    return section_obj

def get_subject(subject):
    return Subject(subject)




class Year:
    def __init__(self, name):
        self.name = name
        self.branches = []
    def add_branch(self, branch):
        self.branches.append(branch)
    def get_branches(self):
        return self.branches
    def __str__(self):
        format = {'1': 'Ist year', '2': 'IInd year', '3': 'IIIrd year', '4': 'IVth year'}
        try:
            return format[self.name]
        except:
            return self.name


class Branch:
    def __init__(self, name):
        self.name = name
        self.sections = []
        self.subjects = []
    def add_section(self, section):
        self.sections.append(section)
    def add_subject(self, subject):
        self.subjects.append(subject)
    def get_sections(self):
        return self.sections
    def get_subjects(self):
        return self.subjects
    def __str__(self):
        return self.name


class Section:
    def __init__(self, name):
        self.name = name
        self.faculty = []
    def add_faculty(self, faculty):
        self.faculty.append(faculty)
    def get_faculty(self):
        return self.faculty
    def __str__(self):
        if self.name is None:
            return 'A'
        return self.name


class Faculty:
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return self.name


class Subject:
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return self.name
