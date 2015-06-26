import os
import sys

sys.path.append('/home/bcpp/source/getresults-distribute')
sys.path.append('/home/bcpp/source/getresults-distribute/getresults_dst')
sys.path.append('/home/bcpp/.virtualenvs/django18/lib/python3.4/site-packages')

activate_env = os.path.join('/home/bcpp/.virtualenvs/django18/bin/activate_this.py')

with open(activate_env) as f:
    code = compile(f.read(), activate_env, 'exec')
    exec(code, dict(__file__=activate_env))

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "getresults_dst.settings")

os.environ['DJANGO_SETTINGS_MODULE'] = 'getresults_dst.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

