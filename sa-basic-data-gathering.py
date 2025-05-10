# Installing Required Dependencies
import sys
sys.version
import subprocess
subprocess.check_call([sys.executable, "-m", "pip", "install", "gitpython"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "pyvis"])

# helper function to get a file path w/o having to always provide the /content/zeeguu-api/ prefix
def file_path(file_name):
    return "./api/"+file_name

# extracting a module name from a file name
def module_name_from_file_path(full_path):

    # e.g. ../core/model/user.py -> zeeguu.core.model.user

    file_name = full_path[len("./api"):]
    file_name = file_name.replace("/__init__.py","")
    file_name = file_name.replace("/",".")
    file_name = file_name.replace(".py","")
    return file_name

assert '.zeeguu.core.model.user' == module_name_from_file_path(file_path('zeeguu/core/model/user.py'))

# naïve way of extracting imports using regular expressions
import re


# we assume that imports are always at the
# TODO for you: add full support for imports; this is not complete...
def import_from_line(line):

    # regex patterns used
    #   ^  - beginning of line
    #   \S - anything that is not space
    #   +  - at least one occurrence of previous
    #  ( ) - capture group (read more at: https://pynative.com/python-regex-capturing-groups/)
    try:
      y = re.search(r"^from (\S+)", line)
      if not y:
        y = re.search(r"^import (\S+)", line)
      return y.group(1)
    except:
      return None


# extracts all the imported modules from a file
# returns a module of the form zeeguu_core.model.bookmark, e.g.
def imports_from_file(file):

    all_imports = []

    lines = [line for line in open(file, encoding="utf-8")]

    for line in lines:
        imp = import_from_line(line)

        if imp:
            all_imports.append(imp)

    return all_imports

imports_from_file(file_path('zeeguu/core/model/user.py'))

# test
bookmark_imports = imports_from_file(file_path('zeeguu/core/model/bookmark.py'))
unique_code_imports =  imports_from_file(file_path('zeeguu/core/model/unique_code.py'))
print(bookmark_imports)
print(unique_code_imports)
assert(unique_code_imports != bookmark_imports)

# Now we extract the dependencies between all the files
# To do that we iterate over all the python files with the help of the Path.rglob function from pathlib
# And we create a network with the help of the networkx package

from pathlib import Path
import networkx as nx

def dependencies_graph(code_root_folder):
    files = Path(code_root_folder).rglob("*.py")

    G = nx.Graph()

    for file in files:
        file_path = str(file)

        module_name = module_name_from_file_path(file_path)

        if module_name not in G.nodes:
            G.add_node(module_name)

        print("Processing " + module_name)

        for each in imports_from_file(file_path):
            print(module_name + " imports " + each)
            G.add_edge(module_name, each)

    return G

# Mathplotlib also has support for drawing networks
# We do a simple drawing of all the files and their dependencies in our system

import matplotlib.pyplot as plt

# a function to draw a graph
def draw_graph(G, size, **args):
    plt.figure(figsize=size)
    nx.draw(G, **args)
    plt.show()

G = dependencies_graph("./api")
# draw_graph(G, (80,80), with_labels=False) # HERE

# However, if we think a bit more about it, we realize tat a dependency graph
# is a directed graph (e.g. module A depends on m)
# with any kinds of graph either directed (nx.DiGraph) or
# non-directed (nx.Graph)

def dependencies_digraph(code_root_folder):
    files = Path(code_root_folder).rglob("*.py")

    G = nx.DiGraph()

    for file in files:
        file_path = str(file)

        source_module = module_name_from_file_path(file_path)

        if source_module not in G.nodes:
            G.add_node(source_module)

        for target_module in imports_from_file(file_path):

            G.add_edge(source_module, target_module)
            # print(module_name + "=>" + each + ".")

    return G

# Looking at the directed graph
DG = dependencies_digraph("./api")
# draw_graph(DG, (40,40), with_labels=True)

# # Copilot suggested the following code to draw the graph
# # We can also use pyvis to draw the graph in a more interactive way
# from pyvis.network import Network   

# def draw_graph_pyvis(G, size, **args):
#     nt = Network(notebook=True, height=size[0], width=size[1], directed=True)
#     nt.from_nx(G)
#     nt.show("graph.html")

# draw_graph_pyvis(DG, (400,400), with_labels=True)


# =============================================
# The next week
# =============================================

# Abstraction
# Let's define some relevant modules
def relevant_module(module_name):

  if "test" in module_name:
    return False


  if module_name.startswith("zeeguu"):
    return True


  return False

# However, if we think a bit more about it, we realize that a dependency graph
# is a directed graph (e.g. module A depends on m)
# with any kinds of graph either directed (nx.DiGraph) or
# non-directed (nx.Graph)

