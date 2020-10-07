#!usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import json

def read_and_extract_Json(jsonFileName):

	try:
		with open(jsonFileName) as f:
		  data = json.load(f)
	except:
		raise Exception("ERROR ! When reading the following Json file: {}".format(jsonFileName))

	if "img_extract" or "expected_status" in jsonFileName:
	 	return data
	else:																# Have to adapt data
		output_data = []
		for element in data:
			output_data.append((element[0], element[1]))

		return output_data

class Database(object):

	def __init__(self, core):											

		self.graph = dict()
		self.extractedInfromation = dict()								# Store informations
		self.image_status = dict()										# Store status to return
		self.first_add = True											# To know if we build or edit 
		self.build_graph = dict()										# Store the first build graph
		self.graph[core] = 'None'										# Set the root node and create the graph
		self.root = core												# Store the root node

	def display_one(self):

		print("Actual graph is:\n")
		for key, value in self.graph.items():
			print("\t{0:10} {1:20} ->\t{2:11} {3:20}".format("Child:", key, "Parent:", value))  
		print("")

		print("Build graph is:\n")
		for key, value in self.build_graph.items():
			print("\t{0:10} {1:20} ->\t{2:11} {3:20}".format("Child:", key, "Parent:", value))  
		print("")

	def add_nodes(self, nodesToAdd):

		update = False
		
		if nodesToAdd[0][1] !=  None:									# We don't want to change the graph (root node)

			if len(self.graph) > 0:										# The graph is already created (it has a root)
				
				for childNode, parentNode in nodesToAdd:				

					if parentNode in self.graph:						# Parent node already exists in the created graph
						
						if update == False and not self.first_add:
							self.build_graph = self.graph.copy()		# Update before a new edits 	
							update = True

						self.graph[childNode] = parentNode			
					
					else:												# Parent node doesn't appear in the created graph
						raise Exception("ERROR ! Trying to add a child to an inexistant parent.")
			
			else: 														# Graph is not created yet
				raise Exception("ERROR ! A graph must have a root.")
		
		else:															# We want to change the graph
			if nodesToAdd[0][0] != self.root:							# We want to change the root node 
				self.__init__(nodesToAdd[0][0])							# Generate a new graph
							
			for childNode, parentNode in nodesToAdd[1:]:				# Adding new nodes
								
				if parentNode in self.graph:							# Parent node already exists in the created graph
					
					if update == False and not self.first_add:			# Update only once
						self.build_graph = self.graph.copy()			# Update before a new edits 	
						update = True					
					
					self.graph[childNode] = parentNode
				
				else:													# Parent node doesn't appear in the created graph
					raise Exception("ERROR ! Trying to add a child to an inexistant parent.")

		if self.first_add:
			self.build_graph = self.graph.copy()
			self.first_add = False
			
	def add_extract(self, informations):

		for key, value in informations.items():	

			if key not in self.extractedInfromation:					# Add a new labeled image
				self.extractedInfromation[key] = value					
			else:														# Replace the image label
				del self.extractedInfromation[key]						# Delete the current image label
				self.extractedInfromation[key] = value					# Replace it


	def get_extract_status(self):
		

		for image, labels in self.extractedInfromation.items():

			status = ""													# Temporary status for each image/label

			for cpt, label in enumerate(labels):

				if label in self.graph:									# Present in the actual graph

					if not label in self.build_graph:					# Not present in the precedent graph

						parentLabel = self.graph[label]					# Get the parent label
						listOfChilds = [key  for (key, value) in self.build_graph.items() if value == parentLabel]	# Childs of parentLabel in the precedent graph

						if len(listOfChilds) == 0:						
							if cpt == 0:
								status += "granularity_staged"
							else:
								status += ",granularity_staged"

						else:
							if cpt == 0:
								status += "coverage_staged"
							else:
								status += ",coverage_staged"							

					else:												# Label exists in both of actual and precedent graph
						parentLabel = self.graph[label]					# Get the parent label

						listOfChildsActual 		= [key  for (key, value) in self.graph.items() if value == parentLabel]					# List of parentLabel's childs in the actual graph
						listOfChildsPrecedent 	= [key  for (key, value) in self.build_graph.items() if value == parentLabel]			# List of parentLabel's childs in the precedent graph
						listOfChilds = [key  for (key, value) in self.graph.items() if value == label]									# List of label's childs in the actual graph

						if len(listOfChildsActual) == len(listOfChildsPrecedent):		

							if len(listOfChilds) > 0:

								if cpt == 0:
									status += "granularity_staged"
								else:
									status += ",granularity_staged"	

							else:										# 0 changes are made

								if cpt == 0:
									status += "valid"
								else:
									status += ",valid"

						else:
							if cpt == 0:
								status += "coverage_staged"
							else:
								status += ",coverage_staged"									
				else:													# Label inexistant in the actual graph
					if cpt == 0:
						status += "invalid"
					else:
						status += ",invalid"						

			################ Output preparation in fuction of priority
			if "invalid" in status.split(","):
				self.image_status[image] = "invalid"

			elif "coverage_staged" in status.split(","):
				self.image_status[image] = "coverage_staged"

			elif "granularity_staged" in status.split(","):
				self.image_status[image] = "granularity_staged"

			else: 
				self.image_status[image] = "valid" 

		return self.image_status


