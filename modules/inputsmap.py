
import sys
import log
import configparser

CONFIG_FN = "inputsmap.cfg"

class Entry:
	def __init__(self):
		self.fixed = None

		self.p = None
		self.k = None

class InputsMap:
	def __init__(self):
		data = configparser.ConfigParser()
		if len( data.read(CONFIG_FN,encoding='utf8') )!=1:
			print( f"Failed to read config file '{CONFIG_FN}'" )
			sys.exit(1)

		self.__map = dict()
		for tp in data.sections():
			for tk in data[tp]:
				try:
					tpInt = int(tp)
					pmap = self.__map.get(tpInt)
					if pmap is None:
						pmap = dict()
						self.__map[tpInt] = pmap

					tkInt = int(tk)

					s = data[tp][tk].strip().lower()
					if s=="off":
						e = Entry()
						e.fixed = False
						pmap[tkInt] = e
					else:
						sa = s.split(":")
						if len(sa)!=2:
							raise RuntimeError( f"incorrect mapping entry syntax: {s}" )
						e = Entry()
						e.p = int(sa[0])
						e.k = int(sa[1])
						pmap[tkInt] = e
					
				except Exception as e:
					log.error( f"Inputs map entry syntax error in {tp}/{tk}" )

	def apply(self,src):
		sDict = dict()
		for sPlacement in src:
			p = sPlacement["placement"]
			sDictEntry = sDict.get(p)
			if sDictEntry is None:
				sDictEntry = dict()
				sDict[p] = sDictEntry
			for sKey in sPlacement["data"]:
				sDictEntry[ sKey["key"] ] = sKey["status"]

		rDict = dict()
		for p, pMapping in self.__map.items():
			rDictEntry = rDict.get(p)
			if rDictEntry is None:
				rDictEntry = { "placement": p, "data": [] }
				rDict[p] = rDictEntry
			for k, kMapping in pMapping.items():
				kEntry = {"key": k, "status": False}
				if kMapping.fixed is not None:
					kEntry["status"] = kMapping.fixed
				else:
					sDictEntry = sDict.get(kMapping.p)
					if sDictEntry is not None:
						value = sDictEntry.get(kMapping.k)
						if value is not None:
							kEntry["status"] = value
				rDictEntry["data"].append(kEntry)

		rList = []
		for rDictEntry in rDict.values():
			rList.append(rDictEntry)

		return rList
