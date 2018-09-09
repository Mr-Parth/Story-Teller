import nltk
import math
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import pandas as pd
from fuzzywuzzy import process


stop_words = set(stopwords.words("english"))
ps = PorterStemmer()


def process_str(string):
    # Token
    tokens = nltk.word_tokenize(string)
    filtered_string = []

    for w in tokens:
        if w not in stop_words:
            filtered_string.append(w)

    stemmed_string = []
    for w in filtered_string:
        stemmed_string.append(ps.stem(w))

    return " ".join(stemmed_string)


data = pd.read_csv("hack.csv")
data = data[data["Tier"] == "Total"]
columns = ["".join(process_str(i)) for i in list(data.columns)]
states = [ps.stem(str(i)) for i in pd.unique(data["State"]).tolist()]
districts = [ps.stem(str(i)) for i in pd.unique(data["District"]).tolist()]


def analyze(string):
    try:
        our_str = process_str(string)
        val = max([[process.extractOne(our_str, i[0]), i[1]]
                   for i in [[states, "State"], [districts, "District"]]], key=lambda x: x[0][1])

        cat = val[1] if val[0][1] >= 85 else "Nation"
        if cat == "State":
            val = pd.unique(data["State"]).tolist()[
                states.index(val[0][0])] if val[0][1] >= 70 else ""
        elif cat == "District":
            val = pd.unique(data["District"]).tolist()[
                states.index(val[0][0])] if val[0][1] >= 70 else ""
        else:
            val = ""

        col = data.columns[columns.index(process.extractOne(our_str, columns)[
            0])] if process.extractOne(our_str, columns)[1] >= 70 else "Did'nt Understand"
    except:
        cat, val, col = "", "", ""
    return [cat, val, col, "", "", ""]


def suggest(string):
    try:
        our_str = process_str(string)
        val = max([[process.extractOne(our_str, i[0]), i[1]]
                   for i in [[states, "State"], [districts, "District"]]], key=lambda x: x[0][1])

        cat = val[1] if val[0][1] >= 85 else "Nation"
        if cat == "State":
            val = pd.unique(data["State"]).tolist()[
                states.index(val[0][0])] if val[0][1] >= 70 else ""
        elif cat == "District":
            val = pd.unique(data["District"]).tolist()[
                states.index(val[0][0])] if val[0][1] >= 70 else ""
        else:
            val = ""

        col = data.columns[columns.index(process.extractOne(our_str, columns)[
            0])] if process.extractOne(our_str, columns)[1] >= 70 else "Did'nt Understand"

        suggest = []

        for i in process.extract(our_str, columns):
            if i[1] >= 70:
                suggest.append(data.columns[columns.index(i[0])])
            else:
                break
    except:
        suggest = []
    return suggest
