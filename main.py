import bs4
from bs4 import BeautifulSoup
import pml_lib.std

filename = 'test.pml'
f = open(filename)
s_ctx = f.read()
f.close()

soup = BeautifulSoup(s_ctx, 'xml')
session = {
	'start': False,
	'import': [],
	'func': [],
	'var': [],
}
def func_query(name: str):
	ls = name.split('.')
	obj = getattr(pml_lib, ls[0])
	ls.pop(0)
	for v in ls:
		obj = getattr(obj, v)

	return obj

def runtime(cursor: BeautifulSoup, depth: int = 0):
	if cursor == None:
		for func in session['func']:
			if func['name'] == 'main':
				print(func.body)
				return func.body

		return
	
	if depth == 0:
		session['start'] = True
		return runtime(getattr(cursor, filename).next, 1)

	else:
		if cursor.name == 'import':
			context = cursor.text.strip().strip('\n').split('\n')
			for v in context:
				session['import'].append({
					'name': v,
					'body': func_query(
						cursor['from'] + '.' + v),
				})

			return runtime(cursor.next, depth)

		elif cursor.name == 'func':
			arg = cursor.find_all('arg', {}, False)
			session['func'].append({
				'name': cursor['name'],
				'args': [],
			})
			for argn in arg:
				session['func'][-1]['args'].append(argn['name'])

			session['func'][-1]['body'] = cursor.body
			cursor = cursor.body

		elif cursor.name != None:
			mark = 0
			count = 0
			for fn in session['import']:
				if fn['name'] == cursor.name:
					mark = 1
					break

				count += 1

			if mark == 1:
				session['import'][count]['body'](cursor.text)
			
			else:
				count = 0
				for fn in session['func']:
					if fn['name'] == cursor.name:
						mark = 1
						break

					count += 1
			
				if mark == 0: return

				session['func'][count]
			
	#print(cursor.name, cursor, end='\n\n\n\n\n\n')
	return runtime(cursor.next, depth)

runtime(soup, 0)
