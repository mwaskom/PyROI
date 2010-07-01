import os

os.system("python ../data/configfiles/make_clean_config.py")
os.system("python ../data/configfiles/extract_config_doc.py")
os.system("make html")
os.system("scp -r build/html/* mwaskom@ftp.dialup.mit.edu:pyroi")
