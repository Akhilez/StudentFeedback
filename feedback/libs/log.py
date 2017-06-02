__author__ = 'Akhil'


def write(string):
    file = open("logger", "a")
    file.write(str(string)+"\n")
    file.close()