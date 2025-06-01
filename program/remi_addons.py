import remi.gui as gui
from remi.gui import decorate_event, decorate_set_on_listener
import markdown
from textwrap import dedent
import pandas as pd

class EditableTable(gui.Table):
	"""
	Simplified version of the Remi table widget.
	"""
	
	def __init__(self, *args, **kwargs):
		"""
		Args:
			kwargs: See Container.__init__()
		"""
		self.__column_count = 0
		super(EditableTable, self).__init__(*args, **kwargs)
		self._editable = []
		self.css_display = 'table'
		self.row_count = 0
		self.column_count = 0
		
	def fill_from_list(self, content:list[list], editable: list[str]):
		"""
		Normal way to fill the table after the constructor.
		The table is build from a List of Lists.
		All rows MUST have equal length.
		The first row is always the header (title)

		Args:
			content: (list of lists(rows)), first row is header/title row, all rows must have equal length
			editable: A list with column names for enabling editable columns. An editable boolean value will be handled by a
		      CheckBox, all other types by a TextInput

		Examples:
			| test = EditableTable()
			| test.fill_from_list([['column1','column2','column3'],[True,'John','Doe'],[False,'Remi','GUI']], editable=[True,False,True])

		Raises:
		    ValueError : raised when the passed content list of lists contains rows of un-equal length

		"""
		max_columns = max(map(len, content))
		min_columns = min(map(len, content))
		if max_columns != min_columns: raise ValueError('Passed table rows must have identical column count...')
		n_columns = max_columns
		n_rows = len(content)
		self._editable = [content[0][x] in editable for x in range(n_columns)]
		# start with a clean empty table
		self.empty()
		self.row_count = 0
		self.column_count = 0
		
		for i in range(n_rows):
			tr = gui.TableRow()
			for c in range(n_columns):
				data = content[i][c]
				if i == 0:
					cl = gui.TableTitle(f'{data}')
				elif self._editable[c]:
					cl = TableCheckBox(data) if type(data) is bool else gui.TableEditableItem(f'{data}')
					cl.onchange.connect(self.on_item_changed, int(i), int(c))
				else:
					cl = gui.TableItem(f'{data}')
				cl.init_value = data
				tr.append(cl, str(c))
			self.append(tr, str(i))
		self.row_count = n_rows
		self.column_count = n_columns
		
	def fill_from_df(self, data_df: pd.DataFrame, editable: list[str]):
		"""
		Fill the table from a pandas dataframe (after the constructor).
		The DataFrame column names form the header row (title)

		Args:
			data_df (DataFrame): pandas dataframe with the data to be displayed in the table
			editable (list[of str]): A list with column names for enabling editable columns. An editable boolean value will be handled by a
		      CheckBox, all other types by a TextInput

		Raises:
		"""
		header = data_df.columns.tolist()
		data = data_df.values.tolist()
		self.fill_from_list([header] + data, editable)
	
	
	def reset(self):
		"""
		Resets all values in the table to their initial values
		"""
		for row_key in self.children.keys():
			for item_key in self.children[row_key].children.keys():
				item = self.item_at(row_key, item_key)
				item.set_text(str(item.init_value))

		
	def item_at(self, row, column):
		"""Returns the TableItem instance at row, column coordinates
	
		Args:
			row (int): zero based index
			column (int): zero based index
		"""
		return self.children[str(row)].children[str(column)]
	
	def item_coords(self, table_item):
		"""Returns table_item's (row, column) cordinates.
		Returns None in case of item not found.
	
		Args:
			table_item (TableItem): an item instance
		"""
		for row_key in self.children.keys():
			for item_key in self.children[row_key].children.keys():
				if self.children[row_key].children[item_key] == table_item:
					return (int(row_key), int(item_key))
		return None
		
	@decorate_set_on_listener("(self, emitter, item, new_value, row, column)")
	@decorate_event
	def on_item_changed(self, item, new_value, row, column):
		"""Event for the item change.
	
		Args:
			emitter (TableWidget): The emitter of the event.
			item (TableItem): The TableItem instance.
			new_value (str): New text content.
			row (int): row index.
			column (int): column index.
		"""
		return (item, new_value, row, column)


class TableCheckBox(gui.Container):
	"""item widget for the TableRow."""
	
	def __init__(self, checked:bool=False, *args, **kwargs):
		"""
		Args:
			checked (bool):
			kwargs: See Container.__init__()
		"""
		super(TableCheckBox, self).__init__(*args, **kwargs)
		self.type = 'td'
		self.checkbox = gui.CheckBox()
		self.append(self.checkbox)
		self.checkbox.set_value(checked)
		self.checkbox.onchange.connect(self.onchange)
		
	def get_text(self):
		return str(self.checkbox.get_value())
	
	def set_text(self, checked:str):
		self.checkbox.set_value(checked.lower() in ['true', 'waar', 'on', 'aan', 'yes'])
		
	def get_value(self):
		return self.checkbox.get_value()
		
	def set_value(self, checked:bool):
		self.checkbox.set_value(checked)
		
	@decorate_set_on_listener("(self, emitter, new_value)")
	@decorate_event
	def onchange(self, emitter, new_value):
		return (new_value,)


class MultilineLabel(gui.Widget):
	"""Multiple lines label with Markdown support

	"""
	
	def __init__(self, text:str='', *args, **kwargs):
		"""
		Multiple lines label with Markdown support

		Args:
			text (str): The Markdown text
		"""
		
		super().__init__(_type='div',  *args, **kwargs)
		self.text = text
		self.markdown_html = None
		if self.text: self.set_value(self.text, **kwargs)
	
	def set_value(self, text: str, **kwargs):
		self.empty()
		list_style = kwargs.pop('list_style', 'square')
		self.markdown_html = markdown.markdown(dedent(text), output_format='html')
		self.markdown_html = self.markdown_html.replace('<li>',
														f'<li style="display:list-item;list-style:{list_style}">')
		self.add_child(str(id(self.markdown_html)), self.markdown_html)



