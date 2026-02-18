"""
Ask Krishna - Interactive CLI for Talk to Krishna
Ask any life question and receive wisdom from Bhagavad Gita.
Type 'quit' or 'exit' to stop.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Fix Windows console encoding for Hindi/Sanskrit text
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gita_api import GitaAPI


def print_banner():
    print("\n" + "=" * 70)
    print("        🪈  Talk to Krishna - Bhagavad Gita Wisdom  🪈")
    print("=" * 70)
    print("  Ask any life question in Hindi, English, or Hinglish.")
    print("  Type 'quit' or 'exit' to stop.")
    print("=" * 70 + "\n")


def print_divider():
    print("\n" + "-" * 70 + "\n")


def main():
    print_banner()

    # Initialize API
    print("Loading Krishna AI...")
    try:
        api = GitaAPI()
        print("✅ Ready! Krishna is listening.\n")
    except Exception as e:
        print(f"❌ Failed to load: {e}")
        print("Make sure you have run 'python rebuild_embeddings.py' first.")
        sys.exit(1)

    conversation_history = []

    while True:
        try:
            # Get user input
            print("You: ", end="", flush=True)
            user_input = input().strip()

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit", "bye", "q"):
                print("\n🙏 Radhe Radhe! Jai Shri Krishna!\n")
                break

            # Get answer from Krishna
            print("\n🪈 Krishna: ", end="", flush=True)

            result = api.search_with_llm(
                user_input,
                conversation_history=conversation_history
            )

            answer = result.get("answer", "")

            if answer:
                print(answer)
            else:
                print("क्षमा करें, अभी उत्तर देने में असमर्थ हूँ।")

            # Save to conversation history (last 5 exchanges)
            if answer:
                conversation_history.append({
                    "question": user_input,
                    "answer": answer
                })
                if len(conversation_history) > 5:
                    conversation_history.pop(0)

            print_divider()

        except KeyboardInterrupt:
            print("\n\n🙏 Radhe Radhe! Jai Shri Krishna!\n")
            break
        except EOFError:
            break
        except Exception as e:
            print(f"\n⚠️  Error: {e}\n")


if __name__ == "__main__":
    main()
