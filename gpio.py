
import config
import log

if config.data['Board']['Type']=='Orange':
	import OPi.GPIO as GPIO
else:
	import RPi.GPIO as GPIO

class Gpio:
	def __init__(self):
		self.onOpenSensorActivated = None

		GPIO.setwarnings(False)
		GPIO.setmode(GPIO.BOARD)

		self.openSensorPin = int(config.data['OpenSensor']['Pin'])
		if self.openSensorPin!=0:
			self.openSensorActive = int(config.data['OpenSensor']['ActiveLevel'])
			if int(config.data['OpenSensor']['PullUp'])==1:
				GPIO.setup(self.openSensorPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			else:
				GPIO.setup(self.openSensorPin, GPIO.IN)
			if self.openSensorActive==1:
				GPIO.add_event_detect(self.openSensorPin, GPIO.RISING)
			else:
				GPIO.add_event_detect(self.openSensorPin, GPIO.FALLING)
			GPIO.add_event_callback(self.openSensorPin, self.__onOpenSensorActivation)

		self.openMotorPin = int(config.data['OpenMotor']['Pin'])
		if self.openMotorPin!=0:
			self.openMotorActive = int(config.data['OpenMotor']['ActiveLevel'])
			self.openMotorInactive = 0 if self.openMotorActive==1 else 1
			GPIO.setup(self.openMotorPin, GPIO.OUT)
			GPIO.output(self.openMotorPin, self.openMotorInactive )

		self.closeMotorPin = int(config.data['CloseMotor']['Pin'])
		if self.closeMotorPin!=0:
			self.closeMotorActive = int(config.data['CloseMotor']['ActiveLevel'])
			self.closeMotorInactive = 0 if self.closeMotorActive==1 else 1
			GPIO.setup(self.closeMotorPin, GPIO.OUT)
			GPIO.output(self.closeMotorPin, self.closeMotorInactive )

		self.redPin = int(config.data['RedLed']['Pin'])
		if self.redPin!=0:
			self.redActive = int(config.data['RedLed']['ActiveLevel'])
			self.redInactive = 0 if self.redActive==1 else 1
			GPIO.setup(self.redPin, GPIO.OUT)
			GPIO.output(self.redPin, self.redInactive )

		self.greenPin = int(config.data['GreenLed']['Pin'])
		if self.greenPin!=0:
			self.greenActive = int(config.data['GreenLed']['ActiveLevel'])
			self.greenInactive = 0 if self.greenActive==1 else 1
			GPIO.setup(self.greenPin, GPIO.OUT)
			GPIO.output(self.greenPin, self.greenInactive )

	def __onOpenSensorActivation(self,pin):
		if self.onOpenSensorActivated!=None:
			self.onOpenSensorActivated()
	
	def isOpen(self):
		if self.openSensorPin!=0:
			return GPIO.input(self.openSensorPin) == self.openSensorActive
		else:
			return False

	def open(self):
		if self.closeMotorPin!=0 and self.openMotorPin!=0:
			log.debug( "open cmd" )
			GPIO.output(self.closeMotorPin, self.closeMotorInactive )
			GPIO.output(self.openMotorPin, self.openMotorActive )

	def close(self):
		if self.closeMotorPin!=0 and self.openMotorPin!=0:
			log.debug( "close cmd" )
			GPIO.output(self.openMotorPin, self.openMotorInactive )
			GPIO.output(self.closeMotorPin, self.closeMotorActive )

	def stop(self):
		if self.closeMotorPin!=0 and self.openMotorPin!=0:
			log.debug( "stop cmd" )
			GPIO.output(self.closeMotorPin, self.closeMotorInactive )
			GPIO.output(self.openMotorPin, self.openMotorInactive )

	def redOn(self):
		if self.redPin!=0:
			log.debug( "red led on" )
			GPIO.output(self.redPin, self.redActive )

	def redOff(self):
		if self.redPin!=0:
			log.debug( "red led off" )
			GPIO.output(self.redPin, self.redInactive )

	def greenOn(self):
		if self.greenPin!=0:
			log.debug( "green led on" )
			GPIO.output(self.greenPin, self.greenActive )

	def greenOff(self):
		if self.greenPin!=0:
			log.debug( "green led off" )
			GPIO.output(self.greenPin, self.greenInactive )

	def motorPinsAvailable(self):
		return self.openSensorPin!=0 and self.closeMotorPin!=0 and self.openMotorPin!=0
