from django.db.models import Max
from feedback.models import Config

__author__ = 'Akhil'


def get_session_length():
    try:
        duration = Config.objects.get(key="feedbackDuration").value
    except:
        Config.objects.create(key="feedbackDuration", value="45",
                              description="The maximum time a feedback can be conducted.")
        duration = 45
    return int(duration)


def get_max_subjects_each_page_loa():
    try:
        config = Config.objects.get(key="max_subs_loa").value
    except:
        Config.objects.create(key="max_subs_loa", value=3, description="Maximum no. of subjects in LOA ratings page")
        config = 3

    return int(config)


def get_max_cfs_each():
    try:
        config = Config.objects.get(key="max_cfs_each").value
    except:
        Config.objects.create(key="max_cfs_each", value=3, description="Maximum no. of faculty in faculty ratings page")
        config = 3

    return int(config)