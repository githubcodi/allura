import difflib


class HtmlSideBySideDiff(object):

    table_tmpl = '''
<table class="side-by-side-diff">
  <thead>
    <th colspan="2">%s</th>
    <th colspan="2">%s</th>
  </thead>
%s
</table>
'''.strip()

    line_tmpl = '''
<tr>
  <td class="lineno">%s</td>
  <td%s><pre>%s</pre></td>
  <td class="lineno">%s</td>
  <td%s><pre>%s</pre></td>
</tr>'''.strip()

    def __init__(self, tabsize=4):
        self._tabsize = tabsize

    def _render_change(self, aline, bline, anum=None, bnum=None, astyle=None, bstyle=None):
        astyle = (' class="%s"' % astyle) if astyle else ''
        bstyle = (' class="%s"' % bstyle) if bstyle else ''
        anum = anum if anum is not None else ''
        bnum = bnum if bnum is not None else ''
        return self.line_tmpl % (anum, astyle, aline, bnum, bstyle, bline)

    def _preprocess(self, line):
        if not line:
            return line
        line = line.expandtabs(self._tabsize)
        return line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _replace_marks(self, line):
        # if entire line was added/removed/changed
        # we strip first mark and return corresponding flag
        # this is needed to be able to highlight entire <td> in the table,
        # rather then highlighting only chunk inside the <span>
        flag = ''
        if line.startswith('\0+') and line.endswith('\1'):
            line = line.lstrip('\0+').rstrip('\1')
            flag = 'diff-add'
        elif line.startswith('\0-') and line.endswith('\1'):
            line = line.lstrip('\0-').rstrip('\1')
            flag = 'diff-rem'
        elif '\0^' in line or '\0+' in line or '\0-' in line:
            flag = 'diff-chg'

        # replace all other marks with <span>'s
        span = '<span class="%s">'
        line = line.replace('\0+', span % 'diff-add')
        line = line.replace('\0-', span % 'diff-rem')
        line = line.replace('\0^', span % 'diff-chg')
        line = line.replace('\1', '</span>')
        return line, flag

    def _make_line(self, diff):
        aline, bline, changed = diff
        if changed is None:
            # context separation
            return self._render_change('...', '...', '', '', 'diff-gap', 'diff-gap')
        anum, aline = aline
        bnum, bline = bline
        aline = self._preprocess(aline)
        bline = self._preprocess(bline)
        if not changed:
            # line doesn't changed - render with default style
            return self._render_change(aline, bline, anum, bnum)

        aline, aflag = self._replace_marks(aline)
        bline, bflag = self._replace_marks(bline)
        return self._render_change(aline, bline, anum, bnum, aflag, bflag)

    def make_table(self, a, b, adesc=None, bdesc=None, context=5):
        """Make html table that displays side-by-side diff

        Arguments:
         - a -- list of text lines to be compared to b
         - b -- list of text lines to be compared to a
         - adesc -- description of the 'a' lines (e.g. filename)
         - bdesc -- description of the 'b' lines (e.g. filename)
         - context -- number of context lines to display

        Uses difflib._mdiff function to generate diff.
        """
        adesc = adesc or ''
        bdesc = bdesc or ''
        diff = difflib._mdiff(a, b, context=context)
        lines = [self._make_line(d) for d in diff]
        return self.table_tmpl % (adesc, bdesc, '\n'.join(lines))
