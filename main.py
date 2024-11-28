from bs4 import BeautifulSoup, NavigableString
from bs4.element import Tag
import pml_lib.std

filename = 'test.pml'
do_debug = False

def DEBUG(title, *a):
	if do_debug: print(f'[ {title} ]', *a)

class PML:
	def __init__(self):
		self.session = {
			'memory': {},
			'temp': [],
		}

	def get_stack_name(self) -> str:
		if len(self.session['temp']) == 0: 
			return ''
		
		return self.session['temp'][-1]
	
	def get_stack_obj(self) -> str:
		name = self.get_stack_name()
		if name == '': return None
		return self.session['memory'][name]

	def get_all_text(self, ele: Tag) -> str:
		res = ''
		if len(ele.contents) > 1:
			for k in ele.find_all(string=True, recursive=False):
				if type(k) == NavigableString:
					#if k.parent == ele:
					res += k.strip()

		else:
			res = ele.text

		return res

	def validity(self, ele: Tag, key: str, 
	default=None, available: list=[]):
		res = ele.get(key)
		if res == None:
			if default == None: raise Exception('')
			res = default
	
		if (not res in available) and len(available) != 0: raise Exception('')
		return res

	def func_query(self, name: str):
		ls = name.split('.')
		obj = getattr(pml_lib, ls[0])
		ls.pop(0)
		for v in ls:
			obj = getattr(obj, v)

		return obj
	
	def func_parse(self, fn: Tag):
		res = [[], None]
		mark = 0
		for el in fn:
			if el.name == 'arg':
				if mark == 1: raise Exception('arg must be placed before body.')
				res[0].append(el['name'])
				DEBUG('func_parse', 'arg:', el['name'])
		
			elif el.name == 'body':
				if mark == 1: raise Exception('Duplicated body')
				mark = 1
				res[1] = el
				DEBUG('func_parse', 'Allocate body')

			else:
				if type(el) == NavigableString:
					DEBUG('func_parse', 'Trapped NavigableString:', el.strip())
					continue
				
				raise Exception('Function structure is not match.')

		return res

	def func_invoke(self, fn: Tag):
		fn_obj = self.validity(self.session['memory'], fn.name)
		argc = len(fn_obj['args'])
		args_arr = self.get_all_text(fn).split('||')
		i = 0

		if argc != len(args_arr): raise Exception('')
		for val in args_arr:
			DEBUG('func_invoke', 'arg:',  val)
			fn_obj['scope'][fn_obj['args'][i]] = val
			i += 1

		self.session['temp'].append(fn.name)
		status = self.execute(ctx=fn_obj['body'], is_sub=True)

		# delete
		fn_obj['scope'] = {}
		return status
	
	def argument_resolver(self, arg: Tag, obj: dict) -> str:
		res = ''
		for v in arg:
			if v.parent != arg: continue
			if type(v) == NavigableString:
				res += v.text

			else:
				if v.name in obj:
					res += obj[v.name]
				
				else: raise Exception('argument error')

		return res

	def executefile(self, filename: str):
		f = open(filename)
		res = self.execute(f.read())
		f.close()
		return res

	def execute(self, string: str=None, 
	ctx: BeautifulSoup=None,
	is_sub: bool=False):
		if ctx == None: ctx = BeautifulSoup(string, 'xml')

		if not is_sub: ctx_list = ctx.src.find_all(recursive=False)
		else: ctx_list = ctx.find_all(recursive=False)

		for v in ctx_list:
			match v.name:
				case 'import':
					DEBUG('execute', 'case: import')
					imports = v.text.strip().split('\n')
					for p in imports:
						self.session['memory'][p] = {
							'type': 5, # imported function
							'args': ['p'],
							'body': self.func_query(
								self.validity(v, 'from') + '.' + p),
							'return': 'false',
						}
						
				case 'func':
					DEBUG('execute', 'case: func')
					if self.session['memory'].get(v.get('name')) == None:
						tmp = self.func_parse(v)
						self.session['memory'][v.get('name')] = {
							'type': 1, # function
							'args': tmp[0],
							'body': tmp[1],
							'scope': {},
							'return': self.validity(v, 
								'return', 'false', ['true', 'false']),
						}
						DEBUG('execute', 'funcinfo: \n\t\t',
							f'name {v.get("name")}\n\t\t',
							f'args {tmp[0]}')

					else:
						raise Exception('Tried to reallocate.')

				case 'return': 
					DEBUG('execute', 'case: return')
					if not is_sub or not self.get_stack_obj():
						raise Exception('return keyword cannot be here.')
					
					return v.string

				case _:
					DEBUG('execute', 'case other: %s' % v.name)
					if is_sub:
						key = self.get_stack_obj()['scope'].get(v.name)
						if key != None: 
							# TODO
							pass

					if v.name in self.session['memory']:
						obj = self.session['memory'][v.name]
						obj_type = obj['type']
						if obj_type == 1:
							DEBUG('execute', 'function invocation: %s' % v.name)
							ret = self.func_invoke(v)


						elif obj_type == 5:
							DEBUG('execute', 'loading external code: %s' % v.name)
							txt = self.argument_resolver(v, 
									self.get_stack_obj()['scope'])
							obj['body']({
								k: txt for k in obj['args']
							})

						else:
							# ????
							DEBUG('execute', '9999')

					else: raise Exception('Not found: %s' % v.name)

		DEBUG('execute', 'function end')
		return 

pml = PML()
pml.executefile(filename)
