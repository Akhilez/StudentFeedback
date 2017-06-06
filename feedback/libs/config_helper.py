from django.db.models import Max
from feedback.models import Config, QSet

__author__ = 'Akhil'

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


def get_current_qset():
    """
    1. if qset not in config, go to 2, else go to 3
    2. get latest qset from qset table and add into config
    3. return current qset object
    :return: qset object
    """
    qset = None
    try:
        config = Config.objects.get(key="qset").value
        if config is not None:
            qset = QSet.objects.get(qset_id=config)
    except:
        try:
            qset = QSet.objects.get(qset_id=QSet.objects.all().aggregate(Max('qset_id')))
            config = Config.objects.create(key="qset", value=str(qset), description="default questions set for the feedback and analysis").value
        except:
            pass


    return qset