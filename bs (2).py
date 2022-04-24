import time
import getpass
from tqdm.auto import tqdm
import sqlite3
import pyzbar.pyzbar as pyzbar
import pyqrcode
import cv2
import os
import numpy
import colorama
from colorama import Back, Style
colorama.init(autoreset=True)
#------ScanningFromWebCamera---------------------
def scan():
	i = 0
	cap = cv2.VideoCapture(0)
	font = cv2.FONT_HERSHEY_PLAIN
	while i<1:
		ret,frame=cap.read()
		decode = pyzbar.decode(frame)
		for obj in decode:
			name=obj.data
			name2= name.decode()
			nn,ii,pp,dd = name2.split(' ')
			db = sqlite3.connect('EmployeeDatabase.db')
			c = db.cursor()
			c.execute('''CREATE TABLE IF NOT EXISTS Record(name TEXT, iid TEXT,phone_no TEXT, dept TEXT, TimeofMArk TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL )''')
			c.execute("INSERT INTO Record(name, iid, phone_no, dept) VALUES (?,?,?,?)", (nn,ii,pp,dd))
			db.commit()

#database portions--------------------------------
			i=i+1
		cv2.imshow("QRCode",frame)
		cv2.waitKey(2)
		cv2.destroyAllWindows

#------CreateDatabaseForeEmployee------------------
def database():
	conn = sqlite3.connect('EmployeeDatabase.db')
	c = conn.cursor()
	c.execute("CREATE TABLE IF NOT EXISTS all_record(employee_name TEXT, employee_id TEXT, employee_contact, employee_department TEXT)")
	conn.commit()
	conn.close()
database()

#------AddingNewUsers/Employee---------------------
def add_User():
	Li = []
	E_name=str(input("Please Enter Employee Name\n"))
	E_id=str(input("Please Enter Employee Id\n"))
	E_contac= input("Please enter Employee Contact No\n")
	E_dept= input("Please enter Employee Department\n")
	Li.extend((E_name,E_id,E_contac,E_dept))
#-----using List Compression to convert a list to str--------------
	listToStr = ' '.join([str(elem) for elem in Li])
	#print(listToStr)
	print(Back.YELLOW + "Please Verify the Information")
	print("Employee Name       = "+ E_name)
	print("Employee ID         = "+ E_id)
	print("Employee Contact    = "+ E_contac)
	print("Employee Department = "+ E_dept)
	input("Press Enter to continue or CTRL+C to Break Operation")
	conn = sqlite3.connect('EmployeeDatabase.db')
	c = conn.cursor()
	c.execute("INSERT INTO all_record(employee_name, employee_id, employee_contact, employee_department) VALUES (?,?,?,?)", (E_name,E_id,E_contac,E_dept))
	conn.commit()
	conn.close()
	qr= pyqrcode.create(listToStr)
	if not os.path.exists('./QrCodes'):
		os.makedirs('./QRCodes')
	qr.png("./QRCodes/" +E_name+ ".png",scale=8)
#--------------ViewDatabase------------------------
def viewdata():
	conn = sqlite3.connect('EmployeeDatabase.db')
	c = conn.cursor()
	c.execute("SELECT * FROM Record")
	rows = c.fetchall()
	for row in rows:
		print(row)
	conn.close()
#----------AdminScreen-----------------------
def afterlogin():
	print("+------------------------------+")
	print("|  1- Add New Employee         |")
	print("|  2- Veiw Record              |")
	print("+------------------------------+")
	user_input = input("")
	if user_input == '1':
		add_User()
	if user_input == '2':
		viewdata()

#Login--------------------------------------
def login():
	print(Back.CYAN+ 'Please Enter Password :')
	print(Back.YELLOW+"QR Code Attendace System")
	password = getpass.getpass()
	if password =='aka':
		for i in tqdm(range(4000)):
			print("",end='\r')
		print("------------------------------------------------------------------------------------------------------------------------")
		print(Back.BLUE+"QR Code Attendace System")
		afterlogin()
	if password != 'aka':
		print("Invalid Password")
		login()



#-------MainPage----------------------------
def markattendance():
	print("+------------------------------+")
	print("|  1- Mark Attendance          |")
	print("|  2- Admin Login              |")
	print("+------------------------------+")
	user_input2 = input("")
	if user_input2== '1':
		scan()
	if user_input2 == '2':
		login()
markattendance()
