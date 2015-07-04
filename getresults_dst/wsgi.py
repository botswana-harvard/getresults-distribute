import os
# import sys

# sys.path.append(os.path.expanduser('~/source/getresults-distribute'))
# sys.path.append(os.path.expanduser('~/source/getresults-distribute/getresults_dst'))
# sys.path.append(os.path.expanduser('~/.virtualenvs/django18/lib/python3.4/site-packages'))
#
# activate_env = os.path.join(os.path.expanduser('~/.virtualenvs/django18/bin/activate_this.py'))
#
# with open(activate_env) as f:
#     code = compile(f.read(), activate_env, 'exec')
#     exec(code, dict(__file__=activate_env))

os.environ['DJANGO_SETTINGS_MODULE'] = 'getresults_dst.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
