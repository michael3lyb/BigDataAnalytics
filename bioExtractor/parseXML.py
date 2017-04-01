import xml.etree.ElementTree as ET
import glob

pathlist = glob.glob(r'./*.xml')
for path in pathlist:
	output = open(path.split('\\')[1].split('.')[0], 'w')
	tree = ET.parse(path).getroot()
	# output = open("small", 'w')
	# tree = ET.parse("other/small.xml").getroot()
	for MedlineCitation in tree.findall("MedlineCitation"):
		output.write("<doc>" + '\n')
		for Article in MedlineCitation.findall("Article"):
			title = Article.find("ArticleTitle").text
			output.write(title.encode('utf-8') + '\n\n')	
			for Abstract in Article.findall("Abstract"):
				abstract1 = Abstract.find("AbstractText").text
				if abstract1:
					output.write(abstract1.encode('utf-8'))			
		for OtherAbstract in MedlineCitation.findall("OtherAbstract"):
			abstract2 = OtherAbstract.find("AbstractText").text
			if abstract2:
				output.write(abstract2.encode('utf-8'))
		output.write('\n\n')
		output.write("</doc>" + '\n')
