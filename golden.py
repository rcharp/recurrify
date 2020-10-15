import os
os.system("git checkout golden")
os.system("git pull origin master --force")
os.system("git add .")
os.system('git commit -m "merge from master to golden"')
os.system("git push origin golden")
os.system("git checkout dev")