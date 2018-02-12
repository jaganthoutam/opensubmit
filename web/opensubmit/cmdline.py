'''
    This module contains administrative functionality
    that is available as command-line tool "opensubmit-web".

    All functions that demand a working Django ORM are implemented
    as Django management command and just called from here.

    Everything else is implemented here, so this file works without
    any of the install dependencies.
'''

import os
import pwd
import grp
import urllib.request
import urllib.parse
import urllib.error
import sys
from configparser import RawConfigParser

DEFAULT_CONFIG = '''
# This is the configuration file for the OpenSubmit tool.
# https://github.com/troeger/opensubmit
#
# It is expected to be located at:
# /etc/opensubmit/settings.ini (on production system), or
# ./settings_dev.ini (on developer systems)

[general]
# Enabling this will lead to detailed developer error information as result page
# whenever something goes wrong on server side.
# In production systems, you never want that to be enabled, for obvious security reasons.
DEBUG: False

[server]
# This is the root host url were the OpenSubmit tool is offered by your web server.
# If you serve the content from a subdirectory, please specify it too, without leading or trailing slashes,
# otherwise leave it empty.
HOST: {server-host}
HOST_DIR:

# This is the local directory were the uploaded assignment attachments are stored.
# Your probably need a lot of space here.
# Make sure that the path starts and ends with a slash.
MEDIA_ROOT: {server-mediaroot}

# This is the logging file. The web server must be allowed to write into it.
LOG_FILE: /var/log/opensubmit.log

# This is the timezone all dates and deadlines are specified in.
# This setting overrides your web server default for the time zone.
# The list of available zones is here:
# http://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIME_ZONE: Europe/Berlin

# This is a unique string needed for some of the security features.
# Change it, the value does not matter.
SECRET_KEY: uzfp=4gv1u((#hb*#o3*4^v#u#g9k8-)us2nw^)@rz0-$2-23)

[database]
# The database you are using. Possible choices are
# - postgresql_psycopg2
# - mysql
# - sqlite3
# - oracle
DATABASE_ENGINE: {database-engine}

# The name of the database. It must be already available for being used.
# In SQLite, this is the path to the database file.
DATABASE_NAME: {database-name}

# The user name for accessing the database. Not needed for SQLite.
DATABASE_USER: {database-user}

# The user password for accessing the database. Not needed for SQLite.
DATABASE_PASSWORD: {database-password}

# The host name for accessing the database. Not needed for SQLite.
# An empty settings means that the database is on the same host as the web server.
DATABASE_HOST: {database-host}

# The port number for accessing the database. Not needed for SQLite.
# An empty settings means that the database default use used.
DATABASE_PORT: {database-port}

[executor]
# The shared secret with the job executor. This ensures that only authorized
# machines can fetch submitted solution attachments for validation, and not
# every student ...
# Change it, the value does not matter.
SHARED_SECRET: 49846zut93purfh977TTTiuhgalkjfnk89

[admin]
# The administrator for this installation. Course administrators
# are stored in the database, so this is only the technical contact for problems
# with the tool itself. Exceptions that happen due to bugs or other issues
# are sent to this address.
ADMIN_NAME: Super Admin
ADMIN_EMAIL: root@localhost

[login]
# Enables or disables login with OpenID
LOGIN_OPENID: True

# Text shown beside the OpenID login icon.
LOGIN_DESCRIPTION: StackExchange

# OpenID provider URL to be used for login.
OPENID_PROVIDER: https://openid.stackexchange.com

# Enables or disables login with Twitter
LOGIN_TWITTER: False

# OAuth application credentials for Twitter
LOGIN_TWITTER_OAUTH_KEY:
LOGIN_TWITTER_OAUTH_SECRET:

# Enables or disables login with Google
LOGIN_GOOGLE: True

# OAuth application credentials for Google
LOGIN_GOOGLE_OAUTH_KEY: 631787075842-1e14uvstrno29bl9b684194lcq435p93.apps.googleusercontent.com 
LOGIN_GOOGLE_OAUTH_SECRET: o4_b20ieVruAr_-U-N6fFwEm 

# Enables or disables login with GitHub
LOGIN_GITHUB: False

# OAuth application credentials for GitHub
LOGIN_GITHUB_OAUTH_KEY:
LOGIN_GITHUB_OAUTH_SECRET:

# Enables or diables login through Apache 2.4 mod_shib authentication
LOGIN_SHIB: False
LOGIN_SHIB_DESCRIPTION: Shibboleth
'''


