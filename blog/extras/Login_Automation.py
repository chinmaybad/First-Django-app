from selenium import webdriver
from kiteconnect import KiteConnect
from time import sleep
from apscheduler.schedulers.blocking import BlockingScheduler
import pandas as pd
import datetime
import os

flag = True
while flag:
	try:
		browser = webdriver.PhantomJS(executable_path= os.getcwd() + r"\phantomjs-2.1.1-windows\bin\phantomjs")
		# insert page link
		browser.get("https://kite.trade/connect/login?api_key=0ld4qxtvnif715ls&v=3")
		sleep(2)
		count = 0
		# insert credential
		username = browser.find_element_by_css_selector("input[type='text']")
		username.send_keys('ZB8746')
		password = browser.find_element_by_css_selector("input[type='password']")
		password.send_keys('@KKR357')
		browser.find_element_by_css_selector("button[type='submit']").click()

		print('Username: ZB8746')
		print('Password: @KKR357')
		sleep(5)


		q1 = browser.find_elements_by_css_selector("label")[0].text
		q2 = browser.find_elements_by_css_selector("label")[1].text

		if q1 == 'What is your height in feet? (e.g. 5.4 4.8 etc)':
			a1 = "5'11"
		elif q1 == 'What was your major during college? (e.g. Finance, IT, etc)':
			a1 = 'finance'
		elif q1 == "With which company did you start your career? (e.g. TATA, Infosys, Etc.)":
			a1 = 'geojit bnp paribas'
		elif q1 == "What is your vehicle registration number? (e.g. 478, 786, etc)":
			a1 = '0006'
		elif q1 == "What's the most famous landmark near your home? (e.g. Xyz Theater, XXX Mall, etc)":
			a1 == 'tirpude college'

		if q2 == 'What is your height in feet? (e.g. 5.4 4.8 etc)':
			a2 = "5'11"
		elif q2 == 'What was your major during college? (e.g. Finance, IT, etc)':
			a2 = 'finance'
		elif q2 == "With which company did you start your career? (e.g. TATA, Infosys, Etc.)":
			a2 = 'geojit bnp paribas'
		elif q2 == "What is your vehicle registration number? (e.g. 478, 786, etc)":
			a2 = '0006'
		elif q2 == "What's the most famous landmark near your home? (e.g. Xyz Theater, XXX Mall, etc)":
			a2 = 'tirpude college'

		sleep(1)   

		print(q1)
		print(a1)
		print(q2)
		print(a2)

		#answering the question    
		question1 = browser.find_elements_by_css_selector("input")[0]
		question1.send_keys(a1)
		question2 = browser.find_elements_by_css_selector("input")[1]
		question2.send_keys(a2)
		browser.find_element_by_css_selector("button[type='submit']").click()
		sleep(5)

		s = browser.current_url
		for i in range(10):
			try:
				request_token = (s.split('request_token='))[1].split('&action')[0]
				break;
			except:
				count += 1
				print('try: ', count)
				sleep(2)
				pass

		kite = KiteConnect(api_key="0ld4qxtvnif715ls")
		api_key="0ld4qxtvnif715ls"
		api_secret="1lg2kjkba3ol83aospgrovvqd5uvetyn"
		kite=KiteConnect(api_key,api_secret)
		dic = kite.generate_session(request_token, api_secret)
		del(dic['login_time'])

		try:
			df = pd.read_csv(os.getcwd() + "/task1.csv", index_col=False)
			df['access_token'] = dic['access_token']
			print("access token = " + str(dic['access_token']))
			df.to_csv(os.getcwd() + "/task1.csv", index=False)
		except:
			print("exception CSV")
			pass
		try:
			file = open(os.getcwd() + r'/LoginDetail.txt','w') 
			file.write(str(dic))
			file.close()        
		except:
			print("exception txt")
			pass
		print(dic)
		flag = False
	except: 
		pass