text_file = open("token.txt", "r")
 
#read whole file to a string
data = text_file.read()

#close file
text_file.close()
 
print(data)