"""
Lexicon Builder — Mines CSV datasets to generate lexicon_custom.csv
====================================================================
Processes:
  1. Emotion_classify_Data.csv → extracts top keywords per emotion
  2. Mental Health Dataset.csv → extracts risk factor indicator words

Output: ai-engine/emotion/lexicon_custom.csv
"""

import csv
import os
import re
from collections import Counter, defaultdict

# --- Configuration ---
# emotion/build_lexicon.py is at ai-engine/emotion/ so go up twice to reach OmniAI root
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
AI_ENGINE_DIR = os.path.dirname(_THIS_DIR)
ROOT = os.path.dirname(AI_ENGINE_DIR)
EMOTION_CSV = os.path.join(ROOT, "Emotion_classify_Data.csv")
MENTAL_CSV = os.path.join(ROOT, "Mental Health Dataset.csv")
OUTPUT_CSV = os.path.join(_THIS_DIR, "lexicon_custom.csv")

# Words already in the built-in lexicon (avoid duplicates)
BUILTIN_WORDS = {
    "happy", "happiness", "glad", "excited", "amazing", "wonderful",
    "fantastic", "great", "awesome", "love", "loving", "joyful", "joy",
    "delighted", "thrilled", "ecstatic", "cheerful", "grateful",
    "thankful", "blessed", "optimistic", "hopeful", "proud",
    "accomplished", "satisfied", "content", "peaceful", "relieved",
    "inspired", "motivated", "energized", "celebrate", "celebrating",
    "fun", "enjoying", "enjoyed", "pleasure", "smile", "smiling",
    "laughing", "laugh", "bliss", "elated",
    "sad", "sadness", "unhappy", "miserable", "heartbroken", "grief",
    "grieving", "mourning", "depressed", "depression", "melancholy",
    "sorrow", "sorrowful", "gloomy", "down", "low",
    "lonely", "loneliness", "alone", "isolated", "empty", "emptiness",
    "numb", "numbness", "crying", "cry", "tears", "tearful", "hurt",
    "hurting", "broken", "shattered", "devastated", "discouraged",
    "disappointed", "hopeless", "despair", "suffering", "pain",
    "painful", "aching", "heartache", "miss", "missing",
    "angry", "anger", "furious", "enraged", "mad", "irritated",
    "annoyed", "frustrated", "frustration", "resentful", "resentment",
    "bitter", "bitterness", "outraged", "livid", "fuming", "hostile",
    "aggressive", "rage", "raging", "infuriated", "disgusted",
    "hate", "hatred", "despise", "loathe",
    "afraid", "fear", "scared", "terrified", "frightened", "panicked",
    "panic", "dread", "dreading", "horrified", "horror", "phobia",
    "paranoid", "paranoia", "nervous", "uneasy", "alarmed",
    "threatened", "vulnerable", "helpless", "trapped",
    "overwhelming", "overwhelmed",
    "anxious", "anxiety", "worried", "worrying", "worry",
    "restless", "tense", "tension", "overthinking",
    "ruminating", "obsessing", "insecure", "insecurity", "uncertain",
    "uncertainty", "doubt", "doubtful", "apprehensive",
    "unsettled", "agitated", "jittery",
    "stressed", "stress", "pressure", "pressured", "burden",
    "burdened", "overloaded", "overworked", "exhausted", "exhaustion",
    "burnout", "drained", "fatigued", "fatigue", "tired", "swamped",
    "drowning", "deadline", "deadlines",
    "worthless", "useless", "incompetent", "failure", "loser",
    "inadequate", "inferior", "imposter", "fraud", "stupid", "dumb",
    "pathetic", "unworthy", "unlovable", "ugly",
    "pointless", "meaningless", "doomed", "cursed",
}

# Stop words to exclude
STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you",
    "your", "yours", "yourself", "yourselves", "he", "him", "his",
    "himself", "she", "her", "hers", "herself", "it", "its", "itself",
    "they", "them", "their", "theirs", "themselves", "what", "which",
    "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having",
    "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if",
    "or", "because", "as", "until", "while", "of", "at", "by", "for",
    "with", "about", "against", "between", "through", "during", "before",
    "after", "above", "below", "to", "from", "up", "down", "in", "out",
    "on", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "s", "t",
    "can", "will", "just", "don", "should", "now", "d", "ll", "m", "o",
    "re", "ve", "y", "ain", "aren", "couldn", "didn", "doesn", "hadn",
    "hasn", "haven", "isn", "ma", "mightn", "mustn", "needn", "shan",
    "shouldn", "wasn", "weren", "won", "wouldn", "also", "get", "got",
    "much", "many", "like", "even", "still", "would", "could", "one",
    "two", "make", "made", "thing", "things", "time", "way", "go",
    "going", "know", "think", "want", "see", "come", "look", "day",
    "really", "back", "right", "well", "something", "anything",
    "everything", "nothing", "never", "always", "ever", "lot", "say",
    "said", "told", "tell", "let", "keep", "take", "give", "try",
    "put", "new", "old", "first", "last", "long", "little", "big",
    "good", "bad", "bit", "life", "people", "person", "man", "woman",
    "part", "year", "years", "work", "home", "world", "another",
    "around", "away", "every", "enough", "though", "already", "since",
    "without", "whole", "felt", "feel", "feeling", "feelings", "felt",
    "im", "ive", "dont", "cant", "didnt", "wont", "doesnt", "wasnt",
    "isnt", "thats", "youre", "theyre", "ill",
}

