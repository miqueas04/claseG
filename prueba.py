import xml.etree.ElementTree as ET
 
tree = ET.parse("data/tasks_provider_c.xml")
root = tree.getroot()
for task in root.findall("task"):
    print({
        "title": task.find("title").text,
        "priority": task.find("priority").text,
        "status": task.find("status").text,
    })