def main():
	
	parser = argparse.ArgumentParser()
	parser.add_argument('--buildFile', type = str, default = "data/graph_build.json", help = "Build graph Json File name")
	parser.add_argument('--editsFile', type = str, default = "data/graph_edits.json", help = "Edits graph Json File name")
	parser.add_argument('--extractFile', type = str, default = "data/img_extract.json", help = "Image extract Json File name")
	parser.add_argument('--expectedStatus', type = str, default = "data/expected_status.json", help = "Expected status Json File name")
	args = parser.parse_args()

	print("\n\n********************************* First Evaluation *********************************\n\n")

	# Initial graph
	build = [("core", None), ("A", "core"), ("B", "core"), ("C", "core"), ("C1", "C")]
	# Extract
	extract = {"img001": ["A"], "img002": ["C1"]}
	# Graph edits
	edits = [("A1", "A"), ("A2", "A")]

	# Get status (this is only an example, test your code as you please as long as it works)
	status = {}
	if len(build) > 0:
	    # Build graph
	    db = Database(build[0][0])
	    if len(build) > 1:
	    	db.add_nodes(build[1:])
	    # Add extract
	    db.add_extract(extract)
	    # Graph edits
	    db.add_nodes(edits)
	    # Update status
	    status = db.get_extract_status()
	print(status)

	
	print("\n\n********************************* Second Evaluation *********************************\n\n")

	# Initial graph
	build = [("core", None), ("A", "core"), ("B", "core"), ("C", "core"), ("C1", "C")]
	# Extract
	extract = {"img001": ["A", "B"], "img002": ["A", "C1"], "img003": ["B", "E"]}
	# Graph edits
	edits = [("A1", "A"), ("A2", "A"), ("C2", "C")]

	# Get status (this is only an example, test your code as you please as long as it works)
	status = {}
	if len(build) > 0:
	    # Build graph
	    db = Database(build[0][0])
	    if len(build) > 1:
	    	db.add_nodes(build[1:])
	    # Add extract
	    db.add_extract(extract)
	    # Graph edits
	    db.add_nodes(edits)
	    # Update status
	    status = db.get_extract_status()
	print(status)


	print("\n\n********************************* Self Evaluation *********************************\n\n")


	# Initial graph
	build = [("core", None), ("A", "core"), ("B", "core"), ("C", "core"), ("C1", "C"), ("B2", "C"),("B1", "B"),("A1", "A")]
	# Extract
	extract = {"img001": ["A1", "B4"], "img002": ["C1"],"img003": ["D"],"img004": ["B3"]}
	# Graph edits
	edits = [("B3", "B"), ("B4", "B1"), ("D", "core")]

	# Get status (this is only an example, test your code as you please as long as it works)
	status = {}
	if len(build) > 0:
	    # Build graph
	    db = Database(build[0][0])
	    if len(build) > 1:
	    	db.add_nodes(build[1:])
	    # Add extract
	    db.add_extract(extract)
	    # Graph edits
	    db.add_nodes(edits)
	    # Update status
	    status = db.get_extract_status()
	print(status)


	print("\n\n********************************* Evaluation on test data *********************************\n\n")

	############# Extract informations from json files 
	build = read_and_extract_Json(args.buildFile)

	edits = read_and_extract_Json(args.editsFile)

	extract = read_and_extract_Json(args.extractFile)

	status_expected = read_and_extract_Json(args.expectedStatus)

	# Get status (this is only an example, test your code as you please as long as it works)
	status = {}
	if len(build) > 0:
	    # Build graph
	    db = Database(build[0][0])
	    if len(build) > 1:
	    	db.add_nodes(build[1:])
	    # Add extract
	    db.add_extract(extract)
	    # Graph edits
	    db.add_nodes(edits)
	    # Update status
	    status = db.get_extract_status()
	print(status)

	print("\n\n********************************* Output of comparaison between my program's status and the expected status *********************************\n")

	is_equal = status == status_expected
	print(is_equal) 

if __name__ == '__main__':
	main()
