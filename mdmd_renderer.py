"""
Written by nanbuwks
forked from LaTeX renderer for mistletoe.
"""

import re
from itertools import chain
import mistletoe.latex_token as latex_token
from mistletoe.base_renderer import BaseRenderer
from mistletoe import block_token, span_token

class MDMDRenderer(BaseRenderer):
    def __init__(self, *extras):
        """
        Args:
            extras (list): allows subclasses to add even more custom tokens.
        """
        self._suppress_ptag_stack = [False]
        tokens = self._tokens_from_module(latex_token)
        self.packages = {}
        super().__init__(*chain(tokens, extras))

    def render_strong(self, token):
        return '**{}**'.format(self.render_inner(token))

    def render_emphasis(self, token):
        return '*{}*'.format(self.render_inner(token))

    def render_inline_code(self, token):
        return '``` {} ```'.format(self.render_inner(token))

    def render_strikethrough(self, token):
        self.packages['ulem'] = ['normalem']
        return '~~{}~~'.format(self.render_inner(token))

    def render_image(self, token):
        self.packages['graphicx'] = []
        return '![]({})'.format(token.src)

    def render_link(self, token):
        self.packages['hyperref'] = []
        template = '[{inner}]({target})'
        inner = self.render_inner(token)
        return template.format(target=token.target, inner=inner)

    def render_auto_link(self, token):
        return ''

    @staticmethod
    def render_math(token):
        return token.content

    def render_escape_sequence(self, token):
        return self.render_inner(token)

    def changehtml2img(self,s):
      #s=" <img src=\"http://www.nanbu.com/wiki/a.jpg\" width=\"12%\"\>  aaa <img src='http://www.au.com/b.png' width=24%> bbb "
      p=re.compile(r'<img[ \t\n\r\f]+.*?src[ \t\n\r\f]*=.+?>',re.IGNORECASE)
      q0=re.compile(r'src[ \t\n\r\f]*=[ \t\n\r\f]*(".*?"|\'.*?\'|.+?)[ \t\n\r\f]+',re.IGNORECASE)
      q1=re.compile(r'width[ \t\n\r\f]*=[ \t\n\r\f]*("(.*?)"|\'(.*?)\'|(.+?))[ \t\n\r\f]+',re.IGNORECASE)
      while True:
        match=p.search(s)
        if not match:
          break
        sub=match.group()[4:-1] #  <img と > を削除
        if "\\" == sub[-1]:
          sub=sub[:-1] # 最後に\があれば削除
        sub=sub+" "  # 最後に空白をつけることでアトリビュートの末尾に必ず空白があることになる
        natch=q0.search(sub)
        oatch=q1.search(sub)
        #if natch:
          # print(natch.group(1))
        if oatch:
          if oatch.group(2) is not None:
            width=oatch.group(2)
          if oatch.group(3) is not None:
            width=oatch.group(3)
          if oatch.group(4) is not None:
            width=oatch.group(4)
          if "%" == width[-1]:
            scale = float(width[:-1])/100
          else:
            scale = float(width)/600
          img=("[]( scale = "+str(scale)+")![]("+natch.group(1)+")")
        else:
          img=("![]("+natch.group(0)+")")
      #    print(oatch.group(1))
        s=s[:match.start()]+img+s[match.end():]
      return(s)

    def render_raw_text(self, token, escape=True):
        
        token.content=self.changehtml2img(token.content)
        value= (token.content.replace('$', '\$').replace('#', '\#')
                             .replace('{', '\{').replace('}', '\}')
                             .replace('&', '\&')) if escape else token.content
        return value



    def render_heading(self, token):
        str="##########"
        template = str[0:token.level]+' {inner}\n'
        inner = self.render_inner(token)
        return template.format( inner=inner)



    def render_quote(self, token):
        elements = []
        elements.extend([self.render(child) for child in token.children])
        quote="".join(elements)
        quote=re.sub('^','> ',quote,flags=re.MULTILINE)
        return '\n'+quote+'\n\n'

    def render_paragraph(self, token):
        if self._suppress_ptag_stack[-1]:
            return '{}'.format(self.render_inner(token))
        return '{}\n'.format(self.render_inner(token))

    def render_block_code(self, token):
        self.packages['listings'] = []
        template = ('\n```{}\n'
                    '{}'
                    '```\n')
        #inner = self.render_raw_text(token.children[0], False)
        inner = token.children[0].content
        return template.format(token.language, inner)

    def render_list(self, token):
        template = '{tag}{attr}\n{inner}\n'
        if token.start is not None:
            tag = '\n'
            attr = ' start="{}"'.format(token.start) if token.start != 1 else ''
        else:
            tag = '\n'
            attr = ''
        self._suppress_ptag_stack.append(not token.loose)
        inner = ''.join([self.render(child) for child in token.children])
        self._suppress_ptag_stack.pop()
        return template.format(tag=tag, attr=attr, inner=inner)
#        inner = self.render_inner(token)
#        return inner

    def render_list_item(self, token):
        template = '{prefix} {inner}\n'
##        prefix = ''.join(self.listTokens)
        result = template.format(prefix='-', inner=self.render_inner(token))
##        result = template.format(prefix=prefix, inner=self.render_inner(token))
#        if self._suppress_ptag_stack[-1]:
#            if token.children[0].__class__.__name__ == 'Paragraph':
#                inner_template = inner_template[1:]
#            if token.children[-1].__class__.__name__ == 'Paragraph':
#                inner_template = inner_template[:-1]
        return result
    def render_inner(self, token):
        """
        Recursively renders child tokens. Joins the rendered
        strings with no space in between.
        If newlines / spaces are needed between tokens, add them
        in their respective templates, or override this function
        in the renderer subclass, so that whitespace won't seem to
        appear magically for anyone reading your program.
        Arguments:
            token: a branch node who has children attribute.
        """
#        print( ''.join(map(self.render, token.children)))
#        print(111111111111111111111)
#        return token.children[0].__class__.__name__
#        st=""
#        for doc in token.children:
#           st = st +"#"+ doc.__class__.__name__

        return ''.join(map(self.render, token.children))


    def render_table(self, token):
        def render_align(column_align):
            if column_align != [None]:
                cols = [get_align(col) for col in token.column_align]
                return '|{}|'.format('|'.join(cols))
            else:
                return ''

        def get_align(col):
            if col is None:
                return ':-----'
            elif col == 0:
                return ':----:'
            elif col == 1:
                return '-----:'
            raise RuntimeError('Unrecognized align option: ' + col)

        template = ('\n{head}{align}\n{inner}\n')
        if hasattr(token, 'header'):
            head_template = '{inner}'
            head_inner = self.render_table_row(token.header)
            head_rendered = head_template.format(inner=head_inner)
        else: head_rendered = ''
        inner = self.render_inner(token)
        align = render_align(token.column_align)
        return template.format(head=head_rendered, inner=inner, align=align)

    def render_table_row(self, token):
        cells = [self.render(child) for child in token.children]
        return "|"+'|'.join(cells) + '|\n'

    def render_table_cell(self, token):
        return self.render_inner(token)

    @staticmethod
    def render_thematic_break(token):
        return '---\n'

    @staticmethod
    def render_line_break(token):
        return '\n' if token.soft else '\\newline\n'

    def render_packages(self):
        pattern = '\\usepackage{options}{{{package}}}\n'
        return ''.join(pattern.format(options=options or '', package=package)
                         for package, options in self.packages.items())

    def render_document(self, token):
        template = ('{inner}')
        self.footnotes.update(token.footnotes)
        return template.format(inner=self.render_inner(token))
