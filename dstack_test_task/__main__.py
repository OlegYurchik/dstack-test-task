import logging

from .cli import get_cli


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    cli = get_cli()
    cli()
