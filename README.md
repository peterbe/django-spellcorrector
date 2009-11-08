About django-spellcorrector
===========================

The spellcorrector app is basically a class that you instanciate and
with it you can do very fast spellcorrections similar to how Google
does it. The inspiration of this came from [Peter
Norvig](http://norvig.com/spell-correct.html) and he release his code
under the [MIT
license](http://www.opensource.org/licenses/mit-license.php) so this
is released under that license too.  

You don't need a word file to load up to start with. You'll basically
just use the content you have in your site. There's no point training
on words that you don't have because there's no point in being able to
do a spellcorrection for something that doesn't exist. 

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
        
Do note, the spellcorrector is only able to do spellcorrection of 2
edit-distances of words shorter than 9 characters. E.g.
"xetter"->"peter" but !"xengtssun"->"bengtsson". The reason for this
is that working out all those combinations for large words becomes
very slow. For really long words it would take up to a second. 

A good idea is to create a Spellcorrector instance in for example your
views.py but not loading it until it's actually needed. Example
views.py:

        spellcorrector = Spellcorrector()
	...
	def search(request):
	    if not spellcorrector.is_loaded():
	        spellcorrector.load()
	    print spellcorrector.correct(request.GET['q'])
	




