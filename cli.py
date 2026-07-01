import argparse
from agent import create_agent

def main():
    parser = argparse.ArgumentParser(description="FAQ‑bot CLI")
    parser.add_argument(
        "-q",
        "--question",
        type=str,
        help="Predefined question to ask the bot (use 'chroma1', 'chroma2', or 'mcp').",
    )
    args = parser.parse_args()

    executor = create_agent()

    predefined = {
        "chroma1": "What is the deadline for assignment 3?",
        "chroma2": "Explain the concept of polymorphism.",
        "mcp": "When does the course start next semester?",
    }

    if args.question:
        question = predefined.get(args.question.lower())
        if not question:
            print("Unknown predefined question. Use chroma1, chroma2, or mcp.")
            return
        result = executor.invoke({"input": question})
        print(result["output"])
    else:
        while True:
            q = input("Question: ")
            if not q.strip():
                break
            result = executor.invoke({"input": q})
            print(result["output"])

if __name__ == "__main__":
    main()
