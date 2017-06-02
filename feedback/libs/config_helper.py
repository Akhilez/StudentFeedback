from feedback.models import Config

__author__ = 'Akhil'


def getStudentTimeout():
    try:
        timeInMin = Config.objects.get(key='studentTimeout')
        return int(timeInMin.value)
    except Exception:
        Config.objects.create(key='studentTimeout', value='5',
                              description="Expire the student login page after these many seconds")
        return 5


def get_session_length():
    try:
        duration = Config.objects.get(key="feedbackDuration").value
    except:
        Config.objects.create(key="feedbackDuration", value="45",
                              description="The maximum time a feedback can be conducted.")
        duration = 45
    return int(duration)


def getGracePeriod():
    try:
        gp = Config.objects.get(key="gracePeriod").value
    except:
        Config.objects.create(key="gracePeriod", value="5",
                              description="Enable stu login page voluntarily for this time.")
        gp = 5
    return int(gp)