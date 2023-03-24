import argparse

from loguru import logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--name",
        required=True,
        type=str,
        help="Identifiable name for the client",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    logger.info(f"Starting client: {args.name}")


if __name__ == "__main__":
    main()
