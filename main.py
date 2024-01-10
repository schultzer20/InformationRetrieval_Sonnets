import requests
import json
from porter_stemmer import PorterStemmer
from collections import Counter

url = "https://poetrydb.org/author,title/Shakespeare;Sonnet"

# get request
response = requests.get(url)  # response.text == str --> we want dictionary
text = json.loads(response.text)

print(type(text))  # a list
print(type(text[0]))  # a dictionary
print(type(text[0]["title"]))  # a string
print(len(text))  # 154 bc we have 154 sonnets

# request successful?
if response.status_code == 200:
    print("The content is:")
    sonnets = []
    for item in text:
        title = item["title"]
        author = item["author"]
        lines = item["lines"]
        linecount = item["linecount"]
        sonnet_dictionary = {"title": title, "author": author, "lines": lines, "linecount": linecount}
        sonnets.append(sonnet_dictionary)

    for sonnet in sonnets:
        print(sonnet)  # prints every sonnet

else:
    print(response.status_code)

print(type(sonnets))  # a list of sonnets
print(type(sonnets[0]))  # a sonnet is a dictionary


# class Document --> parent class for Sonnet & Query
class Document:
    def __init__(self, text: str):
        self.text = text
        self.lines_stems = []

    def get_lines(self):
        if isinstance(self.text, str):
            lines = self.text.splitlines()
            if len(lines) == 1:
                return lines
            else:
                title = lines[0]
                lines = lines[1:]
                return [title, *lines]
        elif isinstance(self.text, list):
            return self.text

    def tokenize(self):
        punctuation = set(".,';:!?")  # at first: line.strip(".,;:!?'").lower().split()) BUT didn't remove all punctuation characters
        table = str.maketrans({p: ' ' for p in punctuation})

        # get words
        words_lists = []
        for line in self.get_lines():
            line_words = (line.translate(table).lower().split())
            words_lists.append(line_words)  # list of 2 lists (one list with title words + second list with line words)

        title_words = words_lists[0] if words_lists else []  # access list with title words # handle case where there's no title
        line_words = words_lists[1] if len(words_lists) > 1 else [] # access list of line words # handle case where there's no line

        # Create an instance of the stemmer
        stemmer = PorterStemmer()

        title_stemmed_words = []
        for token in title_words:
            # Use the stemmer on a token
            stemmed_token_title = stemmer.stem(token, 0, len(token) - 1)
            title_stemmed_words.append(stemmed_token_title)

        lines_stemmed_words = []
        for token in line_words:
            # Use the stemmer on a token
            stemmed_token_lines = stemmer.stem(token, 0, len(token) - 1)
            lines_stemmed_words.append(stemmed_token_lines)
        return title_stemmed_words, lines_stemmed_words


class Sonnet(Document):
    def __init__(self, sonnet_dictionary: dict):
        title_split = sonnet_dictionary["title"].split(":")  # Sonnet 1: ...
        title = title_split[1]  # really only the title
        lines = " ".join(sonnet_dictionary["lines"])  # join all lines together but with a whitespace so line-ends and line-beginnings don't get merged together
        super().__init__(title + "\n" + lines)
        self.id = int(title_split[0].replace("Sonnet", "").strip())
        self.title = title
        #self.lines = sonnet_dictionary["lines"]

    def __repr__(self) -> str:
        title, *lines = self.get_lines()
        only_lines = "\n".join(lines)
        #without_title = line_by_line[:]
        return f"\nSonnet {self.id}:{title}\n{only_lines}"

    def __str__(self):
        return self.__repr__()


instances_list = [Sonnet(sonnet_dictionary) for sonnet_dictionary in sonnets]
print(type(instances_list))  # a list
print(type(instances_list[0]))  # a Sonnet
print(instances_list)  # prints all sonnets like defined in the __repr__
print(instances_list[0])

# a sonnet
#tokenized_sonnet = instances_list[31].tokenize()
#print(tokenized_sonnet)
print(Sonnet.tokenize(instances_list[0]))  # get the stems of all the words in that sonnet [0] --> 1st sonnet


class Query(Document):
    def __init__(self, query: str):
        super().__init__([query])
        self.lines_stems = tuple(self.tokenize())  # no title just query string


class Index(dict[str, set[int]]):  # is a dict that uses str as key (stem) and a set of int as values (where stem is found)
    def __init__(self, documents: list[Sonnet]):
        super().__init__()
        self.documents = documents
        for document in documents:
            self.add(document)

    def add(self, document: Sonnet):
        title_stems, lines_stems = document.tokenize()  # get list of stems
        #title_stems = tuple(title_stems)
        #lines_stems = tuple(lines_stems)

        for stem in title_stems:  # iterate over stemmed words
            if stem not in self:  # if stem not already in self
                self[stem] = set()  # create key-value pair --> key == stem
            self[stem].add(document.id)

        for stem in lines_stems:
            if stem not in self:
                self[stem] = set()
            self[stem].add(document.id)

    def search(self, query: Query) -> list[Sonnet]:
        query_stems = query.tokenize()  # get the stem(s) of the query eg for love
        sonnet_ids = []
        num_of_stems = len(query_stems[0])
        for word in query_stems[0]:
            if word in self:
                sonnet_ids.extend(self[word])  # sonnet_ids contains all sonnets with one of the input words
        # if more than 1 query word --> we need
        if num_of_stems >= 2:
            sonnet_id_counts = Counter(sonnet_ids)
            matches = [sonnet for sonnet in instances_list if all(sonnet_id_counts[sonnet.id] >= num_of_stems for word in query_stems[0])]
        # if only 1 query word
        else:
            matches = [sonnet for sonnet in instances_list if sonnet.id in sonnet_ids]
        if len(matches) == 1:
            print(f"\nThere is {len(matches)} Sonnet from Shakespeare which contains the following word(s): {query.text}. Sonnet: {sonnet_ids}.")
        else:
            print(f"\nThere are {len(matches)} Sonnets from Shakespeare which contain the following word(s): {query.text}. Sonnets: {sonnet_ids}.")
        return matches

# if stem of query matches stem of a sonnet --> add the sonnet id to a list
# put stem of query in index of indices --> indices['stem'] in order to get the set with that stem (sonnet IDs)


indices = Index(instances_list)
print(indices)  # all unique stems as keys and their values are the ids of the sonnets with these stems
#print(len(indices))  # 2495 --> 2495 unique stems? (keys)
#print(type(indices))  # Index
#print(type(indices['from']))  # set


query = Query(input("\nWhich word(s) do you want to look up: "))  # Build the query
matching_sonnets = indices.search(query)  # Search the index with the query
# Print the results
for match in matching_sonnets:
    print('\n', sonnets[match.id - 1]['title'])
    match_lines = sonnets[match.id - 1]['lines']
    for match_line in match_lines:
        print("   ", match_line)


