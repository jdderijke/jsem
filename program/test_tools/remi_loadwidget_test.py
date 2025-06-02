import time

import remi.gui as gui
from remi import start, App

class Load(gui.Widget):
	def __init__(self, min=0, max=100, value=0, load_color='red', main_app=None, *args, **kwargs):
		super(Load, self).__init__(*args, **kwargs)
		if min > max: raise ValueError
		self.min = min
		self.max = max
		self.value = None
		# self.main_app = main_app
		
		self.load_ind = gui.Widget(style=	f'position:absolute; bottom:0%; width:100%; '\
											f'height:0%; background-color:{load_color}')
		self.set_value(value)
		self.add_child(str(id(self.load_ind)), self.load_ind)
		
	def set_value(self, value):
		if value > self.max: self.value = self.max
		elif value < self.min: self.value = self.min
		else: self.value = value
		self.load_ind.css_height = f'{(self.value - self.min) * 100 / (self.max - self.min)}%'
		
class MyApp(App):
	def __init__(self, *args, **kwargs):
		super(MyApp, self).__init__(*args, **kwargs)
		
	def idle(self):
		pass
		
	def main(self):
		teststring="""
		Enter portfolio setup information.<br />
		- Using cached data significantly reduces the data traffic on the Morningstar endpoint.<br />
		- Cached data retention is the number of hours the cached data can be used after it has been downloaded from Morningstar
		"""
		self.container = gui.Container(style='width:500px, height:500px')
		self.load = Load(main_app=self, style='position:absolute; top:20%; left:45%; width:20px; height:150px; border-style:solid; rotate:45deg')
		self.btn = gui.Button('press', style='position:absolute; top:20%; left:20%; width:10%; height:10%')
		self.btn.onclick.connect(btn_clicked, self.load, self)
		self.container.append([self.btn, self.load])
		# returning the root widget
		return self.container

def btn_clicked(btn_widget, load_widget, main_app, **kwargs):
	load_widget.set_value(50)
	# nw_height = f'{(load_widget.value - load_widget.min) * 100 / (load_widget.max - load_widget.min)}%'
	# load_widget.load_ind.repr({load_widget.load_ind: f'style="height:{nw_height}"'})

	main_app.do_gui_update()
	
	time.sleep(1.0)
	
	for teller in range(load_widget.min, load_widget.max, 1):
		load_widget.set_value(teller)
		print(teller)
		main_app.do_gui_update()
		time.sleep(0.05)
	#
	# for teller in range(load_widget.max, load_widget.min, -1):
	# 	load_widget.set_value(teller)
	# 	time.sleep(0.1)


def waitkey(prompt='Press any key to continue: '):
	"""
	Prints a prompt and waits for a keypress
	:param prompt:
	"""
	wait = input(prompt)


# starts the web server
start(MyApp, port=8081)