class Switch(gui.Widget):
	@property
	def locked(self):
		return self._locked
	@locked.setter
	def locked(self, value):
		self._locked = value
		if self._locked:
			self.style['opacity'] = '0.5'
		else:
			self.style['opacity'] = '1.0'
		
	
	def __init__(self, on_text='', off_text='', initial_state=False, initial_locked=False, *args, **kwargs):
		super().__init__(_type='div', _class='switch', *args, **kwargs)
		self._locked = False
		self.slider = gui.Widget(_class='thumb')
		
		self.light = gui.Widget(_class='light')
		
		self.on_text = gui.Widget(_class='onlabel')
		on_txt =f'<text>{on_text}</text>'
		self.on_text.add_child(str(id(on_txt)),on_txt)
		
		self.off_text = gui.Widget(_class='offlabel')
		off_txt =f'<text>{off_text}</text>'
		self.off_text.add_child(str(id(off_txt)),off_txt)

		self.lines = gui.Widget(_class='lines')
		no_of_lines = 3
		for x in range (no_of_lines):
			line = gui.Widget(_class='line')
			self.lines.add_child(str(id(line)), line)
			
		self.slider.add_child(str(id(self.light)), self.light)
		self.slider.add_child(str(id(self.on_text)), self.on_text)
		self.slider.add_child(str(id(self.off_text)), self.off_text)
		self.slider.add_child(str(id(self.lines)), self.lines)
		
		self.add_child(str(id(self.slider)), self.slider)
		self.onclick.connect(self.onswitched)
		
		self.__set_switch(initial_state)
		self.set_lock(initial_locked)

	def get_value(self):
		return self.attributes['switch'] == 'on'

	def set_value(self, nw_state:bool):
		if self.locked: return
		if nw_state:
			self.__set_switch(True)
		else:
			self.__set_switch(False)
		
	def set_lock(self, lock:bool=False):
		self.locked = lock
		
		
		
	@decorate_set_on_listener("(self, emitter)")
	@decorate_event
	def onswitched(self, emitter):
		if self._locked: return (self.get_value(),)
		if self.get_value():
			self.__set_switch(False)
			return(False,)
		else:
			self.__set_switch(True)
			return (True,)

	def __set_switch(self, state):
		if self.locked: return
		if state:
			self.attributes['switch'] = 'on'
			self.slider.style['transform'] = 'translateY(-99%)'
			self.light.style['background-color'] = 'red'
			self.on_text.style['visibility'] = 'visible'
			self.off_text.style['visibility'] = 'hidden'
		else:
			self.attributes['switch'] = 'off'
			self.slider.style['transform'] = 'translateY(0%)'
			self.light.style['background-color'] = 'black'
			self.on_text.style['visibility'] = 'hidden'
			self.off_text.style['visibility'] = 'visible'


class PushBtn(gui.Widget):
	
	@property
	def locked(self):
		return self._locked
	@locked.setter
	def locked(self, value):
		self._locked = value
		if self._locked:
			self.style['opacity'] = '0.5'
		else:
			self.style['opacity'] = '1.0'
			
	def __init__(self, text='', *args, **kwargs):
		super().__init__(_type='div', _class='pushbtn', *args, **kwargs)
		self._locked = False
		self.attributes['pushbtn'] = 'off'
		
		self.press = gui.Widget(_class='press')
		self.light = gui.Widget(_class='light')
		self.press.add_child(str(id(self.light)), self.light)
		
		self.text = gui.Widget(_class='label')
		txt = f'<text>{text}</text>'
		self.text.add_child(str(id(txt)), txt)
		self.press.add_child(str(id(self.text)), self.text)
		
		self.lines = gui.Widget(_class='lines')
		no_of_lines = 2
		for x in range(no_of_lines):
			line = gui.Widget(_class='line')
			self.lines.add_child(str(id(line)), line)
		self.press.add_child(str(id(self.lines)), self.lines)
		
		self.add_child(str(id(self.press)), self.press)
		self.onclick.connect(self.onpushed)
	
	def get_value(self):
		return self.attributes['pushbtn'] == 'on'
	
	def set_value(self, nw_state: bool):
		if self.locked: return
		if nw_state:
			self.__set_switch(True)
		else:
			self.__set_switch(False)
		
	def set_lock(self, lock: bool = False):
		self.locked = lock
	
	@decorate_set_on_listener("(self, emitter)")
	@decorate_event
	def onpushed(self, emitter):
		if self._locked: return (self.get_value(),)
		if self.get_value():
			self.__set_switch(False)
			return(False,)
		else:
			self.__set_switch(True)
			return (True,)

	def __set_switch(self, state):
		if self.locked: return
		if self.attributes['pushbtn'] == 'off':
			self.attributes['pushbtn'] = 'on'
			self.press.style['border-style'] = 'solid solid double solid'
			self.light.style['background'] = 'red'
			self.style['border-style'] = 'solid'
		else:
			self.attributes['pushbtn'] = 'off'
			self.press.style['border-style'] = 'hidden'
			self.light.style['background'] = 'black'
			self.style['border-style'] = 'double'


def waitkey(prompt='Press any key to continue: '):
	"""
	Prints a prompt and waits for a keypress
	:param prompt:
	"""
	wait = input(prompt)
