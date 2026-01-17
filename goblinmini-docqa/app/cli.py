import argparse
import multiprocessing
import os
from .core import DocQualityChecker
from .adapters.local_model import LocalModelAdapter
from .adapters.copilot_proxy import CopilotProxyAdapter


def main():
    # CPU-aware threading for llama-cpp
    cpu_count = multiprocessing.cpu_count()
    n_threads = max(1, cpu_count // 2)
    # Allow override via environment
    n_threads = int(os.getenv("LLAMA_N_THREADS", n_threads))

    print(
        f"🔧 CPU cores detected: {cpu_count}, using {n_threads} threads for llama-cpp"
    )

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", help="relative path under DOCQA_ROOT to analyze")
    parser.add_argument("--content", "-c", help="inline content")
    parser.add_argument("--mode", choices=["local", "proxy", "auto"], default="auto")
    args = parser.parse_args()
    adapters = []
    try:
        adapters.append(LocalModelAdapter(n_threads=n_threads))
    except Exception:
        pass
    adapters.append(CopilotProxyAdapter())
    checker = DocQualityChecker(adapters=adapters)
    if args.file:
        print(checker.analyze_file(args.file))
    elif args.content:
        print(checker.analyze_content(args.content))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