def django_admin(args):
    '''
        Run something like it would be done through Django's manage.py.
    '''
    from django.core.management import execute_from_command_line
    from django.core.exceptions import ImproperlyConfigured
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "opensubmit.settings")
    try:
        execute_from_command_line([sys.argv[0]] + args)
    except ImproperlyConfigured as e:
        print(str(e))
        exit(-1)


def apache_config(config, outputfile):
    '''
        Generate a valid Apache configuration file, based on the given settings.
    '''
    if os.path.exists(outputfile):
        os.rename(outputfile, outputfile + ".old")
        print("Renamed existing Apache config file to " + outputfile + ".old")

    from opensubmit import settings
    f = open(outputfile, 'w')
    print("Generating Apache configuration in " + outputfile)
    subdir = (len(settings.HOST_DIR) > 0)
    text = """
    # OpenSubmit Configuration for Apache 2.4
    # These directives are expected to live in some <VirtualHost> block
    """
    if subdir:
        text += "Alias /%s/static/ %s\n" % (settings.HOST_DIR,
                                            settings.STATIC_ROOT)
        text += "    WSGIScriptAlias /%s %s/wsgi.py\n" % (
            settings.HOST_DIR, settings.SCRIPT_ROOT)
    else:
        text += "Alias /static/ %s\n" % (settings.STATIC_ROOT)
        text += "    WSGIScriptAlias / %s/wsgi.py" % (settings.SCRIPT_ROOT)
    text += """
    WSGIPassAuthorization On
    <Directory {static_path}>
         Require all granted
    </Directory>
    <Directory {install_path}>
         <Files wsgi.py>
              Require all granted
         </Files>
    </Directory>
    """.format(static_path=settings.STATIC_ROOT, install_path=settings.SCRIPT_ROOT)

    f.write(text)
    f.close()


def check_path(directory):
    '''
        Checks if the directories for this path exist, and creates them in case.
    '''
    if directory != '':
        if not os.path.exists(directory):
            os.makedirs(directory, 0o775)   # rwxrwxr-x


def check_file(filepath):
    '''
        - Checks if the parent directories for this path exist.
        - Checks that the file exists.
        - Donates the file to the web server user.

        TODO: This is Debian / Ubuntu specific.
    '''
    check_path(os.path.dirname(filepath))
    if not os.path.exists(filepath):
        print("WARNING: File does not exist. Creating it: %s" % filepath)
        open(filepath, 'a').close()
    try:
        print("Setting access rights for %s for www-data user" % (filepath))
        uid = pwd.getpwnam("www-data").pw_uid
        gid = grp.getgrnam("www-data").gr_gid
        os.chown(filepath, uid, gid)
        os.chmod(filepath, 0o660)  # rw-rw---
    except:
        print("WARNING: Could not adjust file system permissions for %s. Make sure your web server can write into it." % filepath)


def check_web_config_consistency(config):
    '''
        Check the web application config file for consistency.
    '''
    login_conf_deps = {
        'LOGIN_TWITTER': ['LOGIN_TWITTER_OAUTH_KEY', 'LOGIN_TWITTER_OAUTH_SECRET'],
        'LOGIN_GOOGLE': ['LOGIN_GOOGLE_OAUTH_KEY', 'LOGIN_GOOGLE_OAUTH_SECRET'],
        'LOGIN_GITHUB': ['LOGIN_GITHUB_OAUTH_KEY', 'LOGIN_GITHUB_OAUTH_SECRET']
    }

    print("Checking configuration of the OpenSubmit web application...")
    # Let Django's manage.py load the settings file, to see if this works in general
    django_admin(["check"])
    # Check configured host
    try:
        urllib.request.urlopen(config.get("server", "HOST"))
    except Exception as e:
        # This may be ok, when the admin is still setting up to server
        print("The configured HOST seems to be invalid at the moment: " + str(e))
    # Check configuration dependencies
    for k, v in list(login_conf_deps.items()):
        if config.getboolean('login', k):
            for needed in v:
                if len(config.get('login', needed)) < 1:
                    print(
                        "ERROR: You have enabled %s in settings.ini, but %s is not set." % (k, needed))
                    return False
    # Check media path
    check_path(config.get('server', 'MEDIA_ROOT'))
    # Prepare empty log file, in case the web server has no creation rights
    log_file = config.get('server', 'LOG_FILE')
    print("Preparing log file at " + log_file)
    check_file(log_file)
    # If SQLite database, adjust file system permissions for the web server
    if config.get('database', 'DATABASE_ENGINE') == 'sqlite3':
        name = config.get('database', 'DATABASE_NAME')
        if not os.path.isabs(name):
            print("ERROR: Your SQLite database name must be an absolute path. The web server must have directory access permissions for this path.")
            return False
        check_file(config.get('database', 'DATABASE_NAME'))
    # everything ok
    return True


