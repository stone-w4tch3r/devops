#! /usr/bin/env python3

import argparse
import logging
import os

import yaml
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv


def load_env_vars(env_file='.env'):
    if os.path.exists(env_file):
        load_dotenv(env_file)
        logging.info(f"Loaded environment variables from {env_file}")
    else:
        logging.warning(f"No {env_file} file found. Using system environment variables.")


def process_template(template_path: str, output_path: str, overwrite: bool = False) -> None:
    env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))

    try:
        template = env.get_template(os.path.basename(template_path))
    except Exception as e:
        raise ValueError(f"Failed to load template {template_path}: {e}")

    # Load environment variables
    load_env_vars()

    rendered = template.render(os=os, enumerate=enumerate, env=os.environ)

    if ".yaml" in template_path or ".yml" in template_path:
        try:
            yaml.safe_load(rendered)
        except yaml.YAMLError as e:
            raise ValueError(f"The rendered template is not valid YAML: {e}")

    logging.info(f"Preview:\n{rendered}")

    if os.path.exists(output_path):
        if not overwrite:
            raise FileExistsError(f"The output file {output_path} already exists. Use --overwrite to force.")
        else:
            logging.warning(f"The output file {output_path} already exists. Overwriting.")

    if not os.access(os.path.dirname(output_path) or '.', os.W_OK):
        raise PermissionError(f"No write permission for the output directory of {output_path}")

    with open(output_path, 'w') as f:
        f.write(rendered)

    logging.info(f"Successfully processed {template_path} and wrote output to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Process Jinja2 template.")
    parser.add_argument("template", help="Path to the Jinja2 template file (.j2)")
    parser.add_argument("-o", "--output", default=None, help="Output file name")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output file if it exists")
    parser.add_argument("--env-file", default=".env", help="Path to the .env file (default: .env)")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    try:
        if not os.path.isfile(args.template):
            raise FileNotFoundError(f"The file {args.template} does not exist.")
        if args.output is None:
            if args.template.endswith(".j2"):
                args.output = args.template.removesuffix(".j2")
            else:
                raise ValueError("Output file name not specified and cannot be inferred from template file name.")
        load_env_vars(args.env_file)
        process_template(args.template, args.output, args.overwrite)
    except Exception as e:
        logging.error(f"{type(e).__name__}: {e}")
        exit(1)


if __name__ == "__main__":
    main()
