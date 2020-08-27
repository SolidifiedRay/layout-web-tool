# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
<Program Name>
  create_layout.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  March 23, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Creates a basic in-toto layout by reading an ordered list of step link files.

  ** Infer layout fields: **
    expires:
            default value
    keys:
            FIXME: Keys are currently ignored in this module
    steps:
            add steps in the order of passed link files
            name:
                    link.name
            expected_command:
                    link.command
            threshold:
                    default value
            expected_materials/expected_products:
                    currently uses simple approach (see below)
                    FIXME: Should use more complex approach (see ideas below)
            inspections:
                    FIXME Inspections are currently ignored in this module
            signatures:
                    empty (use `in-toto-sign` command line utility)


  ** Infer step artifact rules (simple approach) **
    ** expected_materials **

      IF no materials were recorded
        expected_materials: [["DISALLOW", "*"]]

      ELSE IF materials were recorded and it is the first step
        expected_materials: [["ALLOW", "*"]]

      ELSE
        expected_materials: [["MATCH", "*", "WITH", "PRODUCTS", "FROM", <PREVIOUS STEP>]


    ** expected_products **

      IF no products were recorded
        expected_products: [["DISALLOW", "*"]]

      ELSE products were recorded:
        expected_products: [["ALLOW", "*"]]


  ** Ideas for more complexity: **
    - explicitly, ALLOW or MATCH files by name instead of "*", e.g.:
      expected_materials = \
          [["ALLOW", material] for material in links[index].materials.keys()]

    - for MATCH rules
      match only those that already were in the previous step
      allow the rest by name


  <Usage>

    ```
    # Create a layout given an ordered list of link file paths

    links = []
    for LINK_PATH in LINK_PATHS:
      link = in_toto.models.link.Link.read_from_file(LINK_PATH)
      links.append(link)

    layout = create_layout_from_ordered_links(links)
    layout.dump()

    ```

"""
import os
import in_toto.models.link
import in_toto.models.layout

def snapshot(before_dict, after_dict):
  '''A simple function that returns which files were
    unchanged, modified, added or removed from an input dictionary (before_dict)
    and an output dictionary (after_dict). Both these dictionaries have file
    names as the keys and their hashes as the values.'''

  unchanged_files = []
  modified_files = []
  added_files = []
  removed_files = []
  for key in before_dict:
    if key in after_dict:
      if before_dict[key] == after_dict[key]:
        # Matching the hashes to check if file was unchanged
        unchanged_files.append(key)
      else:
        modified_files.append(key)
    else:
      removed_files.append(key)
  for key in after_dict:
    if key not in before_dict:
      # Looking for new files
      added_files.append(key)

  # Returning the snapshot of the new file system
  return (sorted(unchanged_files), sorted(modified_files), sorted(added_files),
      sorted(removed_files))

def create_material_rules(current_snapshot, links, index):
  """Create generic material rules (3 variants)
  current_snapshot:  the file structure of the current in-toto link object
  links: an ordered list of in-toto link objects
  index: the index of the current in-toto link object

  * MATCH available materials with products from previous step (links must be an
  ordered list) and
  * ALLOW available materials
  * DELETE removed materials
  * DISALLOW everything else

  Returns a list of material rules
  NOTE: Read header docstring for ideas for more complexity.  
  """

  expected_materials = []

  if index != 0:
    pre_step_name = links[index-1].name
    pre_snapshot = snapshot(links[index-1].materials, links[index-1].products)

    for i in range(3):
      # previous_snapshot[3] are removed files, which will not be included
      # in previous step's products

      # Assume all products from the previous step are materials in
      # the current step
      for file in pre_snapshot[i]:
        expected_materials.append(
          ["MATCH", file, "WITH", "PRODUCTS", "FROM", pre_step_name])
  else:
    for file in current_snapshot[0]:
      # ALLOW unchanged files
      expected_materials.append(["ALLOW", file])
    for file in current_snapshot[1]:
      # ALLOW modified files
      expected_materials.append(["ALLOW", file])
  
  for file in current_snapshot[3]:
    # DELETE removed files
    expected_materials.append(["DELETE", file])
    
  expected_materials.append(["DISALLOW", "*"])

  return expected_materials


def create_product_rules(current_snapshot):
  """Create generic product rules (1 variant)
  links: an ordered list of in-toto link objects
  
  * ALLOW available products
  * MODIFY changed products
  * CREATE added products
  * DISALLOW everything else

  Returns a list of product rules
  NOTE: Read header docstring for ideas for more complexity.  """


  expected_products = []

  for file in current_snapshot[0]:
    # ALLOW unchanged files
    expected_products.append(["ALLOW", file])
  for file in current_snapshot[1]:
    # MODIFY modified files
    expected_products.append(["MODIFY", file])
  for file in current_snapshot[2]:
    # CREATE added files
    expected_products.append(["CREATE", file])
    
  expected_products.append(["DISALLOW", "*"])

  return expected_products


def create_layout_from_ordered_links(links):
  """Creates basic in-toto layout from an ordered list of in-toto link objects,
  inferring material and product rules from the materials and products of the
  passed links. """
  # Create an empty layout
  layout = in_toto.models.layout.Layout()
  layout.keys = {}

  for index, link in enumerate(links):
    step_name = link.name
    current_snapshot = snapshot(links[index].materials, links[index].products)
    step = in_toto.models.layout.Step(name=step_name,
      expected_materials=create_material_rules(current_snapshot, links, index),
      expected_products=create_product_rules(current_snapshot),
      expected_command=link.command)

    layout.steps.append(step)


  return layout
