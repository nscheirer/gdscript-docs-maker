"""Merges JSON dumped by Godot's gdscript language server or converts it to a markdown
document.
"""
import json
import logging
import os
import shutil
import sys
from argparse import Namespace
from itertools import repeat
from typing import List

import pkg_resources

from . import command_line
from .config import LOG_LEVELS, LOGGER
from .convert_to_markdown import convert_to_markdown
from .gdscript_objects import GDScriptClasses, ProjectInfo
from .make_markdown import MarkdownDocument


def main():
    args: Namespace = command_line.parse()

    if args.version:
        print(pkg_resources.get_distribution("gdscript-docs-maker").version)
        sys.exit()
        pass

    logging.basicConfig(level=LOG_LEVELS[min(args.verbose, len(LOG_LEVELS) - 1)])
    LOGGER.debug("Output format: {}".format(args.format))
    json_files: List[str] = [f for f in args.files if f.lower().endswith(".json")]
    LOGGER.info("Processing JSON files: {}".format(json_files))
    for f in json_files:
        with open(f, "r") as json_file:
            data: list = json.loads(json_file.read())
            project_info: ProjectInfo = ProjectInfo.from_dict(data)
            classes: GDScriptClasses = GDScriptClasses.from_dict_list(data["classes"])
            classes_count: int = len(classes)

            LOGGER.info(
                "Project {}, version {}".format(project_info.name, project_info.version)
            )
            LOGGER.info(
                "Processing {} classes in {}".format(classes_count, os.path.basename(f))
            )

            if args.include:
                copy(args.include, args.path)
                pass

            documents: List[MarkdownDocument] = convert_to_markdown(
                classes, args, project_info
            )
            if args.dry_run:
                LOGGER.debug("Generated {} markdown documents.".format(len(documents)))
                list(map(lambda doc: LOGGER.debug(doc), documents))
            else:
                if not os.path.exists(args.path):
                    LOGGER.info("Creating directory " + args.path)
                    os.mkdir(args.path)
                    pass

                if not os.path.exists(os.path.join(args.path, "pages")):
                    LOGGER.info("Creating directory " + os.path.join(args.path, "pages"))
                    os.mkdir(os.path.join(args.path, "pages"))
                    pass

                LOGGER.info(
                    "Saving {} markdown files to {}".format(len(documents), args.path)
                )
                list(map(save, documents, repeat(args.path)))
                pass
            pass
        pass
    pass


def save(
    document: MarkdownDocument,
    dirpath: str,
):
    path: str = os.path.join(dirpath, "pages", document.get_filename())
    if document.title == "index":
        path: str = os.path.join(dirpath, document.get_filename())
        pass

    with open(path, "w") as file_out:
        LOGGER.debug("Saving markdown file " + path)
        file_out.write(document.as_string())
        pass
    pass


def copy(src, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    ignore_func = lambda d, files: [f for f in files if os.path.isfile(os.path.join(d, f)) and os.path.splitext(f)[1] not in ['.png', '.md']]
    shutil.copytree(src, dest, ignore=ignore_func)
    pass


if __name__ == "__main__":
    main()
