import os
import dspy
from dotenv import load_dotenv

load_dotenv()

# DSPy natively supports Mistral via LiteLLM — no custom wrapper needed
mistral_lm = dspy.LM(
    model="mistral/mistral-large-latest",
    api_key=os.getenv("MISTRAL_API_KEY"),
    temperature=0.3,
)

dspy.configure(lm=mistral_lm)


# --- DSPy Signatures ---

class QASignature(dspy.Signature):
    """Answer the question clearly and concisely."""
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()


class ContextQASignature(dspy.Signature):
    """Answer the question using the provided context."""
    context: str = dspy.InputField(desc="Previous conversation or retrieved data")
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()


class SummarizeSignature(dspy.Signature):
    """Summarize the given text into key points."""
    text: str = dspy.InputField()
    summary: str = dspy.OutputField()


class ClassifySignature(dspy.Signature):
    """Classify the intent of the user query."""
    query: str = dspy.InputField()
    label: str = dspy.OutputField(desc="One of: question, command, search, calculation, other")


# --- DSPy Modules ---

class QAModule(dspy.Module):
    def __init__(self):
        self.predict = dspy.Predict(QASignature)

    def forward(self, question: str):
        return self.predict(question=question)  # returns prediction object with .answer


class ContextQAModule(dspy.Module):
    def __init__(self):
        self.predict = dspy.Predict(ContextQASignature)

    def forward(self, question: str, context: str):
        return self.predict(question=question, context=context)


class SummarizeModule(dspy.Module):
    def __init__(self):
        self.predict = dspy.Predict(SummarizeSignature)

    def forward(self, text: str) -> str:
        return self.predict(text=text).summary


class ClassifyModule(dspy.Module):
    def __init__(self):
        self.predict = dspy.Predict(ClassifySignature)

    def forward(self, query: str) -> str:
        return self.predict(query=query).label


# Singleton instances
qa = QAModule()
qa_context = ContextQAModule()
summarize = SummarizeModule()
classify = ClassifyModule()
