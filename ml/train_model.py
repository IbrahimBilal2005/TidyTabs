#/ml/train_model.py

import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import ComplementNB
import joblib

"""
═════════════════════════════════════════════════════
📊 Model Evaluation Results
═════════════════════════════════════════════════════
• MultinomialNB        → 68% accuracy
• SVC (RBF kernel)     → 66% accuracy
• LinearSVC            → 70% accuracy
• ComplementNB         → 73% accuracy 
• BernoulliNB          → 61% accuracy
• KNeighborsClassifier → 35% accuracy 
• Source used for classifying appropriate model: https://scikit-learn.org/stable/machine_learning_map.html 
═════════════════════════════════════════════════════

═════════════════════════════════════════════════════
📊 Dataset
═══════════════════════════════════════════════════════════════════════════════════════════════════════
• Datasets used: https://www.kaggle.com/datasets/rmisra/news-category-dataset, 
                 https://www.kaggle.com/datasets/imuhammad/edx-courses
• This dataset is saved as data.csv in ml/data 
• Transformed categories into categories appropriate for our model
• Training data is saved in ml/data as two pkl files
═══════════════════════════════════════════════════════════════════════════════════════════════════════
"""

work_sites = [
    "linkedin.com",
    "slack.com",
    "github.com",
    "gitlab.com",
    "notion.so",
    "jira.com",
    "zoom.us",
    "figma.com",
    "airtable.com",
    "trello.com",
    "docs.google.com",
    "sheets.google.com",
    "meet.google.com",
    "dropbox.com",
    "microsoft365.com",
    "outlook.office.com",
    "asana.com",
    "clickup.com",
    "confluence.atlassian.com",
    "loom.com",
    "calendly.com"
]

# Combine relevant datasets to make an improved dataset

df1 = pd.read_json("ml/data/huffpost.json", lines=True)
df2 = pd.read_csv("ml/data/learning.csv")
df3 = pd.DataFrame({
    "headline": work_sites,
    "category": "TECH"  
})

df3.loc[len(df3)] = ["Learn online courses open courseware", "EDUCATION"]
df3.loc[len(df3)] = ["Online courses learn", "EDUCATION"]

df2["category"] = "EDUCATION"
df2 = df2.rename(columns={'title': 'headline', "course_url": "link"})
df = pd.concat([df1, df2, df3])
df = df.drop(columns={'n_enrolled', 'course_type', 'institution',
       'instructors', 'Level', 'subject', 'language', 'subtitles',
       'course_effort', 'course_length', 'price', 'course_description',
       'course_syllabus', 'summary'})


df = df.dropna(subset=["headline", "category"])
categories = df.category.unique()
print(df.head())


# Change existing categories to more suitable cateogries
mapped_groups = {
    "U.S. NEWS": "News",
    "WORLD NEWS": "News",
    "POLITICS": "News",
    "CRIME": "News",
    "MEDIA": "News",
    "WEIRD NEWS": "Entertainment",
    "GOOD NEWS": "News",

    "TECH": "Work",
    "BUSINESS": "Work",
    "MONEY": "Finance",
    "SCIENCE": "Research",
    "EDUCATION": "Learning",
    "COLLEGE": "Learning",
    "HEALTHY LIVING": "Learning",
    "WELLNESS": "Learning",
    "RELIGION": "News",
    "IMPACT": "News",
    "ENVIRONMENT": "News",
    "GREEN": "News",
    'SPORTS': 'Sports',

    "TRAVEL": "Travel",
    "FOOD & DRINK": "Entertainment",
    "TASTE": "Entertainment",
    "STYLE & BEAUTY": "Lifestyle",
    "STYLE": "Lifestyle",
    "HOME & LIVING": "Lifestyle",
    "WEDDINGS": "Lifestyle",
    "DIVORCE": "Lifestyle",

    "CULTURE & ARTS": "Entertainment",
    "ENTERTAINMENT": "Entertainment",
    "COMEDY": "Entertainment",
    "ARTS": "Entertainment",
    "ARTS & CULTURE": "Entertainment",

    "PARENTING": "Lifestyle",
    "PARENTS": "Lifestyle",

    "QUEER VOICES": "News",
    "WOMEN": "News",
    "BLACK VOICES": "News",
    "LATINO VOICES": "News",

    "FIFTY": "Lifestyle",
    "THE WORLDPOST": "News",
    "WORLDPOST": "News"
}


df.replace({
    "category": mapped_groups
}, inplace=True)

# Gives each ateogry a number, and saves it in column variable
label_encoder = LabelEncoder()
df['target'] = label_encoder.fit_transform(df["category"])

x = df.headline
y = df.target
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, train_size=0.8, random_state=42)

# Vectorization clf stands for classifier
clf = Pipeline([
    ('cv', CountVectorizer()),
    ('cnb', ComplementNB())
])

clf.fit(x_train, y_train)
print('Accuracy', round(clf.score(x_test, y_test), 4))

# Saves training data
joblib.dump(clf, "ml/data/tab_classifier.pkl")
joblib.dump(label_encoder, "ml/data/label_encoder.pkl")