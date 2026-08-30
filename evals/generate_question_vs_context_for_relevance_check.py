import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableLambda

class RelevanceResponseModel(BaseModel):
    question_id: int = Field(description="unique identifier for the question")
    context_id: int = Field(description="unique identifier for the context")
    relevant: bool = Field(description="True if context is relevant to question, else False.")

def generate_question_vs_context_for_relevance_check(questions_path_json: str, contexts_path_json: str):
    with open(questions_path_json, "r", encoding="utf-8") as f:
            questions = json.load(f)
    with open(contexts_path_json, "r", encoding="utf-8") as f:
            contexts = json.load(f)
    qc_pairs = []
    for i, question in enumerate(questions):
        for j, context in enumerate(contexts):
            qc_pair = { "question_id": i, "question": question, "context_id": j, "context": context }
            qc_pairs.append(qc_pair)
    return qc_pairs

check_relevance_prompt_template = ChatPromptTemplate.from_messages([
    ("system", """
You will be given a structured JSON input having four fields:
1. question_id: unique identifier for given question.
2. question: the question itself.
3. context_id: unique identifier for given context.
4. context: the context itself.

Your task is to generate a structured output in JSON format of structure:
{{ question_id: *same as input, context_id: *same as input, relevant: boolean }}

where `relevant` is `True` if the given context is relevant to the question. Otherwise `False`.
"""),
    ("human", """
{{
question_id: {question_id},
question: {question},
context_id: {context_id},
context: {context}
}}
""")
])

check_relevance_agent = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-8b",
    temperature=0
)
check_relevance_agent_structured = check_relevance_agent.with_structured_output(RelevanceResponseModel)

def check_relevance_with_llm(qc_pairs: List[Dict[str, Any]]):
    check_relevance_chain = (
        check_relevance_prompt_template
        | check_relevance_agent_structured
        | RunnableLambda(lambda x: x.model_dump())
    )
    res = check_relevance_chain.batch(qc_pairs)
    return res

# simulated
def generate_question_ground_truth_contexts(qc_pairs: List[Dict[str, Any]], questions: List[str], dest_path: str):
    output = [{
        "question_id": i,
        "ground_truth_context_ids": []
    } for i in range(len(questions))]
    batch_results = check_relevance_with_llm(qc_pairs)
    for resObj in batch_results:
        if resObj['relevant']:
            output[resObj['question_id']]['ground_truth_context_ids'].append(resObj['context_id'])
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)    