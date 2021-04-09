import csv

class Entry:

	def __init__(self, raw_entry):
		self.refid = raw_entry["refid"]
		self.raw_entries = [raw_entry]
		self.is_parsed = False

	def __str__(self):
		string = "%s\n" % self.refid

		if not self.is_parsed:
			for entry in self.raw_entries:
				string += "%s\n" % entry

		else:
			string += ("Type: {type}\n"
				"Time: {time}\n"
				"Asset: {asset}\n"
				"Amount: {amount}\n"
				"Fee: {fee}\n").format(**vars(self))

		return string

	def add_raw_entry(self, raw_entry):
		self.raw_entries.append(raw_entry)

	def parse_raw_entries(self):
		
		self.type = self.raw_entries[0]["type"]
		multi_entry = self.type in ["trade", "spend"]

		self.time = self.raw_entries[0]["time"]
		self.asset = [entry["asset"] for entry in self.raw_entries] if multi_entry else self.raw_entries[0]["asset"]
		self.amount = [float(entry["amount"]) for entry in self.raw_entries] if multi_entry else float(self.raw_entries[0]["amount"])
		self.fee = float(self.raw_entries[0]["fee"])

		self.is_parsed = True

def read_data(path):
	
	with open(path, newline='') as f:
	    reader = csv.reader(f)
	    data = list(reader)

	# Create dict for each event
	columns = data[0]
	data = [dict(zip(columns, row)) for row in data[1:]]

	# Group event with same refid
	entries = dict()
	for row in data:
		refid = row["refid"]
		if not refid in entries:
			entries[refid] = Entry(row)

		else:
			entries[refid].add_raw_entry(row)

	# Parse raw entries
	entries = list(entries.values())	
	for entry in entries:
		entry.parse_raw_entries()

	return entries


class Wallet:

	def __init__(self):

		self.assets = dict()

	def __str__(self):

		string = "=== Wallet Assets ===\n"

		for asset, amount in self.assets.items():
			string += "%s: %.8f\n" % (asset, amount)

		return string

	def update_asset(self, asset, amount):

		if asset in self.assets:
			self.assets[asset] += amount

			if self.assets[asset] < 1e-4:
				del self.assets[asset]

		else:
			self.assets[asset] = amount 

	def update(self, entry):

		if entry.type == "transfer":
			self.update_asset(entry.asset, -entry.amount)

		elif entry.type == "withdrawal":
			self.update_asset(entry.asset, entry.amount - entry.fee)

		elif entry.type == "spend":
			for i in range(2):
				self.update_asset(entry.asset[i], entry.amount[i])

		elif entry.type == "deposit":
			self.update_asset(entry.asset, entry.amount)

		elif entry.type == "trade":
			self.update_asset(entry.asset[0], entry.amount[0] - entry.fee)
			self.update_asset(entry.asset[1], entry.amount[1] - entry.fee)

		elif entry.type == "staking":
			pass 	# Updated both as staking and deposit (i.e. omit these in order to not double count staking) 
			#self.update_asset(entry.asset, entry.amount)

		else:
			raise Exception("Invalid type!")
			
def main():
	entries = read_data("data/ledgers.csv")
			
	wallet = Wallet()
	for entry in entries:
		wallet.update(entry)

		# TODO: Fix mismatch in balance between Wallet and ledgers.csv.
		# Probably due to some rounding in ledgers.csv

		print(entry)
		print([(entry["asset"], entry["balance"]) for entry in entry.raw_entries])
		print(wallet)

	print(wallet)

if __name__ == '__main__':
	main()