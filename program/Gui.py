#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Gui.py
#  
#  Copyright 2022  <pi@raspberrypi>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
def create_mainmenu(app, device_width=Device_Width, device_height=Device_Height):
	global Main_menu, Main_app, Main_menu_created
	# print ("create_mainmenu is called by: {}".format(stack()[1].function))
	# print ("CALLER FUNCTION: {}".format(stack()[1].function))
	
	# om de een of andere vage reden roept Remi deze routine meerdere keren aan tijdens opstarten.
	# We controleren dus of Main_menu al bestaat,...zo ja dan geven we die retour, zo nee dan
	# maken we een nieuw Main_menu
	# if Main_menu_created: return Main_menu
	# Main_menu = None
	Main_app = app
	init_gui()
	# print ("Lengte van Main Menu Items:", str(len(main_menu_items)))
	Main_menu=Container()
	Main_menu.css_left = "2%"
	Main_menu.css_top = "2%"
	Main_menu.set_size("96%","96%")
	Main_menu.css_font_size = "30px"
	Main_menu.css_position = "absolute"
	
	vbox0 = VBox()
	vbox0.css_align_items = "center"
	vbox0.set_size("100%","100%")
	
	vbox0.css_align_items = "center"
	vbox0.css_display = "flex"
	vbox0.css_flex_direction = "row"
	vbox0.css_flex_wrap = "wrap"
	vbox0.css_justify_content = "space-around"
	vbox0.css_position = "static"
	
	for menu_item in main_menu_items:
		# make button tekst from lists !!!
		nw_btn = Button(menu_item.text)
		nw_btn.css_font_size = "70%"
		nw_btn.css_left = "5%"
		# nw_btn.set_size("90%", str(int(100/(len(main_menu_items)+1)))+"%")
		nw_btn.set_size("45%", "12%")
		
		nw_btn.attributes.update({"menu_definition":menu_item})
		nw_btn.ontouchstart.connect(on_mainmenu_buttonpressed, menu_item=menu_item)
		nw_btn.onclick.connect(on_mainmenu_buttonpressed, menu_item=menu_item)
		# nw_btn.onclick.do(on_mainmenu_buttonpressed)
		vbox0.append(nw_btn)
	Main_menu.append(vbox0)
	return Main_menu

def main(args):
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
