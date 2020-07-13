import unittest

def changes_of_two_snapshots(before, after):
	'''
	Given two 'snapshots' of a file structure -- 'before' and 'after' -- determine 
	which files have been added, which have been removed, which have been modified, 
	and which have remained unchanged.
	'''
	changes = {
		'unchanged': [],
		'modified': [],
		'added': [],
		'removed': []
	}

	# find unchanged, modified, removed files:
	for file_name in before:
		hash_value = before[file_name]
		if file_name not in after:
			changes['removed'].append(file_name)
		elif before[file_name] != after[file_name]:
			changes['modified'].append(file_name)
		else:
			changes['unchanged'].append(file_name)

	# find added files:
	for file_name in after:
		if file_name not in before:
			changes['added'].append(file_name)

	return(changes)


class Test(unittest.TestCase):
	before = {
	  'one.tgz': '1234567890abcdef',
	  'foo/two.tgz': '0000001111112222',
	  'three.txt': '1111222233334444',
	  'bar/bat/four.tgz': '6677889900112233'
	}

	after = {
	  'five.txt': '5555555555555555',
	  'one.tgz': '1234567890abcdef',
	  'foo/two.tgz': 'ffffffffffffffff',
	  'bar/bat/four.tgz': '6677889900112233',
	  'baz/six.tgz': '6666666666666666'
	}

	def test_changes_of_two_snapshots(self):
		changes = {
			'unchanged': ['one.tgz', 'bar/bat/four.tgz'],
			'modified': ['foo/two.tgz'],
			'added': ['five.txt', 'baz/six.tgz'],
			'removed': ['three.txt']
		}
		self.assertEqual(changes,
			  changes_of_two_snapshots(self.before, self.after))


if __name__ == "__main__":
    unittest.main()