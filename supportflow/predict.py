"""Command-line prediction, sharing the same model as the app."""

import argparse
import json

from supportflow.model import TicketClassifier


def main():
    parser = argparse.ArgumentParser(description="Classify one English banking support ticket")
    parser.add_argument("text", help="Ticket text, in quotes")
    args = parser.parse_args()
    try:
        result = TicketClassifier.load().predict(args.text)
    except (FileNotFoundError, ValueError) as error:
        parser.exit(2, f"{error}\nRun python -m supportflow.train if the model is missing.\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
