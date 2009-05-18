import re
from models import Word

def tokenize_text(text):
    # XXX improve this 
    return re.findall(u'[a-z\xe5\xe4\xf6]+', text.lower())


def remove_stopwords(word_sequence, language='en'):
    stopwords = \
    (
     "a", "and", "are", "as", "at", "be", "but", "by",
     "for", "if", "in", "into", "is", "it",
     "no", "not", "of", "on", "or", "such",
     "that", "the", "their", "then", "there", "these",
     "they", "this", "to", "was", "will", "with"
    )
    return [x for x in word_sequence if x.lower() not in stopwords]
    

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
    
    
def _guess_alphabet(language):
    default = u'abcdefghijklmnopqrstuvwxyz'
    language = language.lower().strip()
    if language == 'sv':
        return default + u'\xe5' + u'\xe4' + u'\xf6'
    elif language == 'de':
        return default + u'\xdf\xe4\xf6\xfc'
    return default
    
class Spellcorrector(object):
    def __init__(self, language='en', alphabet=None):
        self.language = language
        if alphabet is None:
            self.alphabet = _guess_alphabet(language)
        else:
            self.alphabet = unicode(alphabet)

        # this is the dict that contains the master record of all word variants
        self.nwords = {}
        
        # this is a list of all the good words that we've loaded
        # and assumingly does not contain any spelling mistakes
        self._trained_words = []
        
        # by default we assume that we haven't loaded a list of stored words
        self._loaded = False
        
        
    def load(self):
        for record in Word.objects.filter(language=self.language):
            self.nwords[record.word] = record.count
        self._loaded = True
        
    def save(self):
        for word in self._trained_words:
            Word.set_word(word, self.nwords[word], language=self.language)

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
        new_words = words
        for word in new_words:
            word = unicode(word)
            
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
            # Now, suppose you train on these words:
            #   ['mike','sivia','make']
            # Then, in the first element,  you're expected to add 
            # misspelled alternatives of the word 'mike' (e.g 'mbke')
            # but thanks to this limiting list compression here below we can 
            # make sure we're not going to bother with the alternative 'make' 
            # because that's in the list of training words.
            if self._loaded:
                new_word_alternatives = [x for x in self._edits1(word) if x not in new_words]
                for variant in new_word_alternatives:
                    if variant not in self.nwords:
                        self.nwords[variant] = -1

            self._trained_words.append(word)
        

    def train(self, words):
        if not isinstance(words, (tuple, list)):
            words = [words]
            
        self._train(words)
        
    def untrain(self, words):
        if not isinstance(words, (tuple, list)):
            words = [words]
            
        self._untrain(words)
        
    def _untrain(self, words):
        for word in words:
            word = unicode(word)
            
            if word in self.nwords:
                count = self.nwords.pop(word)
                if count > 1:
                    # put it back in
                    self.nwords[word] = count - 1
                else:
                    # it's gone!
                    try:
                        self._trained_words.remove(word)
                    except ValueError:
                        pass
                    

    def correct(self, word):
        candidates = self._candidates(word)
        
        if word in self._trained_words:
            # this test is important because if you've trained a word, specifcally,
            # we can be pretty certain that it's correct and doesn't need to
            # be corrected. Without this if statement the max() function below
            # might "break" because the two top candidates have the same score
            # Suppose...:
            #   s = Spellcorrector('en')
            #   s.train('peter')
            #   s.train('petter')
            #   (at this point self.nwords is {'peter':1, 'petter':1}
            #   s.correct('peter') --> 'petter'
            # With this if statement, the word 'peter' which shares the max
            # score position won't be considered incorrect.
            return word
            
        if len(candidates) > 1:
            # take the one with the best score if it has 
            # a better score than all others
            scores = [(self.nwords.get(w, 1),w) for w in candidates]
            scores.sort()
            scores.reverse()
            winner = scores[0]
            second_place = scores[1]
            if winner[0] > second_place[0]:
                return winner[1]
            return word
        else:
            # candidates is a set so can't take the 0th element
            # so first turn it into a list
            return list(candidates)[0]
        
    def suggestions(self, word, detailed=False):
        candidates = self._candidates(word)
        suggestions = list([(self.nwords.get(x,0), x) for x in candidates])
        suggestions = [(a,b) for (a,b) in suggestions if a > 0]
        suggestions.sort()
        suggestions.reverse()
        if detailed:
            total = sum([a for (a,b) in suggestions])
            return [{'word':b,  'count':a, 'percentage': 100.0*a/total} for (a,b) in suggestions]
        else:
            return [b for (a,b) in suggestions]
        
    def count_trained_words(self):
        return len(self.nwords)
        
    def __str__(self):
        msg = 'Spellcorrector - %s different words counted %s times'
        return msg % (self.count_trained_words(), sum(self.nwords.values()))
        
    
    
def test_spellcorrector():
    sc = Spellcorrector('en')
    sc.train('peter')
    assert sc.correct('peter') == 'peter'
    assert sc.correct('petter') == 'peter'
    sc.train('petter')
    assert sc.correct('peter') == 'peter'
    assert sc.correct('petter') == 'petter'
    
    assert sc.suggestions('peterr') == ['peter']
    assert sc.suggestions('petterr') == ['petter']
    
    assert sc.suggestions('eter', detailed=True) == \
      [{'count': 1, 'percentage': 100.0, 'word': u'peter'}]
    
    
#test_spellcorrector()