# Install required libraries (for local testing only)
# Uncomment and run these commands in your local environment if needed
# !pip install flask flask_cors spacy deep-translator gspread oauth2client gunicorn

import spacy
import subprocess
import os
import json
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from deep_translator import GoogleTranslator
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load Google NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Flask app setup
app = Flask(__name__)
CORS(app)

# English-Tamil grammar glossary
glossary = {
    "Subject": "எழுவாய்",
    "Verb": "வினைச்சொல்",
    "Object": "பொருள்",
    "Direct Object": "நேர்முக பொருள்",
    "Indirect Object": "மறைமுக பொருள்",
    "Adverb": "வினையுரிச்சொல்",
    "Adjective": "பெயரடை",
    "Complement": "நிரப்புச்சொல்",
    "Auxiliary Verb": "துணை வினைச்சொல்",
    "Sentence pattern": "வாக்கிய பாங்கு",
    "Sentence structure": "வாக்கிய அமைப்பு"
}

# Function to translate text to Tamil
def translate_to_tamil(text):
    return GoogleTranslator(source='auto', target='ta').translate(text)

# Function to analyze sentence
def analyze_sentence(sentence):
    doc = nlp(sentence)
    components = []
    sentence_structure = []
    tamil_sentence_structure = []
    sentence_pattern = []
    tamil_sentence_pattern = []

    auxiliary_verbs = []
    subject, verb, direct_object, indirect_object, adverb, adjective, complement = None, None, None, None, None, None, None

    # Identify sentence components
    for token in doc:
        role = ""
        if token.dep_ in ("nsubj", "nsubjpass"):
            role = "Subject"
            subject = token.text
        elif token.dep_ == "aux":
            role = "Auxiliary Verb"
            auxiliary_verbs.append(token.text)
        elif token.dep_ in ("ROOT", "xcomp", "ccomp") and token.text.lower() not in auxiliary_verbs:
            role = "Verb"
            verb = token.text
        elif token.dep_ == "dobj":
            role = "Direct Object"
            direct_object = token.text
        elif token.dep_ == "iobj":
            role = "Indirect Object"
            indirect_object = token.text
        elif token.dep_ in ("advmod", "npadvmod"):
            role = "Adverb"
            adverb = token.text
        elif token.dep_ in ("acomp", "attr"):
            role = "Complement"
            complement = token.text
        elif token.pos_ == "ADJ":
            role = "Adjective"
            adjective = token.text

        if role and role != "Auxiliary Verb":
            components.append((role, token.text))

    # Construct sentence pattern dynamically
    sentence_pattern = [role[:1] + ".O" if "Object" in role else role[:1] for role, _ in components]
    tamil_sentence_pattern = [glossary.get(role, role) for role, _ in components]

    # Construct sentence structure
    for role, word in components:
        sentence_structure.append(f"{role} ({word})")
        tamil_sentence_structure.append(f"{glossary.get(role, role)} ({word})")

    tamil_translation = translate_to_tamil(sentence)

    return {
        "English Sentence": sentence,
        "Tamil Sentence": tamil_translation,
        "Sentence Pattern": " + ".join(sentence_pattern),
        "Sentence Structure": " + ".join(sentence_structure),
        "Tamil Sentence Pattern": " + ".join(tamil_sentence_pattern) if tamil_sentence_pattern else "முறையை கண்டுபிடிக்க முடியவில்லை",
        "Tamil Sentence Structure": " + ".join(tamil_sentence_structure) if tamil_sentence_structure else "அமைப்பை கண்டுபிடிக்க முடியவில்லை"
    }

# Define the API endpoint
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    sentence = data.get("sentence", "")
    if not sentence:
        return jsonify({"error": "No sentence provided"}), 400

    result = analyze_sentence(sentence)
    return jsonify(result)

# Default route for testing Railway deployment
@app.route('/')
def home():
    return "Railway deployment is successful! Use the /analyze endpoint to analyze sentences."

# Run the Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
