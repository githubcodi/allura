from tg import expose, redirect, flash
from pylons import c
from pymongo.bson import ObjectId

from pyforge.lib.helpers import push_config
from pyforge.lib.security import require, has_artifact_access

class ConfigOption(object):

    def __init__(self, name, ming_type, default):
        self.name, self.ming_type, self._default = (
            name, ming_type, default)

    @property
    def default(self):
        if callable(self._default):
            return self._default()
        return self._default

class WSGIHook(object):

    def handles(self, environ):
        return False

    def __call__(self, environ, start_response):
        return []

class SitemapEntry(object):

    def __init__(self, label, url=None, children=None):
        self.label = label
        self.url = url
        if children is None:
            children = []
        self.children = children

    def __getitem__(self, x):
        if isinstance(x, (list, tuple)):
            self.children.extend(list(x))
        else:
            self.children.append(x)
        return self

    def bind_app(self, app):
        lbl = self.label
        url = self.url
        if callable(lbl):
            lbl = lbl(app)
        if url and not url.startswith('/'):
            url = app.script_name + '/' + url
        return SitemapEntry(lbl, url, [
                ch.bind_app(app) for ch in self.children])

    def extend(self, sitemap):
        child_index = dict(
            (ch.label, ch) for ch in self.children)
        for e in sitemap:
            lbl = e.label
            match = child_index.get(e.label)
            if match and match.url == e.url:
                match.extend(e.children)
            else:
                self.children.append(e)
                child_index[lbl] = e

class Application(object):
    'base pyforge pluggable application'
    __version__ = None
    config_options = [
        ConfigOption('mount_point', str, 'app') ]
    templates=None # path to templates
    script_name=None
    root=None  # root controller
    permissions=[]
    sitemap = [ ]
    installable=True
    wsgi = WSGIHook()

    def __init__(self, project, app_config_object):
        self.project = project
        self.config = app_config_object # pragma: no cover
        self.admin = DefaultAdminController(self)
        self.script_name = project.script_name + self.config.options.mount_point

    @classmethod
    def default_options(cls):
        return dict(
            (co.name, co.default)
            for co in cls.config_options)

    def install(self, project):
        'Whatever logic is required to initially set up a plugin'
        pass # pragma: no cover

    def uninstall(self, project):
        'Whatever logic is required to tear down a plugin'
        pass # pragma: no cover

    def sidebar_menu(self):
        return []

class DefaultAdminController(object):

    def __init__(self, app):
        self.app = app

    @expose('pyforge.templates.app_admin')
    def index(self):
        return dict(app=self.app)

    @expose()
    def configure(self, **kw):
        with push_config(c, app=self.app):
            require(has_artifact_access('configure'), 'Must have configure permission')
            is_admin = self.app.config.plugin_name == 'admin'
            if kw.pop('delete', False):
                if is_admin:
                    flash('Cannot delete the admin plugin, sorry....')
                    redirect('.')
                c.project.uninstall_app(self.app.config.options.mount_point)
                redirect('..')
            for k,v in kw.iteritems():
                self.app.config.options[k] = v
            self.app.config.m.save()
            if is_admin:
                # possibly moving admin mount point
                redirect('/'
                         + c.project._id
                         + self.app.config.options.mount_point
                         + '/'
                         + self.app.config.options.mount_point
                         + '/')
            else:
                redirect('../' + self.app.config.options.mount_point + '/')

    @expose()
    def add_perm(self, permission, role):
        require(has_artifact_access('configure'))
        self.app.config.acl[permission].append(ObjectId.url_decode(role))
        self.app.config.m.save()
        redirect('.#app-acl')

    @expose()
    def del_perm(self, permission, role):
        require(has_artifact_access('configure'))
        self.app.config.acl[permission].remove(ObjectId.url_decode(role))
        self.app.config.m.save()
        redirect('.#app-acl')
        

