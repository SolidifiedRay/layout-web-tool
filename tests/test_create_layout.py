import unittest
import create_layout
import in_toto.models.link

class Test_create_layout(unittest.TestCase):

  '''Check whether the output of before_after_filesystem_snapshot is as defined
    by each test case.'''

  before = {
    'one.tgz': '1234567890abcdef',
    'foo/two.tgz': '0000001111112222',
    'three.txt': '1111222233334444',
    'bar/bat/four.tgz': '6677889900112233'
  }

  first_step_link_str = {
    '_type': 'link', 
    'name': 'first_step', 
    'byproducts': {}, 
    'environment': {}, 
    'materials': {}, 
    'command': [], 
    'products': {
      'one.tgz': {'sha256': '1234567890abcdef'},
      'foo/two.tgz': {'sha256': '0000001111112222'},
      'three.txt': {'sha256': '1111222233334444'},
      'bar/bat/four.tgz': {'sha256': '6677889900112233'}
    }
  }

  second_step_link_str = {
    '_type': 'link', 
    'name': 'second_step', 
    'byproducts': {}, 
    'environment': {}, 
    'materials': {
      'one.tgz': {'sha256': '1234567890abcdef'},
      'foo/two.tgz': {'sha256': '0000001111112222'},
      'three.txt': {'sha256': '1111222233334444'},
      'bar/bat/four.tgz': {'sha256': '6677889900112233'}
    }, 
    'command': [], 
    'products': {
      'five.txt': {'sha256': '5555555555555555'},
      'one.tgz': {'sha256': '1234567890abcdef'},
      'foo/two.tgz': {'sha256': 'ffffffffffffffff'},
      'bar/bat/four.tgz': {'sha256': '6677889900112233'},
      'baz/six.tgz': {'sha256': '6666666666666666'}
    }
  }

  snapshot = [
    ['one.tgz', 'bar/bat/four.tgz'], # unchanged
    ['foo/two.tgz'], # modified
    ['five.txt', 'baz/six.tgz'], # added
    ['three.txt'] # removed
  ]

  def test_same_filesystem_snapshot(self):

    after = {
      'one.tgz': '1234567890abcdef',
      'foo/two.tgz': '0000001111112222',
      'three.txt': '1111222233334444',
      'bar/bat/four.tgz': '6677889900112233'
    }

    snapshot = create_layout.snapshot(self.before, after)
    self.assertEqual(snapshot, (['bar/bat/four.tgz', 'foo/two.tgz', 'one.tgz',
      'three.txt'], [], [], []))


  def test_removed_files_filesystem_snapshot(self):

    after = {}

    snapshot = create_layout.snapshot(self.before, after)
    self.assertEqual(snapshot, ([], [], [], ['bar/bat/four.tgz', 'foo/two.tgz',
      'one.tgz', 'three.txt']))


  def test_new_filesystem_snapshot(self):
    after = {
      'five.tgz': '1234567890defghi',
      'foo/bar/six.tgz': '0000001111112234',
      'foofoo/seven.txt': '1111222233334555'
    }

    snapshot = create_layout.snapshot(self.before, after)
    self.assertEqual(snapshot, ([], [], ['five.tgz', 'foo/bar/six.tgz',
      'foofoo/seven.txt'], ['bar/bat/four.tgz', 'foo/two.tgz', 'one.tgz',
      'three.txt']))


  def test_fully_modified_filesystem_snapshot(self):

    after = {
      'one.tgz': '1234567890aabbcc',
      'foo/two.tgz': '0000001111112233',
      'three.txt': '1111222233334455',
      'bar/bat/four.tgz': '6677889900123456'
    }

    snapshot = create_layout.snapshot(self.before, after)
    self.assertEqual(snapshot, ([], ['bar/bat/four.tgz', 'foo/two.tgz',
      'one.tgz', 'three.txt'], [], []))


  def test_partially_modified_filesystem_snapshot(self):

    after = {
      'five.txt': '5555555555555555',
      'one.tgz': '1234567890abcdef',
      'foo/two.tgz': 'ffffffffffffffff',
      'bar/bat/four.tgz': '6677889900123456',
      'baz/six.tgz': '6666666666666666'
    }

    snapshot = create_layout.snapshot(self.before, after)
    self.assertEqual(snapshot, (['one.tgz'], ['bar/bat/four.tgz',
      'foo/two.tgz'], ['baz/six.tgz', 'five.txt'], ['three.txt']))

  def test_create_material_rules_with_zero_index(self):
    first_link = in_toto.models.link.Link.read(self.first_step_link_str)
    links = [first_link]

    expected_materials = [
      ['ALLOW', 'one.tgz'],
      ['ALLOW', 'bar/bat/four.tgz'],
      ['ALLOW', 'foo/two.tgz'],
      ['DELETE', 'three.txt'],
      ['DISALLOW', '*']
    ]

    self.assertEqual(expected_materials,
        create_layout.create_material_rules(self.snapshot, links, 0))

  def test_create_material_rules_with_nonzero_index(self):
    first_link = in_toto.models.link.Link.read(self.first_step_link_str)
    second_link = in_toto.models.link.Link.read(self.second_step_link_str)
    links = [first_link, second_link]

    expected_materials = [
      ['MATCH', 'bar/bat/four.tgz', 'WITH', 'PRODUCTS', 'FROM', 'first_step'],
      ['MATCH', 'foo/two.tgz', 'WITH', 'PRODUCTS', 'FROM', 'first_step'],
      ['MATCH', 'one.tgz', 'WITH', 'PRODUCTS', 'FROM', 'first_step'],
      ['MATCH', 'three.txt', 'WITH', 'PRODUCTS', 'FROM', 'first_step'],
      ['DELETE', 'three.txt'],
      ['DISALLOW', '*']
    ]

    self.assertEqual(expected_materials,
        create_layout.create_material_rules(self.snapshot, links, 1))

  def test_create_product_rules(self):
    expected_products = [
      ['ALLOW', 'one.tgz'],
      ['ALLOW', 'bar/bat/four.tgz'],
      ['MODIFY', 'foo/two.tgz'],
      ['CREATE', 'five.txt'],
      ['CREATE', 'baz/six.tgz'],
      ['DISALLOW', '*']
    ]

    self.assertEqual(expected_products,
        create_layout.create_product_rules(self.snapshot))

  if __name__ == '__main__':
    unittest.main()
