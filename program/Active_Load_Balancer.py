import logging
import sys
import threading
import time
from dataclasses import dataclass, field

from program.Common_Data import DATAPOINTS_ID as dp
from Datapoint_IDs import *

Logger = logging.getLogger()
Logger.setLevel(logging.DEBUG)
Logger.addHandler(logging.StreamHandler(sys.stdout))




class ALB_device:
	def __init__(self, name:str, priority:int=1, phase_loads:tuple[int]=None, mins:tuple[int]=None, is_tune_able:bool=False, startup_delay:int=1):
		"""
		:param name: 			Name of the device
		:param priority: 		Priority of the device for ALB purposes, higher means more important and less likely to be cut-off or tuned down
		:param phase_loads: 	tuple of typical load per phase when in full operational mode, default (9,9,9)
		:param mins: 			Only for tune_able devices: the minimal amps per phase while still maintaining some level of operation, default (0,0,0)
		:param is_tune_able: 	If True an alb threshold setpoint will be generated, if false an On/Off setpoint will be generated.
		:param startup_delay: 	The time (in seconds) it takes to start from shutoff to fully operational
		"""
		self.name = name
		self.priority = priority
		
		self.phase_loads = phase_loads
		if self.phase_loads is None: self.phase_loads=(9,9,9)
		
		self.mins = mins
		if self.mins is None: self.mins=(0,0,0)
		
		self.is_tune_able = is_tune_able
		self.startup_delay = startup_delay

	


class ALB():
	"""
		Active_Load_Balancer.py
		The ALB class has to be instantiated with a list of ALB devices and a loop time
	
		Every time it runs (also callable by calling the run method) it will:
			* 	Check the current load on the grid for all phases (L1_amps, L2_amps and L3_amps) against the current setpoints
				(L1_max_current, L2_max_current, L3_max_current)
			*	If the current load for at least 1 phase exceeds the setpoint for that phase:
			
				*	Analyze the ALB_device_list (which is filtered for that phase and sorted on ALB priority, lowest priority first) for entries that can
					be limited per phase **FOR THAT SPECIFIC PHASE** and see if that device can solve the problem by switching off or tuning down
				*	If that works, that device is shut off
				*	If that does not work, the ALB_device_list is revisited for all devices that use that phase and the first one that will solve
				 	the problem will be switched off or tuned down, thereby accepting that the phase not in overload will also be tuned down or switched off.
				*	Tuning down or switching off results in a ALB_setpoint which overrules all other setpoints for that device. This setpoints can either be a
					threshold value (tuning down) or a boolean (on/off).
				* 	The datapoint for each device in the ALB_device_list will via its calc rule implement a hard limit for the ALB setpoint.
				
			* If the current load for none of the phases exceeds the setpoint for that phase:
			
				* 	For on/off ALB devices the highest blocked priority will be deblocked if that fits in the available space for all phases
				*	For tune ALB devices the limiter  will be decreased by 1 amp untill it reaches 0
				* 	Only 1 of action per loop iteration will be performed
	"""
	
	def __init__(self, alb_list: list[ALB_device]=None, loop_time: float=2.0, auto_start: bool=True):
		"""
		
		:param alb_list:
		:param loop_time:
		:param auto_start:
		"""
		self.alb_list = alb_list
		if self.alb_list is None: self.alb_list=[]
		if not type(self.alb_list) is list: self.alb_list=[self.alb_list]
		
		self.loop_time = loop_time
		
		self.alb_thread = None
		if auto_start: self.run()
		
		
	def run(self):
		# get the current loads and setpoints on L1... L3
		Logger.info("Running ALB_device_list...")
		# act_amps = (dp[L1_amps].value, dp[L2_amps].value, dp[L3_amps].value)
		# act_setp = (dp[L1_max_current].value, dp[L2_max_current].value, dp[L3_max_current].value)
		if self.alb_thread is not None: self.alb_thread.cancel()
		self.alb_thread = threading.Timer(self.loop_time, self.run)
		self.alb_thread.daemon = True
		self.alb_thread.start()
		
if __name__ == '__main__':
	device1 = ALB_device('test1', 1, [1], 10.0, True, 1.0)
	device2 = ALB_device('test2', 2, [1,2,3], 10.0, True, 1.0)
	
	alb = ALB([device1, device2])
	
	print(alb.alb_list)
	
	time.sleep(20)
	
	
	

		