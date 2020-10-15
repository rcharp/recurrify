import os
import time

'''
Pushes the live version of the site.
'''
os.system("git checkout dev")
os.system("git add .")
os.system('git commit -m "changes"')
os.system('git push origin dev')

time.sleep(5)

os.system("git checkout master")
os.system("git pull origin dev --force")
os.system("git add .")
os.system('git commit -m "push to master"')
os.system("git push origin master")
os.system("git checkout dev")