# -*- coding: utf-8 -*-
'''
PythonTeX utilities class for Python scripts.

The utilities class provides variables and methods for the individual 
Python scripts created and executed by PythonTeX.  An instance of the class 
named "pytex" is automatically created in each individual script.

Copyright (c) 2012, Geoffrey M. Poore
All rights reserved.
Licensed under the BSD 3-Clause License:
    http://www.opensource.org/licenses/BSD-3-Clause

'''


# Imports
# Imports are only needed for SymPy; these are brought in via "lazy import."
# Importing unicode_literals here shouldn't ever be necessary under Python 2.
# If unicode_literals is imported in the main script, then all strings in this 
# script will be treated as bytes, and the main script will try to decode the 
# strings from this script as necessary.  The decoding shouldn't cause any 
# problems, since all strings in this file may be decoded as valid ascii. 
# (The actual file is encoded in utf-8, but only characters within the ascii 
# subset are actually used).


class PythontexUtils(object):
    '''
    A class of PythonTeX utilities.
    
    Provides variables for keeping track of TeX-side information, and methods
    for formatting and saving data.
    '''
    
    def __init__(self, fmtr='str'):
        '''
        Initialize, optionally setting the formatter.
        '''
        self._sympy_latex_is_init = False
        
        self.set_formatter(fmtr)
        
        # If not using the 'sympy_latex' formatter, set up a dummy interface
        if fmtr != 'sympy_latex':
            self.set_sympy_latex = self._dummy_set_sympy_latex
            self.sympy_latex = self._dummy_sympy_latex
        

        # The following variables and methods will be created within instances 
        # of the class during execution.  They are listed here for bookkeeping 
        # purposes.        
        #
        # String variables for keeping track of TeX information.  Most are 
        # actually needed; the rest are included for completeness.
        #     * inputtype
        #     * inputsession
        #     * inputgroup
        #     * inputinstance
        #     * inputcommand
        #     * inputcontext
        #     * inputline
        #
        # Future file handle for output that is saved via macros
        #     * macrofile
        #
        # Future formatter function that is used to format output
        #     * formatter

    
    # We need a context-aware interface to SymPy's latex printer.  The 
    # appearance of typeset math should depend on where it appears in a 
    # document.  (We will refer to the latex printer, rather than the LaTeX 
    # printer, because the two are separate.  Compare sympy.printing.latex 
    # and sympy.galgebra.latex_ex.)  
    #
    # Creating this interface takes some work, since we don't want to import 
    # anything from SymPy unless it is actually used, to keep things clean and 
    # fast.  Part of this involves creating a dummy interface, for when SymPy 
    # isn't available.
    #
    # First we create a tuple containing all LaTeX math styles.  These are 
    # the contexts that SymPy's latex printer must adapt to.  Then we create 
    # a dummy dictionary of settings functions and a dummy interface 
    # function.  Both of these raise UserWarning.  They attempt to proceed 
    # if warnings happen to be suppressed.

    # The style order doesn't matter, but it corresponds to that of \mathchoice
    _sympy_styles = ('display', 'text', 'script', 'scriptscript')
    
    def _dummy_set_sympy_latex(self):
        '''
        A dummy function for setting the latex printer.
        '''
        raise UserWarning("Attempt to use sympy_latex before initializing; use method init_sympy_latex()")
        pass
    
    def _dummy_sympy_latex(self, expr, **settings):
        '''
        A dummy interface to SymPy's LatexPrinter
        '''
        raise UserWarning("Attempt to use sympy_latex before initializing; use method init_sympy_latex()")
        return str(expr)
    
    # Next we create a method that initializes the actual context-aware 
    # interface to SymPy's latex printer.
    def init_sympy_latex(self):
        '''
        Initialize a context-aware interface to SymPy's latex printer.
        
        This consists of creating the dictionary of settings and creating the 
        sympy_latex method that serves as an interface to SymPy's 
        LatexPrinter.  This last step is actually performed by calling 
        self._make_sympy_latex().
        
        The initialization code only runs if initialization hasn't already 
        occurred.
        '''
        if self._sympy_latex_is_init:
            return
        else:
            self._sympy_latex_is_init = True
            
            # Create dictionaries of settings for different contexts.
            # 
            # Currently, the main goal is to use pmatrix (or an equivalent) 
            # in \displaystyle contexts, and smallmatrix in \textstyle, 
            # \scriptstyle (superscript or subscript), and \scriptscriptstyle
            # (superscript or subscript of a superscript or subscript) 
            # contexts.  Basically, we want matrix size to automatically 
            # scale based on context.  It is expected that additional 
            # customization may prove useful as SymPy's LatexPrinter is 
            # further developed.
            #
            # The 'fold_frac_powers' option is probably the main other 
            # setting that might sometimes be nice to invoke in a 
            # context-dependent manner.  This folds fractional powers (slash 
            # rather than \frac).  Apparently, the folding only applies for 
            # powers that are Rationals; symbolic powers aren't folded.
            #
            # In the default settings below, all matrices are set to use 
            # parentheses rather than square brackets.  This is largely a 
            # matter of personal preference.  The use of parentheses is based 
            # on the rationale that parentheses are less easily confused with 
            # the determinant and are easier to write by hand than are square 
            # brackets.  The settings for 'script' and 'scriptscript' are set
            # to those of 'text', since all of these should in general 
            # require a more compact representation of things.
            self._sympy_latex_settings = dict()
            self._sympy_latex_settings['display'] = {
                    'mat_str': 'pmatrix',
                    'mat_delim': None}
            self._sympy_latex_settings['text'] = {
                    #'fold_frac_powers': True,
                    'mat_str': 'smallmatrix',
                    'mat_delim': '('}            
            self._sympy_latex_settings['script'] = self._sympy_latex_settings['text']
            self._sympy_latex_settings['scriptscript'] = self._sympy_latex_settings['text']
            
            # Now we create a function for updating the settings.
            #
            # Note that EVERY time the settings are changed, we must call 
            # self._make_sympy_latex().  This is because the sympy_latex() 
            # method is defined based on the settings, and every time the 
            # settings change, it may need to be redefined.  It would be 
            # possible to define sympy_latex() so that its definition remained 
            # constant, simply drawing on the settings.  But most common 
            # combinations of settings allow more efficient versions of 
            # sympy_latex() to be defined.            
            self.set_sympy_latex = dict()
            def set_sympy_latex(style, **kwargs):
                if style in self._sympy_styles:
                    self._sympy_latex_settings[style].update(kwargs)
                elif style == 'all':
                    for s in self._sympy_styles:
                        self._sympy_latex_settings[s].update(kwargs)
                else:
                    raise UserWarning('Unknown LaTeX math style ' + str(style))
                self._make_sympy_latex()
            self.set_sympy_latex = set_sympy_latex
            
            # Now that the dictionaries of settings have been created, and 
            # the dictionaries of functions for modifying the settings are in 
            # place, we are ready to create the actual interface.
            self._make_sympy_latex()
            
    # Finally, we create the actual interface to SymPy's LatexPrinter
    def _make_sympy_latex(self):
        '''
        Create a context-aware interface to SymPy's LatexPrinter class.
        
        This is an interface to the LatexPrinter class, rather than 
        to the latex function, because the function is simply a 
        wrapper for accessing the class and because settings may be 
        passed to the class more easily.
        
        Context dependence is accomplished via LaTeX's \mathchoice macro.  
        This macros takes four arguments:
            \mathchoice{<display>}{<text>}{<script>}{<scriptscript>}
        All four arguments are typeset by LaTeX, and then the appropriate one 
        is actually typeset in the document based on the current style.  This 
        may seem like a very inefficient way of doing things, but this 
        approach is necessary because LaTeX doesn't know the math style at a 
        given point until after ALL mathematics have been typeset.  This is 
        because macros such as \over and \atop change the math style of things 
        that PRECEDE them.  See the following discussion for more information:
            http://tex.stackexchange.com/questions/1223/is-there-a-test-for-the-different-styles-inside-maths-mode
        
        The interface takes optional settings.  These optional 
        settings override the default context-dependent settings.  
        Accomplishing this mixture of settings requires (deep)copying 
        the default settings, then updating the copies with the optional 
        settings.  This leaves the default settings intact, with their 
        original values, for the next usage.
        
        The interface is created in various ways depending on the specific
        combination of context-specific settings.  While a general, static 
        interface could be created, that would involve invoking LatexPrinter 
        four times, once for each math style.  It would also require that 
        LaTeX process a \mathchoice macro for everything returned by 
        sympy_latex(), which would add more inefficiency.  In practice, there 
        will generally be enough overlap between the different settings, and 
        the settings will be focused enough, that more efficient 
        implementations of sympy_latex() are possible.
        
        Note that we perform a "lazy import" here.  We don't want to import
        the LatexPrinter unless we are sure to use it, since the import brings
        along a number of other dependencies from SymPy.  We don't want 
        unnecessary overhead from SymPy imports.
        '''
        import copy
        # sys is also needed, but it is part of the default code defined in
        # pythontex_types*.py, so it will always be present.
        try:
            from sympy.printing.latex import LatexPrinter
        except ImportError:
            sys.exit('Could not import from SymPy')
        
        # Go through a number of possible scenarios, to create an efficient 
        # implementation of sympy_latex()
        if all(self._sympy_latex_settings[style] == {} for style in self._sympy_styles):
            def sympy_latex(expr, **settings):
                '''            
                Deal with the case where there are no context-specific 
                settings.
                '''
                return LatexPrinter(settings).doprint(expr)
        elif all(self._sympy_latex_settings[style] == self._sympy_latex_settings['display'] for style in self._sympy_styles):
            def sympy_latex(expr, **settings):
                '''
                Deal with the case where all settings are identical, and thus 
                the settings are really only being used to set defaults, 
                rather than context-specific behavior.
                
                Check for empty settings, so as to avoid deepcopy
                '''
                if not settings:
                    return LatexPrinter(self._sympy_latex_settings['display']).doprint(expr)
                else:
                    final_settings = copy.deepcopy(self._sympy_latex_settings['display'])
                    final_settings.update(settings)
                    return LatexPrinter(final_settings).doprint(expr)
        elif all(self._sympy_latex_settings[style] == self._sympy_latex_settings['text'] for style in ('script', 'scriptscript')):
            def sympy_latex(expr, **settings):
                '''
                Deal with the case where only 'display' has different settings.
                
                This should be the most common case.
                '''
                if not settings:
                    display = LatexPrinter(self._sympy_latex_settings['display']).doprint(expr)
                    text = LatexPrinter(self._sympy_latex_settings['text']).doprint(expr)
                else:
                    display_settings = copy.deepcopy(self._sympy_latex_settings['display'])
                    display_settings.update(settings)
                    display = LatexPrinter(display_settings).doprint(expr)
                    text_settings = copy.deepcopy(self._sympy_latex_settings['text'])
                    text_settings.update(settings)
                    text = LatexPrinter(text_settings).doprint(expr)
                if display == text:
                    return display
                else:
                    return r'\mathchoice{' + display + '}{' + text + '}{' + text + '}{' + text + '}'
        else:
            def sympy_latex(expr, **settings):
                '''
                If all attempts at simplification fail, create the most 
                general interface.
                
                The main disadvantage here is that LatexPrinter is invoked 
                four times and we must create many temporary variables.
                '''
                if not settings:
                    display = LatexPrinter(self._sympy_latex_settings['display']).doprint(expr)
                    text = LatexPrinter(self._sympy_latex_settings['text']).doprint(expr)
                    script = LatexPrinter(self._sympy_latex_settings['script']).doprint(expr)
                    scriptscript = LatexPrinter(self._sympy_latex_settings['scriptscript']).doprint(expr)
                else:
                    display_settings = copy.deepcopy(self._sympy_latex_settings['display'])
                    display_settings.update(settings)
                    display = LatexPrinter(display_settings).doprint(expr)
                    text_settings = copy.deepcopy(self._sympy_latex_settings['text'])
                    text_settings.update(settings)
                    text = LatexPrinter(text_settings).doprint(expr)
                    script_settings = copy.deepcopy(self._sympy_latex_settings['script'])
                    script_settings.update(settings)
                    script = LatexPrinter(script_settings).doprint(expr)
                    scriptscript_settings = copy.deepcopy(self._sympy_latex_settings['scripscript'])
                    scriptscript_settings.update(settings)
                    scriptscript = LatexPrinter(scriptscript_settings).doprint(expr)
                if display == text and display == script and display == scriptscript:
                    return display
                else:
                    return r'\mathchoice{' + display + '}{' + text + '}{' + script + '}{' + scriptscript+ '}'
        self.sympy_latex = sympy_latex
    
    # Now we are ready to create non-SymPy formatters and a method for 
    # setting formatters
    def identity_formatter(self, expr):
        '''
        For generality, we need an identity formatter, a formatter that does
        nothing to its argument and simply returns it unchanged.
        '''
        return expr
   
    def set_formatter(self, fmtr='str'):
        '''
        Set the formatter method.
        
        This is used to process output that is brought in via macros.  It is 
        also available for the user in formatting printed or saved output.
        '''
        #// Python 2
        if not isinstance(fmtr, basestring):
            raise TypeError('set_formatter() takes a string argument')
        #\\ End Python 2
        #// Python 3
        #if not isinstance(fmtr, str):
        #    raise TypeError('set_formatter() takes a string argument')
        #\\ End Python 3
        if fmtr == 'str':
            #// Python 2
            self.formatter = unicode
            #\\ End Python 2
            #// Python 3
            #self.formatter = str
            #\\ End Python 3
        elif fmtr == 'sympy_latex':
            self.init_sympy_latex()
            self.formatter = self.sympy_latex
        elif fmtr in {'None', 'none', 'identity'}:
            self.formatter = self.identity_formatter
        else:
            raise ValueError('Unsupported formatter type')
    
    # Finally, we provide a method that saves "printed" content via macros.
    # This is one of the two primary tasks of the class.  (Actually, this is 
    # the primary task when the SymPy latex printer interface isn't needed.)
    def _print_via_macro(self, expr):
        '''
        Function for "printing" via macros.  Convert output to macro form
        and save it to an external file.
        
        This function is not intended for general use.  It is specifically 
        for inline commands without a suffix, which pull in Python content 
        via macros.  Attempts to use it in other contexts may fail or cause 
        unexpected behavior.
        '''
        before = (r'\expandafter\long\expandafter\def\csname pytx@MCR@' + 
                  self.inputtype + '@' + self.inputsession + '@' + 
                  self.inputgroup + '@' + self.inputinstance + r'\endcsname{')
        after = '}\n\n'
        #// Python 2
        self.macrofile.write(unicode(before + self.formatter(expr) + after))
        #\\ End Python 2
        #// Python 3
        #self.macrofile.write(before + self.formatter(expr) + after)
        #\\ End Python 3

