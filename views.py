import re
from models import Word

def tokenize_text(text):
    # XXX improve this 
    return re.findall(u'[a-z\xe5\xe4\xf6]+', text.lower())

def train_text(text, language='en'):
    for word in tokenize_text(text):
        train_word(word, language='en')
        
def train_word(word, language='en'):
    pass
    

def incr_word(word, language='en'):
    try:
        word_object = Word.objects.get(word=word.lower(), language=language)
        word_object.count += 1
        word_object.save()
    except Word.DoesNotExist:
        Word.objects.create(word=word.lower(), language=language)
        
        
def decr_word(word, language='en'):
    try:
        word_object = Word.objects.get(word=word.lower(), language=language)
        if word_object.count == 1:
            word_object.delete()
        else:
            word_object.count -= 1
            word_object.save()
    except Word.DoesNotExist:
        pass
    
    
    
class Spellcorrector(object):
################################################################################    
    def __init__(self, language='en', alphabet=u'abcdefghijklmnopqrstuvwxyz'):
        self.language = language
        self.alphabet = alphabet; assert isinstance(alphabet, unicode)
        
        # this is the dict that contains the master record of all word variants
        self.nwords = {}
        
        # this is a list of all the good words that we've loaded
        # and assumingly does not contain any spelling mistakes
        self._trained_words = []
        
        # by default we assume that we haven't loaded a list of stored words
        self._loaded = False
        
        
    def load(self):
        for record in Word.objects.filter(language=self.language):
            
            #self.nwords[record.word] = record.count
            
        self._loaded = []
        
    def _edits1(self, word):
        n = len(word)
        return set(# deletion
                   [word[0:i]+word[i+1:] for i in range(n)] +
                   # transposition
                   [word[0:i]+word[i+1]+word[i]+word[i+2:] for i in range(n-1)] +
                   # alteration
                   [word[0:i]+c+word[i+1:] for i in range(n) for c in self.alphabet] +
                   # insertion
                   [word[0:i]+c+word[i:] for i in range(n+1) for c in self.alphabet])

    def _known_edits2(self, word):
        return set(e2 for e1 in self._edits1(word) 
                      for e2 in self._edits1(e1) 
                      if e2 in self.nwords)

    def known(self, words): 
        return set(w for w in words if w in self.nwords)

    def _candidates(self, word):
        word = word.lower()
        if len(word) > 10:
            # if the word is this big, edits2() returns a HUUUUGE
            # set which kills the CPU and takes forever.
            return self.known([word]) | self.known(self._edits1(word)) or [word]
        else:
            return self.known([word]) | self.known(self._edits1(word)) or \
                   self._known_edits2(word) or [word]
        
            
   def _train(self, words):
        #words = [safe_unicode(x).lower() for x in words]

        _trained_words = self._trained_words
        
        new_words = words
        for word in new_words:
            assert isinstance(word, unicode), "word %r not a unicode object" % word
            
            # if we've already trained a variant of this word, e.g 'mike', 
            # that would have added the misspellt alternatives too (set to -1)
            # like 'mqke','mbke','make' etc. Perhaps now the second word 
            # we train on is 'make' which was a misspelled alternative of 'mike'
            # entered in the previous loop.
            # When we train on words, we never want to add a word with a bad start 
            # (e.g. -1) so that's why we use this max() function here so that
            # the previous (that we +1 to) never is -1)

            if self._loaded:
                # since there are other word already in there like this, make sure
                # our trained word gets higher no matter what.
                p = max(self.nwords.get(self.correct(word), 0), 0) + 1
            else:
                # if we haven't loaded the language file, there's no need to find
                # an alternative that is higher than this.
                p = max(self.nwords.get(word.lower(), 0), 0) + 1
                
            self.nwords[word] = p
            
            # Right, now that we've added this new strange word we also
            # add all the possible misspellings of this new word and
            # assign them the lowest possible score, -1.
            # The reason for doing is that only words that exist in the
            # nwords variable can be corrected. That means that you can
            # do spelling corrections on the trained new word.
            # For example, if you add your own word 'Laphroaig' and assume
            # that's correct the you want to be able to spellcorrect if
            # someone queries the word 'Laproaig' or 'Laphroaigh'

            # If you read the comment a couple of lines above about the necessary
            # use of the max() function you'll understand the thinkin here.
            # Training can be done in separate batches. 
            # For example, in the first batch to train on the words:
            #   ['mike','peter']
            # in the second batch to train on 
            #  ['make','george']
            # Thanks to the max() function above, that make word end up with 
            # a count of 0.
            # No, suppose you train on these words:
            #   ['mike','sivia','make']
            # Then, in the first element,  you're expected to add 
            # misspelled alternatives of the word 'mike' (e.g 'mbke')
            # but thanks to this limiting list compression here below we can 
            # make sure we're not going to bother with the alternative 'make' 
            # because that's in the list of training words.
            if self._load_language_files:
                new_word_alternatives = [x for x in self._edits1(word) if x not in new_words]
                for variant in new_word_alternatives:
                    if variant not in self.nwords:
                        self.nwords[variant] = -1

            _trained_words.append(word)
            
        self._trained_words = _trained_words
        

    def train(self, words):
        if not isinstance(words, (tuple, list)):
            words = [words]

        self._train(words)
    