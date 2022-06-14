
import log
import config
import requests
import uuid
import datetime
import json

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'

class Server:
	def isUuidAllowed(self,uuid):
		try:
			url = config.data['Server']['AuthUrl']
			headers = {'Content-type': 'application/json', "accept": "application/json"}
			body = {'user': uuid, 'module': config.data['Server']['Module'] }
			resp = requests.post( url, json=body, headers=headers )
			log.debug( f"auth uuid={uuid} => http status={resp.status_code}" )
			return resp.status_code==200
		except Exception as e:
			log.debug( f"auth uuid={uuid} => error: {e}, going to allow" )
			return True

	def strToUuid(self,uid):
		return str(uuid.uuid3(uuid.NAMESPACE_X500, uid.upper()))

	def isUidAllowed(self,uid):
		return self.isUuidAllowed( self.strToUuid(uid) )

	def sendInventory(self,user,lodgments,tags):
		body = {
			"updated_at": datetime.datetime.now().strftime(TIMESTAMP_FORMAT),
			'module': config.data['Server']['Module'],
		}

		if user is None:
			body['user'] = None
		else:
			body['user'] = self.strToUuid(user)

		if lodgments is not None:
			body['lodgments'] = lodgments

		if tags is not None:
			uuids = []
			for tag in tags:
				uuids.append( self.strToUuid(tag) )
			body['items'] = uuids
			
		url = config.data['Server']['InventoryUrl']
		headers = {'Content-type': 'application/json', "accept": "application/json"}

		log.debug( f"Sending inventory update: {json.dumps(body)}" )
		resp = requests.post( url, json=body, headers=headers )
		if resp.status_code!=200:
			log.info( f"Failed to send inventory update, http status code is {resp.status_code}" )
			raise RuntimeError( f"failed to send inventory update" )

		log.info( f"Inventory update sent: {body}" )
