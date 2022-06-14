
import log
import sys
import time
import config
import gpio
import nfc
import server
import usb
import inputsmap
from enum import Enum
import threading
import datetime

class State(Enum):
    # Только запустились, еще ничего не сделали
	INIT = 1

	# Стоим закрытые ничего не делаем.
	IDLE = 2

	# Движемся на открытие. Ждем пока активируется датчик открытия, чтобы потом начать ждать пока он неактивируется.
	OPENING1 = 3

	# Движемся на открытие. Ждем пока деактивируется датчик открытия.
	OPENING2 = 4

	# Стоим в открытом положении. Ждем пока сработает таймер на начало закрытия.
	OPENED = 5
	
	# Движемся на закрытие. Ждем пока пройдет время, отведенное на закрытие.
	CLOSING = 6

	# Находимся в закрытом положении и собираем данные по активации входов и наличию в поле UHF меток.
    # Ждем пока пройдет установленное время на инвентаризацию.
	INVENTORY = 7

	# Датчик открытия неожиданно активировался без команды на открытие.
	# Ждем пока он деактивируется назад.
	OPENED_UNEXPECTED = 8

class StateMachine:
	def __init__(self):
		self.mutex = threading.Lock()

		self.state = State.INIT
		self.stateBeginTime = None
		self.stateEndTime = None

		self.cardUid = None
		self.inventoryPending = True

		self.closeTime = int(config.data['CloseMotor']['FirstCloseTime'])

		self.gpio = gpio.Gpio()
		self.gpio.onOpenSensorActivated = self.__onOpenSensorActivated

		if int(config.data['Nfc']['Active'])==1:
			self.nfc = nfc.Reader()
			self.nfc.onRead = self.__onNfcRead

		self.server = server.Server()
		
		self.usbPorts = usb.Usb()
		self.usbPorts.onCard = self.__onNfcRead
		self.usbPorts.start()

		if int(config.data['Inputs']['Remap'])==1:
			self.__inputsMap = inputsmap.InputsMap()
		else:
			self.__inputsMap = None

	def __onOpenSensorActivated(self):
		with self.mutex:
			if self.state == State.IDLE:
				self.__switchState( State.OPENED_UNEXPECTED, None )
			elif self.state == State.INVENTORY:
				self.usbPorts.stopUhf()
				self.inventoryPending = True
				self.__switchState( State.OPENED_UNEXPECTED, None )
			elif self.state == State.OPENING1:
				log.debug( f"switching state to {State.OPENING2}" )
				self.state = State.OPENING2

	def __onNfcRead(self,uid):
		isAllowed = self.server.isUidAllowed(uid)
		if not isAllowed:
			for i in range(3):
				self.gpio.redOff()
				time.sleep(0.2)
				self.gpio.redOn()
				time.sleep(0.2)
			return

		with self.mutex:
			if self.state == State.INVENTORY:
				self.__finishInventory()

			if self.state == State.INVENTORY or self.state == State.IDLE:
				self.cardUid = uid
				self.inventoryPending = True
				if self.gpio.motorPinsAvailable():
					self.gpio.redOff()
					self.gpio.open()
					self.__switchState( State.OPENING1, None )
				else:
					self.usbPorts.sendOpen()
					self.usbPorts.startUhf()
					self.__switchState( State.INVENTORY, int(config.data['Inventory']['Duration']) )

	def __onTick(self):
		with self.mutex:
			if self.state == State.INIT:
				self.gpio.greenOff()
				self.gpio.redOn()
				if self.gpio.isOpen():
					log.info("Starting with active open sensor. Closing.")
					self.gpio.close()
					self.__switchState( State.CLOSING, self.closeTime )
				else:
					log.info("Starting with inactive open sensor.")
					self.gpio.stop()
					self.__switchState( State.IDLE, None )

			elif self.state == State.IDLE:
				if self.gpio.isOpen():
					self.__switchState( State.OPENED_UNEXPECTED, None )
				elif self.inventoryPending:
					self.inventoryPending = False
					self.usbPorts.startUhf()
					self.__switchState( State.INVENTORY, int(config.data['Inventory']['Duration']) )
			
			elif self.state == State.OPENING2:
				if not self.gpio.isOpen():
					self.gpio.greenOn()
					self.gpio.stop()
					self.closeTime = (datetime.datetime.now()-self.stateBeginTime).total_seconds()*1.1
					self.__switchState( State.OPENED, int(config.data['CloseMotor']['DelayBeforeClose']) )

			elif self.state == State.OPENED:
				if datetime.datetime.now() >= self.stateEndTime:
					self.gpio.greenOff()
					self.gpio.close()
					self.__switchState( State.CLOSING, self.closeTime )

			elif self.state == State.CLOSING:
				if datetime.datetime.now() >= self.stateEndTime:
					self.gpio.redOn()
					self.gpio.stop()
					if self.gpio.isOpen():
						self.__switchState( State.OPENED_UNEXPECTED, None )
					else:
						self.__switchState( State.IDLE, None )

			elif self.state == State.INVENTORY:
				if datetime.datetime.now() >= self.stateEndTime:
					self.__finishInventory()
					self.__switchState( State.IDLE, None )

			elif self.state == State.OPENED_UNEXPECTED:
				if not self.gpio.isOpen():
					self.__switchState( State.IDLE, None )

	def __finishInventory(self):
		lodegments = self.usbPorts.getInputs()
		if lodegments is not None and self.__inputsMap is not None:
			lodegments = self.__inputsMap.apply(lodegments)

		tags = self.usbPorts.stopUhf()
		log.info( f"finishing inventory. card: {self.cardUid}, lodegments: {lodegments}, tags: {tags}" )
		try:
			self.server.sendInventory( self.cardUid, lodegments, tags )
		except Exception as e:
			log.error( f"finishing inventory. failed to send inventory update to the server: {e}" )

	def __switchState(self,state,duration):
		log.debug( f"switching state to {state}, duration limit: {duration}" )
		self.state = state
		self.stateBeginTime = datetime.datetime.now()
		if duration is None:
			self.stateEndTime = None
		else:
			self.stateEndTime = self.stateBeginTime + datetime.timedelta(seconds=duration)

	def run(self):
		while True:
			self.__onTick()
			time.sleep(0.2)

if __name__ == '__main__':
	log.info("Starting")
	sm = StateMachine()
	sm.run()
