# ######################################################################
#
# Syntax for cross-references to the Reference Manual:
#   `ClassName^`
#       generates a link from `ClassName` to the class doc page
#   `functionName(*)^`
#       generates a link from `functionName(*)` to the function doc page
#   `ClassName.methodName(*)^`
#       generates a link from `ClassName.methodName(*)` to the method
#       doc page.
#   `(ClassName.)methodName(*)^`
#       generates a link from `methodName(*)` to the method doc page.
#   `package.functionName(*)^`
#       generates a link from `functionName` to the function doc page
#   `(package.)functionName(*)^`
#       generates a link from `functionName` to the function doc page,
#       hiding the package.
# ######################################################################
import os
import re
from typing import Dict
import logging
import json
from weakref import ref

from importlib_metadata import pass_none

def define_env(env):
    """
    Mandatory to make this a proper MdDocs macro
    """
    pass


TOC_ENTRY_PART1 = r"<li\s*class=\"md-nav__item\">\s*<a\s*href=\""
TOC_ENTRY_PART2 = r"\"\s*class=\"md-nav__link\">([^<]*)</a>\s*</li>\s*"
# XREF_RE details:
#  group(1) - A potential opening '('.
#  group(2) - The package, class or function name with a trailing '.'.
#    Can be empty.
#  group(3) - The name of a method, or the last sub-package name.
#  group(4) - The function parameters, with their ().
XREF_RE = re.compile(r"<code>(\()?((?:[^\d\W]\w*\.)*)"
                     + r"(?:\))?([^\d\W]\w*)(\(.*?\))?\^</code>")
                      

def find_dummy_h3_entries(content: str) -> Dict[str, str]:
    """
    Find 'dummy <h3>' entries.

    These are <h3> tags that are just redirections to another page.
    These need to be removed, and redirection must be used in TOC.
    """

    ids = {}
    TOC_ENTRY = re.compile(TOC_ENTRY_PART1 + r"(#[^\"]+)" + TOC_ENTRY_PART2, re.M | re.S)
    while True:
        toc_entry = TOC_ENTRY.search(content)
        if toc_entry is None:
            break
        content = content[toc_entry.end() :]
        id = toc_entry.group(1)[1:]
        dummy_h3 = re.search(r"<h3\s+id=\"" + id + r"\">\s*<a\s+href=\"(.*?)\".*?</h3>", content, re.M | re.S)
        if dummy_h3 is not None:
            ids[id] = dummy_h3.group(1)
    return ids


def remove_dummy_h3(content: str, ids: Dict[str, str]) -> str:
    """
    Removes dummy <h3> entries and fix TOC.
    """

    for id, redirect in ids.items():
        # Replace redirection in TOC
        content = re.sub(
            TOC_ENTRY_PART1 + "#" + id + TOC_ENTRY_PART2,
            '<li class="md-nav__item"><a href="' + redirect + '" class="md-nav__link">\\1</a></li>\n',
            content,
            re.M | re.S,
        )
        # Remove dummy <h3>
        content = re.sub(r"<h3\s+id=\"" + id + r"\">\s*<a\s+href=\".*?\".*?</h3>", "", content, re.M | re.S)
    return content


