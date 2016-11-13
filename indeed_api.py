from collections import namedtuple
import markovify
import random
import requests
from bs4 import BeautifulSoup

from env_variables import INDEED_PUBLISHER_ID, TWITTER_CONSUMER_KEY, \
    TWITTER_CONSUMER_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET


REQUEST_URL = 'http://api.indeed.com/ads/apisearch?publisher={publisher_id}&q={search_term}&l=&sort=&radius=&jt=&start=&limit=30&fromage=&filter=&latlong=%co=&chnl=&userip=&v=2'

StartingPhrase = namedtuple('StartingPhrase', 'phrase, replace_with')

STARTING_PHRASES = (
    StartingPhrase('experience', 'To have experience'),
    StartingPhrase('you will', 'To'),
    StartingPhrase('has a', 'To have a'),
    StartingPhrase('will be', 'To be'),
)

SEARCH_TERMS = (
    'python',
    'ruby',
    'software',
    'developer',
    'react',
    'javascript',
    'django',
    'agile',
    'flask',
    'rails',
    'java',
    'erlang',
    'clojure',
    'HTML',
    'CSS',
    'elixir',
)


class FiveYearPlanText(markovify.Text):
    
    def make_short_sentence_with_start(self, beginning, char_limit, **kwargs):
        """
        Tries making a sentence that begins with `beginning` string,
        which should be a string of one or two words known to exist in the 
        corpus. **kwargs are passed to `self.make_sentence`.
        """
        split = self.word_split(beginning)
        word_count = len(split)
        if word_count == self.state_size:
            init_state = tuple(split)
        elif word_count > 0 and word_count < self.state_size:
            init_state = tuple([ markovify.chain.BEGIN ] * (self.state_size - word_count) + split)
        else:
            err_msg = "`make_sentence_with_start` for this model requires a string containing 1 to {0} words. Yours has {1}: {2}".format(self.state_size, word_count, str(split))
            raise ParamError(err_msg)

        return self.make_short_sentence(char_limit, init_state=init_state, **kwargs)


def indeed_api_request(search_term):
    url = REQUEST_URL.format(
        publisher_id=INDEED_PUBLISHER_ID,
        search_term=search_term
    )

    response = requests.get(url)
    return response
    

def make_soup(response):
    xml_document = response.content
    soup = BeautifulSoup(xml_document, 'lxml')
    return soup


def get_snippets(soup):
    snippets = [snippet.contents[0] for snippet in soup.find_all('snippet')]
    snippet_string = (' ').join(snippets)
    return snippet_string 


def get_job_descriptions(soup):
    links = [url.contents[0] for url in soup.find_all('url')]
    descriptions = ''
    for link in links:
        response = requests.get(link)
        job_soup = BeautifulSoup(response.content, 'html.parser')
        job_description_list = job_soup.find(id='job_summary').find_all(string=True)
        descriptions = descriptions + ' '.join(job_description_list)

    return descriptions
 

def collect_descriptions(search_terms):
    list_of_descriptions = []

    for search_term in search_terms:
        response = indeed_api_request(search_term)
        soup = make_soup(response)
        # snippets = get_snippets(soup)
        # list_of_descriptions.append(snippets)
        descriptions = get_job_descriptions(soup)
        list_of_descriptions.append(descriptions)
    
    return list_of_descriptions


def retrieve_corpus(search_terms=('python', 'ruby', 'software')):
    list_of_descriptions = collect_descriptions(search_terms)
    corpus = ' '.join(list_of_descriptions)
    corpus = corpus.replace('\n','')
    corpus = corpus.replace('\u2019', '\'')
    return corpus


def make_plans(number_of_plans=10):
    search_terms = random.sample(SEARCH_TERMS, 3)
    corpus = retrieve_corpus(search_terms)
    text_model = FiveYearPlanText(corpus)
    return make_plan_from_corpus(text_model, number_of_plans=number_of_plans)


def make_plan_from_corpus(text_model, number_of_plans=1):
    plans = []
    for i in range(0, number_of_plans):
        starting_phrase = random.choice(STARTING_PHRASES)
        not_a_good_word = True
        while not_a_good_word:
            try:
                sentence = text_model.make_short_sentence_with_start(starting_phrase.phrase, 140)
                not_a_good_word = False
            except KeyError:
                starting_phrase = random.choice(STARTING_PHRASES)

        plan =  sentence.replace(starting_phrase.phrase, starting_phrase.replace_with)
        plans.append(plan)
    return plans
   

def get_a_good_plan():
    plans = make_plans()
    good_plans = []
    # Exclude the ones that have the word "our" or "your"
    for plan in plans:
        if 'our' not in plan and 'your' not in plan:
            good_plans.append(plan)
    return random.choice(good_plans)