def check_web_config(config_fname):
    '''
        Try to load the Django settings.
        If this does not work, than settings file does not exist.

        Returns:
            Loaded configuration, or None.
    '''
    print("Looking for config file at {0} ...".format(config_fname))
    config = RawConfigParser()
    try:
        config.readfp(open(config_fname))
        return config
    except IOError:
        print("ERROR: Seems like the config file does not exist. Please call 'opensubmit-web configcreate' first.")
        return None


def check_web_db():
    '''
        Everything related to database checks and updates.
    '''
    print("Testing for neccessary database migrations...")
    django_admin(["migrate"])             # apply schema migrations
    print("Checking the OpenSubmit permission system...")
    # configure permission system, of needed
    django_admin(["fixperms"])
    return True


def configcreate(config_path, config_fname, open_options):
    content = DEFAULT_CONFIG.format(**open_options)

    try:
        check_path(config_path)
        f = open(config_path + config_fname, 'wt')
        f.write(content)
        f.close()
        print("Config file %s generated at %s. Please edit it." % (config_fname. config_path))
    except Exception:
        print("ERROR: Could not create config file at {0}. Please use sudo or become root.".format(
            config_path + config_fname))


def configtest(config_path, config_fname):
    print("Inspecting OpenSubmit configuration ...")
    config = check_web_config(config_path + config_fname)
    if not config:
        return          # Let them first fix the config file before trying a DB access
    if not check_web_config_consistency(config):
        return
    if not check_web_db():
        return
    print("Preparing static files for web server...")
    django_admin(["collectstatic", "--noinput", "--clear", "-v 0"])


def print_help():
    print("configcreate:        Create initial config files for the OpenSubmit web server.")
    print("apachecreate:        Create config file snippet for Apache 2.4.")
    print("configtest:          Check config files and database for correct installation of the OpenSubmit web server.")
    print("democreate:          Install some test data (courses, assignments, users).")
    print("fixperms:            Check and fix student and tutor permissions")
    print("fixchecksums:        Re-create all student file checksums (for duplicate detection)")
    print("makeadmin   <email>: Make this user an admin with backend rights.")
    print("makeowner   <email>: Make this user a course owner with backend rights.")
    print("maketutor   <email>: Make this user a course tutor with backend rights.")
    print("makestudent <email>: Make this user a student without backend rights.")


def console_script(fsroot='/'):
    '''
        The main entry point for the production administration script 'opensubmit-web'.
        The argument allows the test suite to override the root of all paths used in here.
    '''

    if len(sys.argv) == 1:
        print_help()
        return

    # Translate legacy commands
    if sys.argv[1] == "configure":
        sys.argv[1] = 'configtest'
    if sys.argv[1] == "createdemo":
        sys.argv[1] = 'democreate'

    if sys.argv[1] == 'apachecreate':
        config = check_web_config(fsroot + 'etc/opensubmit/' + 'settings.ini')
        if config:
            apache_config(config, fsroot + 'etc/opensubmit/' + 'apache24.conf')
        return

    if sys.argv[1] == 'configcreate':
        # TODO: Hack, do the arg handling with a proper library

        # Config name, default value, character pos of argument
        poss_options = [['server-host', '***not configured***'],
                        ['server-mediaroot', '***not configured***'],
                        ['database-name', '/tmp/database.sqlite'],
                        ['database-engine', 'sqlite3'],
                        ['database-user', ''],
                        ['database-password', ''],
                        ['database-host', ''],
                        ['database-port', ''],
                        ]
        options = {}

        for optionname, default in poss_options:
            options[optionname] = default
            for index, text in enumerate(sys.argv[2:]):
                if text.startswith('--' + optionname + '='):
                    options[optionname] = text[len(optionname) + 3:]
        configcreate(fsroot + 'etc/opensubmit/', 'settings.ini', options)
        return

    if sys.argv[1] == 'configtest':
        configtest(fsroot + 'etc/opensubmit/', 'settings.ini')
        return

    if sys.argv[1] in ['fixperms', 'fixchecksums', 'democreate']:
        django_admin([sys.argv[1]])
        return

    if sys.argv[1] in ['makeadmin', 'makeowner', 'maketutor', 'makestudent']:
        django_admin([sys.argv[1], sys.argv[2]])
        return

    print_help()


if __name__ == "__main__":
    console_script()