def dependencies_digraph_new(code_root_folder):
    files = Path(code_root_folder).rglob("*.py")

    G = nx.DiGraph()

    for file in files:
        file_path = str(file)

        source_module = module_name_from_file_path(file_path)
        if not relevant_module(source_module):
          continue

        if source_module not in G.nodes:
            G.add_node(source_module)

        for target_module in imports_from_file(file_path):

            if relevant_module(target_module):
              G.add_edge(source_module, target_module)


    return G


# Looking at the directed graph
DG = dependencies_digraph_new("./api")
# draw_graph(DG, (40,40), with_labels=True) # HERE


# extracts the parent of depth X
def top_level_package(module_name, depth=1):
    components = module_name.split(".")
    return ".".join(components[:depth])

assert (top_level_package("zeeguu.core.model.util") == "zeeguu")
assert (top_level_package("zeeguu.core.model.util", 2) == "zeeguu.core")


def abstracted_to_top_level(G, depth=1):
    aG = nx.DiGraph()
    for each in G.edges():
        src = top_level_package(each[0], depth)
        dst = top_level_package(each[1], depth)

        if src != dst:
          aG.add_edge(src, dst)

    return aG


ADG = abstracted_to_top_level(DG, 2)


plt.figure(figsize=(10,10))
nx.draw(ADG, with_labels=True)
plt.show()

# Evolution Analysis
subprocess.check_call([sys.executable, "-m", "pip", "install", "pydriller==2.6"])
from pydriller import Repository
REPO_DIR = 'https://github.com/zeeguu/api'

all_commits = list(Repository(REPO_DIR).traverse_commits())

def print_out_commit_details(commits):
  for commit in commits:
      print(commit)
      for each in commit.modified_files:
          print(f"{commit.author.name} {each.change_type} {each.filename}\n -{each.old_path}\n -{each.new_path}")

print_out_commit_details(all_commits[0:1])


from collections import defaultdict

commit_counts = defaultdict(int)

for commit in all_commits:
    for each in commit.modified_files:
        try:
            commit_counts [each.new_path] += 1
        except:
            pass

# sort by number of commits in decreasing order
sorted(commit_counts.items(), key=lambda x: x[1], reverse=True)[:42]

# discussion: What is ("None", 103) ?


from pydriller import ModificationType

commit_counts = {}

for commit in all_commits:
    for modification in commit.modified_files:

        new_path = modification.new_path
        old_path = modification.old_path

        try:

            if modification.change_type == ModificationType.RENAME:
                commit_counts[new_path]=commit_counts.get(old_path,0)+1
                commit_counts.pop(old_path)

            elif modification.change_type == ModificationType.DELETE:
                commit_counts.pop(old_path, '')

            elif modification.change_type == ModificationType.ADD:
                commit_counts[new_path] = 1

            else: # modification to existing file
                    commit_counts [old_path] += 1
        except Exception as e:
            print("something went wrong with: " + str(modification))
            pass

sorted(commit_counts.items(), key=lambda x:x[1], reverse=True)


def module_name_from_rel_path(full_path):

    # e.g. ../core/model/user.py -> zeeguu.core.model.user

    file_name = full_path.replace("/__init__.py","")
    file_name = file_name.replace("/",".")
    file_name = file_name.replace(".py","")
    return file_name


assert ("tools.migrations.teacher_dashboard_migration_1.upgrade" == module_name_from_rel_path("tools/migrations/teacher_dashboard_migration_1/upgrade.py"))

assert ("zeeguu.api") == module_name_from_rel_path("zeeguu/api/__init__.py")


def module_name_from_rel_path(full_path):

    # e.g. ../core/model/user.py -> zeeguu.core.model.user

    file_name = full_path.replace("/__init__.py","")
    file_name = file_name.replace("/",".")
    file_name = file_name.replace(".py","")
    return file_name


assert ("tools.migrations.teacher_dashboard_migration_1.upgrade" == module_name_from_rel_path("tools/migrations/teacher_dashboard_migration_1/upgrade.py"))

assert ("zeeguu.api") == module_name_from_rel_path("zeeguu/api/__init__.py")




sizes = []

for n in ADG.nodes():
  sizes.append(package_activity[n])

print(sizes)



plt.figure(figsize=(20,20))
nx.draw_networkx(ADG, with_labels=True, node_size = sizes, node_color='r')
plt.show()


# For Home: Extract Multiple Evolution Hotspots from Zeeguu

#     Extract multiple complementary module views from your case study system
#     Ensure that your layouts are readable - limit the number of nodes in a view, use a different layout in networkx, or use a different library than networkx
#     Augment each of the previously obtained module views by mapping the above-computed churn metric on the color of a given node
