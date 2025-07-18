import json
import joblib
import numpy as np
from sklearn.preprocessing import LabelEncoder

from datasets import Dataset
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments
)
import torch

# 1. Load your tab title dataset
with open("ml/training_data.json", "r") as f:
    data = json.load(f)

titles = [item["title"] for item in data]
categories = [item["category"] for item in data]

# 2. Convert category labels to integers using LabelEncoder
le = LabelEncoder()
encoded_labels = le.fit_transform(categories)

# Save the label encoder to use during inference
joblib.dump(le, "ml/label_encoder.joblib")

# 3. Convert to HuggingFace Dataset format
dataset = Dataset.from_dict({
    "text": titles,
    "label": encoded_labels
})

# 4. Load the DistilBERT tokenizer
tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

# 5. Tokenize the tab titles with fixed max_length padding
def tokenize_function(batch):
    return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=32)

tokenized_dataset = dataset.map(tokenize_function, batched=True)

# 6. Load the DistilBERT model for classification
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=len(le.classes_)
)

# 7. Define training settings
training_args = TrainingArguments(
    output_dir="./ml/distilbert_tab_classifier",
    per_device_train_batch_size=8,
    num_train_epochs=4,
    logging_dir="./ml/logs",
    logging_steps=10,
    save_strategy="epoch"
)

# 8. Create a Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset
)

# 9. Train the model
trainer.train()

# 10. Save model and tokenizer
model.save_pretrained("ml/distilbert_tab_classifier")
tokenizer.save_pretrained("ml/distilbert_tab_classifier")