def on_post_build(env):
    "Post-build actions for Taipy documentation"

    site_dir = env.conf["site_dir"]
    log = logging.getLogger("mkdocs")
    xrefs = {}
    if os.path.exists(site_dir + "/manuals/xrefs"):
        with open(site_dir + "/manuals/xrefs") as xrefs_file:
            xrefs = json.load(xrefs_file)
    if xrefs is None:
        log.error(f"Could not find xrefs in /manuals/xrefs")
    x_packages = set()
    for ps in xrefs.values():
        x_packages.add(ps[0])
        if ps[2]:
            x_packages.update(ps[2])
    manuals_files_path = os.path.join(site_dir, "manuals")
    ref_files_path = os.path.join(manuals_files_path, "reference")
    for root, _, file_list in os.walk(site_dir):
        for f in file_list:
            # Post-process generated '.html' files
            if f.endswith(".html"):
                filename = os.path.join(root, f)
                file_was_changed = False
                with open(filename) as html_file:
                    try:
                        html_content = html_file.read()
                    except Exception as e:
                        print(f"Couldn't read HTML file {filename}")
                        raise e
                    # Rebuild coherent links from TOC to sub-pages
                    ids = find_dummy_h3_entries(html_content)
                    if ids:
                        html_content = remove_dummy_h3(html_content, ids)
                        file_was_changed = True
                    # Remove <h1>Index</h1> part of relevant pages
                    INDEX_H1_RE = re.compile(
                        r"<h1>Index</h1>\s*<h2(.*?)>(.*?)</h2>", re.M | re.S
                    )
                    match = INDEX_H1_RE.search(html_content)
                    if match:
                        before = html_content[:match.start()]
                        new_title = match.group(2)
                        if new_title.startswith("Package"):
                            USELESS_TITLE_RE = re.compile(r"(?<=<title>)Index(.*?)(?=</title>)", re.M | re.S)
                            t_match = USELESS_TITLE_RE.search(before)
                            if t_match:
                                new_title = re.sub(r"<a\s+.*?</a>", "", new_title)
                                new_title, n = re.subn(r"<code>(.*?)</code>", r"\g<1>", new_title)
                                new_title = "Taipy p" + new_title[1:]
                        before = before[:t_match.start()] + new_title + before[t_match.end():]
                        html_content = (before
                            + f"<h1{match.group(1)}>{match.group(2)}</h1>"
                            + html_content[match.end():])
                        file_was_changed = True
                    # Collapse doubled <h1>/<h2> page titles
                    REPEATED_H1_H2 = re.compile(
                        r"<h1>(.*?)</h1>\s*<h2\s+(id=\".*?\")>\1(<a\s+class=\"headerlink\".*?</a>)?</h2>", re.M | re.S
                    )
                    html_content, n_changes = REPEATED_H1_H2.subn('<h1 \\2>\\1\\3</h1>', html_content)
                    if n_changes != 0:
                        file_was_changed = True
                    # Specific processing for Getting Started documentation files
                    if "getting_started" in filename:
                        GS_H1_H2 = re.compile(r"<h1>(.*?)</h1>(.*?<h2.*?>\1)<", re.M | re.S)
                        html_content, n_changes = GS_H1_H2.subn('\\2<', html_content)
                        if n_changes != 0:
                            file_was_changed = True
                        gs_rel_path = os.path.relpath(site_dir, filename).replace("\\", "/").replace("../", "", 1)
                        GS_DOCLINK = re.compile(r"(href=\")https://docs\.taipy\.io/en/latest(.*?\")", re.M | re.S)
                        html_content, n_changes = GS_DOCLINK.subn(f"\\1{gs_rel_path}\\2", html_content)
                        if n_changes != 0:
                            file_was_changed = True
                    # Add external link icons (and open in new tab)
                    # Note we want this only for the simple [text](http*://ext_url) cases
                    EXTLINK = re.compile(
                        r"<a\s+(href=\"http[^\"]+\">.*?<\/a>)", re.M | re.S
                    )
                    html_content, n_changes = EXTLINK.subn('<a class="ext-link" target="_blank" \\1', html_content)
                    if n_changes != 0:
                        file_was_changed = True
                    # Find and resolve automatic cross-references to the Reference Manual
                    # The syntax in Markdown is `(class.)method()^` and similar.
                    rel_path = os.path.relpath(ref_files_path, filename).replace("\\", "/").replace("../", "", 1)
                    new_content = ""
                    last_location = 0
                    for xref in XREF_RE.finditer(html_content):
                        groups = xref.groups()
                        # function_name -> None, function_name, None, *
                        # class_name -> None, class_name, None, *
                        # package.class.function_name -> None, package.class., function_name, *
                        # (package.class.)function_name -> '(', package.class., function_name, *
                        # package.class_name -> None, package., class_name, *
                        # class_name.method_name -> None, class_name., method_name, *
                        # (class_name.)method_name -> '(', class_name., method_name, *
                        dest = None
                        package = None
                        entry = None
                        method = None
                        dest_package = None
                        if groups[1]:
                            # Class.Method?
                            entry = groups[1][:-1]
                            dest = xrefs.get(entry)
                            if dest:
                                package = dest[0]
                                method = groups[2]
                            else: # Package?
                                full_package = f"{groups[1]}{groups[2]}"
                                if full_package in x_packages:
                                    package = full_package
                                    entry = None
                                    dest = True
                                else: # Package.entry?
                                    package = entry
                                    dest = xrefs.get(groups[2])
                                    if dest:
                                        # Rename package if necessary
                                        if package != dest[0] and package in dest[2]:
                                            dest_package = dest[0]
                                        entry = groups[2]
                        else:
                            dest = xrefs.get(groups[2])
                            if dest:
                                package = dest[0]
                                entry = groups[2]
                            else: # Package?
                                if groups[2] in x_packages:
                                    package = groups[2]
                                    dest = True
                        if not dest:
                            (dir, file) = os.path.split(filename)
                            (dir, dir1) = os.path.split(dir)
                            (dir, dir2) = os.path.split(dir)
                            bad_xref = re.sub(r"</?code>", "`", xref.group(0))
                            message = f"Unresolve crossref '{bad_xref}' found in "
                            if file == "index.html":
                                (dir, dir3) = os.path.split(dir)
                                log.error(f"{message}{dir3}/{dir2}/{dir1}.md")
                            else:
                                log.error(f"{message}{dir2}/{dir1}/{file}")
                            continue
                        if dest_package is None:
                            dest_package = package
                        new_content += html_content[last_location:xref.start()]
                        new_content += f"<a href=\"{rel_path}/"
                        if entry:
                            new_content += f"{dest_package}.{entry}/"
                            if method:
                                new_content += f"index.html#{dest[1]}.{entry}.{method}\"><code>"
                                if not groups[0]:
                                    new_content += f"{entry}."
                                new_content += f"{method}"
                            else:
                                new_content += f"\"><code>"
                                # FIX:
                                # This block would add the destination package name
                                # before the entry name, in the link body.
                                # That's usualy what we do not want.
                                # It is kept until no bad impact is found.
                                #if not groups[0]:
                                #    new_content += f"{package}."
                                new_content += entry
                        else:
                            new_content += f"pkg_{dest_package}"
                            if method:
                                new_content += method
                            new_content += "/\"><code>"
                            if not groups[0]:
                                new_content += f"{package}"
                            if method:
                                new_content += f".{method}"
                        new_content += f"{groups[3] if groups[3] else ''}</code></a>"
                        last_location = xref.end()
                    if last_location:
                        file_was_changed = True
                        html_content = new_content + html_content[last_location:]
                    # Find 'free' crossrefs to the Reference Manual
                    # Syntax in Markdown is [free text]((class.)method()^) and similar
                    new_content = ""
                    last_location = 0
                    FREE_XREF_RE = re.compile(r"(<a\s+href=\")"
                                            + r"([^\d\W]\w*)(?:\.\))?"
                                            + r"((?:\.)?(?:[^\d\W]\w*))?(\(.*?\))?\^"
                                            + r"(\">.*?</a>)")
                    for xref in FREE_XREF_RE.finditer(html_content):
                        groups = xref.groups()
                        entry = groups[1]
                        method = groups[2]
                        # Function in package? Or method in class?
                        packages  = [entry, None] if entry in x_packages else xrefs.get(entry)
                        if packages is None:
                            (dir, file) = os.path.split(filename)
                            (dir, dir1) = os.path.split(dir)
                            (dir, dir2) = os.path.split(dir)
                            bad_xref = xref.group(0)
                            message = f"Unresolve crossref '{bad_xref}' found in "
                            if file == "index.html":
                                (dir, dir3) = os.path.split(dir)
                                log.error(f"{message}{dir3}/{dir2}/{dir1}.md")
                            else:
                                log.error(f"{message}{dir2}/{dir1}/{file}")
                            continue
                        else: # Free XRef was found: forget about the previous warning after all
                            md_file=filename[len(site_dir):]
                            sep=md_file[0]
                            (dir, file) = os.path.split(md_file[1:]) # Drop the separator
                            (dir, dir1) = os.path.split(dir)
                            if file == "index.html": # Other cases to be treated as they come
                                log.warning(f"FIXED error on link in '{dir}{sep}{dir1}.md' to '{dir}{sep}{entry}{method}{groups[3]}^'")
                        package = packages[0]
                        orig_package = packages[1]
                        new_content += html_content[last_location:xref.start()]
                        new_content += f"{groups[0]}{rel_path}/{package}."
                        if orig_package:
                            new_content += f"{entry}"
                            if method:
                                new_content += f"/index.html#{orig_package}.{entry}{method}\""
                        else:
                            new_content += f"{method}/"
                        new_content += f"\"{groups[4]}"
                        last_location = xref.end()
                    if last_location:
                        file_was_changed = True
                        html_content = new_content + html_content[last_location:]

                    # Finding xrefs in 'Parameters', 'Returns' and similar constructs.
                    # These would be <typeName>^ fragments located in potentially
                    # complex constructs such as "Optional[Union[str, <typeName>^]]"
                    #
                    # These fragments appear in single-line <td> blocks.
                    #
                    # At this point, this code is pretty sub-optimal and heavily
                    # depends on the MkDocs generation. Time will tell if we can
                    # keep it as is...
                    typing_code = re.compile(r"(<td>\s*<code>)(.*\^.*)(</code>\s*</td>)")
                    # This will match a single <typeName>^ fragment.
                    typing_type = re.compile(r"\w+\^")
                    for xref in typing_code.finditer(html_content):
                        groups = xref.groups()
                        table_line = groups[1]
                        table_line_to_replace = "".join(groups)
                        new_table_line = table_line_to_replace

                        for type_ in typing_type.finditer(table_line):
                            class_ = type_[0][:-1] # Remove ^
                            packages = xrefs.get(class_)
                            if packages:
                                new_content = f"<a href='{rel_path}/{packages[0]}.{class_}'>{class_}</a>"
                                new_table_line = new_table_line.replace(f"{class_}^", new_content)
                                file_was_changed = True
                        if file_was_changed:
                            html_content = html_content.replace(table_line_to_replace, new_table_line)

                    # Shorten Table of contents in REST API files
                    if "rest/apis_" in filename or "rest\\apis_" in filename:
                        REST_TOC_ENTRY_RE = re.compile(r"(<a\s+href=\"#apiv.*?>\s+)"
                                                     + r"/api/v\d+(.*?)(?=\s+</a>)")
                        new_content = ""
                        last_location = 0
                        for toc_entry in REST_TOC_ENTRY_RE.finditer(html_content):
                            new_content += html_content[last_location:toc_entry.start()]
                            new_content += f"{toc_entry.group(1)}{toc_entry.group(2)}"
                            last_location = toc_entry.end()
                        if last_location:
                            file_was_changed = True
                            html_content = new_content + html_content[last_location:]

                    # Rename Extension API type aliases
                    if "reference_guiext" in filename:
                        for in_out in [("TaipyAction", "Action", "../interfaces/Action"),
                                       ("TaipyContext", "Context", "#context")]:
                            LINK_RE = re.compile(f"<code>{in_out[0]}</code>")
                            new_content = ""
                            last_location = 0
                            for link in LINK_RE.finditer(html_content):
                                new_content += html_content[last_location:link.start()]
                                new_content += f"<a href=\"{in_out[2]}\"><code>{in_out[1]}</code></a>"
                                last_location = link.end()
                            if last_location:
                                file_was_changed = True
                                html_content = new_content + html_content[last_location:]

                if file_was_changed:
                    with open(filename, "w") as html_file:
                        html_file.write(html_content)
            # Remove '.md_template' files
            elif f.endswith(".md_template"):
                os.remove(os.path.join(root, f))
