import argparse
from agent import create_agent


def main():
    parser = argparse.ArgumentParser(description="FAQ Bot CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Predefined questions
    parser_qdrant1 = subparsers.add_parser("q1", help="Ask about course content (Chroma)")
    parser_qdrant2 = subparsers.add_parser("q2", help="Ask about prerequisites (Chroma)")
    parser_mcp = subparsers.add_parser("mcp", help="Ask about schedule (MCP tool)")

    parser_interactive = subparsers.add_parser("interactive", help="Interactive mode")

    args = parser.parse_args()

    executor = create_agent()
    if args.command == "q1":
        question = "What is the course about?"
    elif args.command == "q2":
        question = "What are the prerequisites?"
    elif args.command == "mcp":
        question = "When does week 3 start?"
    else:
        print("Enter your question:")
        question = input("> ")

    result = executor.invoke({"input": question})
    print("\nAnswer:\n", result["output"])


if __name__ == "__main__":
    main()
