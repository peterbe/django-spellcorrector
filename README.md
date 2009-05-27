About django-spellcorrector
===========================

The spellcorrector app is basically a class that you instanciate and
with it you can do very fast spellcorrections similar to how Google
does it. The inspiration of this came from [Peter
Norvig](http://norvig.com/spell-correct.html) and he release his code
under the [MIT
license](http://www.opensource.org/licenses/mit-license.php) so this
is released under that license too.  

The exampleapp included in this repo should basically show how you can
use the spellcorrector. For the impatient, here's some code that wraps
that up:

        from spellcorrector.views import Spellcorrector
        
        sc = Spellcorrector()
        sc.load() # nothing will happen the first time
        
        sc.train(u"peter")
        print sc.correct(u"petter") # will print peter
        sc.save()
        
        sc2 = Spellcorrector()
        sc2.load()
        print sc2.correct(u"petter") # will print peter
        


