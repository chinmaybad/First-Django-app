
import smtplib 
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders 
import os
   
fromaddr = "zomato2604@gmail.com"

recv_list = ["yogesh.kothari2601@gmail.com", "badhecm@rknec.edu"]   
# instance of MIMEMultipart 

for toaddr in recv_list:
	msg = MIMEMultipart() 
	   
	msg['From'] = fromaddr 
	msg['To'] = toaddr 
	msg['Subject'] = "Access Token"
	body = "Body_of_the_mail"
	  
	msg.attach(MIMEText(body, 'plain')) 
	filename = "LoginDetail.txt"
	attachment = open(os.getcwd() + r'/LoginDetail.txt','rb') 
	  
	# instance of MIMEBase and named as p 
	p = MIMEBase('application', 'octet-stream') 
	  
	# To change the payload into encoded form 
	p.set_payload((attachment).read()) 
	encoders.encode_base64(p) 
	   
	p.add_header('Content-Disposition', "attachment; filename= %s" % filename) 
	msg.attach(p) 
	  
	s = smtplib.SMTP('smtp.gmail.com', 587) 	  
	s.starttls() 	 
	s.login(fromaddr, "yogesh123") 
	  
	text = msg.as_string() 	  
	s.sendmail(fromaddr, toaddr, text) 
	s.quit() 
