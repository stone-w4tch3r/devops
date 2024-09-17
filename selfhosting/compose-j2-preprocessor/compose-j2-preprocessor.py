#! /usr/bin/env python3

import argparse
import logging
import os

import yaml
from jinja2 import Environment, FileSystemLoader


def process_template(template_path: str, output_path: str, overwrite: bool = False, preview: bool = False) -> None:
    env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))

    try:
        template = env.get_template(os.path.basename(template_path))
    except Exception as e:
        raise ValueError(f"Failed to load template {template_path}: {e}")

    rendered = template.render(os=os, enumerate=enumerate)

    try:
        yaml.safe_load(rendered)
    except yaml.YAMLError as e:
        raise ValueError(f"The rendered template is not valid YAML: {e}")

    if preview:
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
    parser = argparse.ArgumentParser(description="Process Docker Compose Jinja2 template.")
    parser.add_argument("template", help="Path to the Jinja2 template file (.j2)")
    parser.add_argument("-o", "--output", default="docker-compose-j2.yml", help="Output file name")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite output file if it exists")
    parser.add_argument("--preview", action="store_true", help="Preview the output before writing")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    try:
        if not os.path.isfile(args.template):
            raise FileNotFoundError(f"The file {args.template} does not exist.")
        output_path = args.output if args.output.endswith(('.yml', '.yaml')) else args.output + '.yml'
        process_template(args.template, output_path, args.overwrite, args.preview)
    except Exception as e:
        logging.error(f"{type(e).__name__}: {e}")
        exit(1)


if __name__ == "__main__":
    main()