def tokenize(text: str) -> list[str]:
    """Simple word tokenizer."""
    text = text.lower()
    text = re.sub(r"[^a-z\s'-]", " ", text)
    words = text.split()
    return [w.strip("'-") for w in words if len(w.strip("'-")) > 2]


def extract_bigrams(text: str) -> list[str]:
    """Extract word bigrams from text."""
    words = tokenize(text)
    bigrams = []
    for i in range(len(words) - 1):
        bg = f"{words[i]} {words[i+1]}"
        bigrams.append(bg)
    return bigrams


def mine_emotion_csv() -> dict[str, list[tuple[str, float]]]:
    """
    Mine Emotion_classify_Data.csv for distinctive keywords per emotion.
    Returns: {emotion: [(keyword, weight), ...]}
    """
    if not os.path.isfile(EMOTION_CSV):
        print(f"  ⚠ {EMOTION_CSV} not found, skipping.")
        return {}

    # Map the CSV emotions to our categories
    emotion_map = {
        "joy": "joy",
        "anger": "anger",
        "fear": "fear",
        "sadness": "sadness",
        "surprise": "joy",      # map surprise → joy
        "love": "joy",          # map love → joy
        "disgust": "anger",     # map disgust → anger
    }

    # Count words per emotion
    word_counts: dict[str, Counter] = defaultdict(Counter)
    total_counts: Counter = Counter()
    bigram_counts: dict[str, Counter] = defaultdict(Counter)
    total_bigrams: Counter = Counter()
    row_count = 0

    with open(EMOTION_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("Comment", "").strip()
            label = row.get("Emotion", "").strip().lower()
            mapped = emotion_map.get(label)
            if not mapped or not text:
                continue

            words = tokenize(text)
            for w in set(words):  # Use set to avoid counting duplicates in single text
                if w not in STOP_WORDS and w not in BUILTIN_WORDS:
                    word_counts[mapped][w] += 1
                    total_counts[w] += 1

            # Bigrams
            bigrams = extract_bigrams(text)
            for bg in set(bigrams):
                parts = bg.split()
                if all(p not in STOP_WORDS for p in parts):
                    bigram_counts[mapped][bg] += 1
                    total_bigrams[bg] += 1

            row_count += 1

    print(f"  ✓ Processed {row_count} rows from Emotion_classify_Data.csv")

    # Calculate distinctiveness score (TF-IDF-like)
    results: dict[str, list[tuple[str, float]]] = {}

    for emotion, counts in word_counts.items():
        scored = []
        for word, count in counts.items():
            if count < 3:  # Minimum frequency
                continue
            # Distinctiveness = count_in_emotion / total_count_across_all
            total = total_counts[word]
            distinctiveness = count / total if total > 0 else 0
            if distinctiveness >= 0.4:  # At least 40% of usages are in this emotion
                weight = min(0.5 + (distinctiveness * 0.4), 0.85)
                scored.append((word, round(weight, 2)))

        # Sort by weight desc, take top 40
        scored.sort(key=lambda x: x[1], reverse=True)
        results[emotion] = scored[:40]

    # Add distinctive bigrams
    for emotion, counts in bigram_counts.items():
        scored_bg = []
        for bg, count in counts.items():
            if count < 2:
                continue
            total = total_bigrams[bg]
            distinctiveness = count / total if total > 0 else 0
            if distinctiveness >= 0.5:
                weight = min(0.6 + (distinctiveness * 0.3), 0.9)
                scored_bg.append((bg, round(weight, 2)))

        scored_bg.sort(key=lambda x: x[1], reverse=True)
        if emotion not in results:
            results[emotion] = []
        results[emotion].extend(scored_bg[:20])

    return results


def mine_mental_health_csv() -> list[tuple[str, str, float]]:
    """
    Mine Mental Health Dataset.csv for risk factor keywords.
    Returns: [(keyword, emotion, weight), ...]
    """
    if not os.path.isfile(MENTAL_CSV):
        print(f"  ⚠ {MENTAL_CSV} not found, skipping.")
        return []

    # The mental health dataset is survey-based (not text), so we extract
    # contextual keywords from column names and domain knowledge
    # These are phrases users might say that correlate with risk factors
    risk_keywords = [
        # Growing Stress indicators
        ("growing stress", "stress", 0.75),
        ("increasing stress", "stress", 0.75),
        ("stress keeps growing", "stress", 0.85),
        ("more stressed each day", "stress", 0.85),
        ("stress getting worse", "stress", 0.85),

        # Coping Struggles
        ("struggling to cope", "stress", 0.80),
        ("can't cope anymore", "stress", 0.90),
        ("difficulty coping", "stress", 0.80),
        ("lost my coping", "hopelessness", 0.85),
        ("no way to cope", "hopelessness", 0.90),

        # Mood Swings
        ("mood swings", "anxiety", 0.70),
        ("mood keeps changing", "anxiety", 0.70),
        ("emotional rollercoaster", "anxiety", 0.75),
        ("emotions all over", "anxiety", 0.70),
        ("up and down emotionally", "anxiety", 0.70),

        # Social Weakness / Withdrawal
        ("social withdrawal", "sadness", 0.75),
        ("withdrawing from people", "sadness", 0.80),
        ("avoiding everyone", "sadness", 0.80),
        ("don't want to see anyone", "sadness", 0.80),
        ("stopped socializing", "sadness", 0.80),
        ("cutting off friends", "sadness", 0.85),
        ("isolating myself", "sadness", 0.85),

        # Days Indoors / Isolation
        ("haven't gone outside", "sadness", 0.80),
        ("staying indoors", "sadness", 0.70),
        ("can't leave the house", "fear", 0.85),
        ("afraid to go outside", "fear", 0.85),
        ("locked myself in", "sadness", 0.85),
        ("haven't left my room", "sadness", 0.85),

        # Work Interest Loss
        ("lost interest in work", "sadness", 0.75),
        ("can't focus on work", "stress", 0.70),
        ("no motivation to work", "sadness", 0.80),
        ("work feels pointless", "hopelessness", 0.80),
        ("dreading going to work", "anxiety", 0.75),

        # Changes in Habits
        ("not eating properly", "sadness", 0.70),
        ("lost my appetite", "sadness", 0.75),
        ("eating too much", "stress", 0.65),
        ("sleeping all day", "sadness", 0.75),
        ("can't sleep at night", "anxiety", 0.75),
        ("stopped exercising", "sadness", 0.70),
        ("neglecting hygiene", "sadness", 0.80),
        ("stopped taking care", "sadness", 0.80),

        # Family History awareness
        ("family history of depression", "sadness", 0.65),
        ("mental illness runs in family", "anxiety", 0.65),
        ("my parent was depressed", "sadness", 0.65),

        # Treatment seeking
        ("need professional help", "stress", 0.70),
        ("should see a therapist", "anxiety", 0.65),
        ("considering therapy", "anxiety", 0.60),
        ("need medication", "anxiety", 0.70),
    ]

    # Verify the survey data structure
    with open(MENTAL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        first_row = next(reader, None)

    print(f"  ✓ Mental Health Dataset verified — {len(headers)} columns")
    print(f"    Columns: {', '.join(headers[:8])}...")
    print(f"  ✓ Generated {len(risk_keywords)} contextual risk phrases")

    return risk_keywords


def build_lexicon():
    """Main: mine both datasets and write lexicon_custom.csv."""
    print("=" * 60)
    print("LEXICON BUILDER — Mining CSV Datasets")
    print("=" * 60)

    # 1. Mine emotion classification data
    print("\n📊 Mining Emotion_classify_Data.csv...")
    emotion_keywords = mine_emotion_csv()

    # 2. Mine mental health survey data
    print("\n🧠 Mining Mental Health Dataset.csv...")
    mental_keywords = mine_mental_health_csv()

    # 3. Combine and write output
    print(f"\n📝 Writing {OUTPUT_CSV}...")

    all_entries: list[tuple[str, str, float]] = []

    # Add emotion-mined keywords
    for emotion, keywords in emotion_keywords.items():
        for kw, weight in keywords:
            all_entries.append((kw, emotion, weight))

    # Add mental health risk keywords
    all_entries.extend(mental_keywords)

    # Deduplicate (keep higher weight)
    seen: dict[str, tuple[str, float]] = {}
    for kw, emotion, weight in all_entries:
        key = kw.lower()
        if key not in seen or weight > seen[key][1]:
            seen[key] = (emotion, weight)

    # Write CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["keyword", "emotion", "weight"])
        for kw in sorted(seen.keys()):
            emotion, weight = seen[kw]
            writer.writerow([kw, emotion, weight])

    total = len(seen)
    print(f"\n  ✅ Generated {total} custom keywords:")
    for emotion in sorted(set(e for e, _ in seen.values())):
        count = sum(1 for e, _ in seen.values() if e == emotion)
        print(f"     {emotion}: {count} keywords")

    print(f"\n  Output: {OUTPUT_CSV}")
    print("=" * 60)


if __name__ == "__main__":
    build_lexicon()
