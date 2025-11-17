# **Revised Prompts**

## Prompt 1

Wrap these into a function without modifying the API calls.

## Prompt 2

Wrap these into a function that accepts model, instruction, input, topic, and temperature as arguments.

## Prompt 3

Design a general-purpose function that asks a single question and returns a response.

## Prompt 4

Design a function named `translator`.
Its input is either Chinese or English, and it should translate the text into the other language.
When responding, structure the output into two parts: the original text and the translated text.

## Prompt 5

Design a function that summarizes news articles using the 5W1H framework and outputs the results in a structured JSON schema.

## Prompt 6

Correct the error using the following sample code:

```python
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class ResearchPaperExtraction(BaseModel):
    title: str
    authors: list[str]
    abstract: str
    keywords: list[str]

response = client.responses.parse(
    model="gpt-4o-2024-08-06",
    input=[
        {
            "role": "system",
            "content": "You are an expert at structured data extraction. You will be given unstructured text from a research paper and should convert it into the given structure.",
        },
        {"role": "user", "content": "..."},
    ],
    text_format=ResearchPaperExtraction,
)

research_paper = response.output_parsed
```

## Prompt 7

An error occurred.

## Prompt 8

Design a task dispatcher that uses `ask_question()` to determine which function to execute.
For example, when the user says “請幫我翻譯…”, the dispatcher should call the `translator()` function.

## Prompt 9

Could you copy all the prompts I have made in this chat session?

## Prompt 10

Can you export all my prompts from this chat session as a Markdown file?
