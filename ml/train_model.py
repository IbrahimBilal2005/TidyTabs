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
• Dataset used: https://www.kaggle.com/datasets/timilsinabimal/newsarticlecategories?resource=download
• This dataset is saved as data.csv in ml/data 
• Transformed categories into categories appropriate for our model
• Training data is saved in ml/data as two pkl files
═══════════════════════════════════════════════════════════════════════════════════════════════════════
"""


df = pd.read_csv("ml/data/data.csv")
print(df.size)

# Change existing categories to more suitable cateogries
mapped_groups = {
    "ARTS & CULTURE": "Entertainment",
    "BUSINESS": "Finance",
    "COMEDY": "Entertainment",
    "CRIME": "News",
    "EDUCATION": "Learning",
    "ENTERTAINMENT": "Entertainment",
    "ENVIRONMENT": "News",
    "MEDIA": "News",
    "POLITICS": "News",
    "RELIGION": "News",
    "SCIENCE": "Research",        
    "SPORTS": "Entertainment",    
    "TECH": "Work",               
    "WOMEN": "News"               
}

df.replace({
    "category": mapped_groups
}, inplace=True)

# prints all the categories
categories = df.category.unique()

# Gives each ateogry a number, and saves it in column variable
label_encoder = LabelEncoder()
df['target'] = label_encoder.fit_transform(df["category"])

x = df.title
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
