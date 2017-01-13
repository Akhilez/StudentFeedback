from datetime import datetime
import time
from django.test import TestCase
fmt = '%Y-%m-%d %H:%M:%S'
d1 = datetime.strptime('2017-01-14 00:00:00', fmt)
tdiff = (datetime.now() - d1).total_seconds()/60 > 5
print(tdiff)