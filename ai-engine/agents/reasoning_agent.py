from app.dspy_module import QAModule

qa = QAModule()

def reasoning_agent(state):
    messages = state["messages"]
    query = messages[-1].content

    result = qa(question=query)

    return {
        "messages": [("assistant", result.answer)]
    }
