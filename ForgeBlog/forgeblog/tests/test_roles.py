from pylons import c, g

from allura.tests import helpers
from allura import model as M

def setUp():
    helpers.setup_basic_test()
    helpers.setup_global_objects()
    g.set_project('test')
    c.project.install_app('blog', 'blog')
    g.set_app('blog')

def test_role_assignments():
    role_developer = M.ProjectRole.query.get(name='Developer')._id
    role_auth = M.ProjectRole.query.get(name='*authenticated')._id
    role_anon = M.ProjectRole.query.get(name='*anonymous')._id
    assert c.app.config.acl['configure'] == c.project.acl['tool']
    assert c.app.config.acl['read'] == c.project.acl['read']
    assert c.app.config.acl['write'] == [role_developer]
    assert c.app.config.acl['unmoderated_post'] == [role_auth]
    assert c.app.config.acl['post'] == [role_anon]
    assert c.app.config.acl['moderate'] == [role_developer]
    assert c.app.config.acl['admin'] == c.project.acl['tool']
