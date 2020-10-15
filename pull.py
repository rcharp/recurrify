import os
os.system("git checkout dev")
os.system('git pull origin dev --force')
os.system("git checkout master")
os.system('git pull origin master --force')
os.system("git checkout dev")